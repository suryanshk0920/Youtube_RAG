import type { Citation, IngestResponse, IntroData, Message, Source } from "@/types"
import { auth } from "@/lib/firebase"

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function authHeaders(): Promise<Record<string, string>> {
  const user = auth.currentUser
  if (!user) return { "Content-Type": "application/json" }
  const token = await user.getIdToken()
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`,
  }
}

// ── Sources ──────────────────────────────────────────────────────────

export async function getSources(kb_id?: string): Promise<Source[]> {
  const url = kb_id ? `${BASE}/sources?kb_id=${kb_id}` : `${BASE}/sources`
  const res = await fetch(url, { headers: await authHeaders() })
  if (!res.ok) throw new Error("Failed to fetch sources")
  return res.json()
}

export async function deleteSource(source_id: string, kb_id: string): Promise<void> {
  const res = await fetch(`${BASE}/sources/${source_id}?kb_id=${kb_id}`, {
    method: "DELETE",
    headers: await authHeaders(),
  })
  if (!res.ok) throw new Error("Failed to delete source")
}

// ── Ingest ───────────────────────────────────────────────────────────

export async function ingestUrl(url: string, kb_id: string): Promise<IngestResponse> {
  const res = await fetch(`${BASE}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, kb_id }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || "Ingestion failed")
  }
  return res.json()
}

export interface IngestStreamCallbacks {
  onStep: (step: string, detail: string) => void
  onProgress: (current: number, total: number, video: string) => void
  onDone: (result: IngestResponse) => void
  onError: (error: string) => void
}

export async function streamIngest(
  url: string,
  kb_id: string,
  callbacks: IngestStreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${BASE}/ingest/stream`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({ url, kb_id }),
    signal,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Ingestion failed" }))
    callbacks.onError(err.detail || "Ingestion failed")
    return
  }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n")
    buffer = lines.pop() ?? ""
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue
      const data = line.slice(6).trim()
      if (!data) continue
      try {
        const event = JSON.parse(data)
        if (event.type === "step") callbacks.onStep(event.step, event.detail)
        else if (event.type === "progress") callbacks.onProgress(event.current, event.total, event.video)
        else if (event.type === "done") callbacks.onDone(event.source)
        else if (event.type === "error") callbacks.onError(event.detail)
      } catch { /* skip */ }
    }
  }
}

export async function getIntro(source_id: string): Promise<IntroData> {
  const res = await fetch(`${BASE}/ingest/${source_id}/intro`, { headers: await authHeaders() })
  if (!res.ok) throw new Error("Failed to generate intro")
  return res.json()
}

// ── YouTube thumbnail ────────────────────────────────────────────────

export function getYoutubeThumbnail(url: string): string | null {
  const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/)
  if (!match) return null
  return `https://img.youtube.com/vi/${match[1]}/mqdefault.jpg`
}

// ── Chat streaming ───────────────────────────────────────────────────

export interface StreamCallbacks {
  onToken: (token: string) => void
  onCitation: (citation: Citation) => void
  onDone: () => void
  onError: (error: string, upgradeRequired?: boolean, limitDetails?: any) => void
}

export async function streamChat(
  question: string,
  kb_id: string,
  history: Message[],
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
  source_ids?: string[]
): Promise<void> {
  try {
    const res = await fetch(`${BASE}/chat/stream`, {
      method: "POST",
      headers: await authHeaders(),
      body: JSON.stringify({
        question,
        kb_id,
        history: history.map((m) => ({ role: m.role, content: m.content })),
        source_ids: source_ids ?? null,
      }),
      signal,
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Stream failed" }))
      callbacks.onError(err.detail || "Stream failed")
      return
    }

    const reader = res.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ""

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // SSE events are separated by double newlines
      const events = buffer.split("\n\n")
      buffer = events.pop() ?? ""  // keep incomplete last event

      for (const event of events) {
        for (const line of event.split("\n")) {
          if (!line.startsWith("data: ")) continue
          const data = line.slice(6).trim()
          if (!data || data === "[DONE]") continue

          try {
            const parsed = JSON.parse(data)
            if (parsed.type === "token") callbacks.onToken(parsed.content)
            else if (parsed.type === "citation") callbacks.onCitation(parsed.content)
            else if (parsed.type === "done") callbacks.onDone()
            else if (parsed.type === "error") {
              callbacks.onError(
                parsed.content, 
                parsed.upgrade_required, 
                parsed.limit_details
              )
            }
          } catch (e) {
            console.warn("SSE parse error:", data.slice(0, 50), e)
          }
        }
      }
    }
  } catch (err: unknown) {
    // AbortError is expected when user stops the stream — not a real error
    if (err instanceof Error && err.name === "AbortError") return
    callbacks.onError(err instanceof Error ? err.message : "Stream failed", false, null)
  }
}

// ── Sessions (Supabase-backed) ───────────────────────────────────────

export interface DBSession {
  id: string
  source_id: string
  source_title: string
  kb_name: string
  messages: Message[]
  created_at: string
  updated_at: string
}

export async function fetchSessions(): Promise<DBSession[]> {
  try {
    const res = await fetch(`${BASE}/sessions`, { headers: await authHeaders() })
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

export async function createDBSession(source_id: string, source_title: string, kb_name: string): Promise<DBSession> {
  const res = await fetch(`${BASE}/sessions`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({ source_id, source_title, kb_name }),
  })
  if (!res.ok) throw new Error("Failed to create session")
  return res.json()
}

export async function updateDBSession(session_id: string, messages: Message[]): Promise<void> {
  await fetch(`${BASE}/sessions/${session_id}`, {
    method: "PATCH",
    headers: await authHeaders(),
    body: JSON.stringify({ messages }),
  })
}

export async function deleteDBSession(session_id: string): Promise<void> {
  await fetch(`${BASE}/sessions/${session_id}`, {
    method: "DELETE",
    headers: await authHeaders(),
  })
}

// ── Profile ──────────────────────────────────────────────────────────

export interface UserProfile {
  uid: string
  email: string
  display_name: string
  photo_url: string
  plan: "free" | "pro" | "team"
  created_at: string
  usage: {
    ingest: { used: number; limit: number }
    chat:   { used: number; limit: number }
  }
}

export async function fetchProfile(): Promise<UserProfile | null> {
  try {
    const res = await fetch(`${BASE}/profile`, { headers: await authHeaders() })
    if (!res.ok) return null
    return res.json()
  } catch { return null }
}

// ── Knowledge Bases ──────────────────────────────────────────────────

export interface KB {
  id: string
  name: string
  created_at: string
}

export async function fetchKBs(): Promise<KB[]> {
  try {
    const res = await fetch(`${BASE}/kbs`, { headers: await authHeaders() })
    if (!res.ok) return []
    return res.json()
  } catch { return [] }
}

export async function createKB(name: string): Promise<KB | null> {
  try {
    const res = await fetch(`${BASE}/kbs`, {
      method: "POST",
      headers: await authHeaders(),
      body: JSON.stringify({ name }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || "Failed to create library")
    }
    return res.json()
  } catch (e) {
    throw e
  }
}

export async function deleteKB(id: string): Promise<void> {
  await fetch(`${BASE}/kbs/${id}`, { method: "DELETE", headers: await authHeaders() })
}

// ── Subscription ─────────────────────────────────────────────────────

export interface UsageLimits {
  allowed: boolean
  used: number
  limit: number
  plan: string
  resets_at: string
  upgrade_message?: {
    title: string
    message: string
    cta: string
    benefits: string[]
  }
}

export interface UserLimitsSummary {
  plan: {
    type: string
    status: string
    features: {
      advanced_summaries: boolean
      priority_processing: boolean
      export_enabled: boolean
      history_retention_days: number
    }
  }
  usage: {
    videos_today: number
    videos_limit: number
    questions_today: number
    questions_limit: number
    total_videos: number
    max_concurrent_videos: number
  }
  resets_at: string
  upgrade_required: boolean
}

export async function getLimits(): Promise<UserLimitsSummary> {
  const res = await fetch(`${BASE}/subscription/limits`, { headers: await authHeaders() })
  if (!res.ok) throw new Error('Failed to get limits')
  return res.json()
}

export async function checkVideoLimit(): Promise<UsageLimits> {
  const res = await fetch(`${BASE}/subscription/check/video`, { headers: await authHeaders() })
  if (!res.ok) throw new Error('Failed to check video limit')
  return res.json()
}

export async function checkQuestionLimit(): Promise<UsageLimits> {
  const res = await fetch(`${BASE}/subscription/check/question`, { headers: await authHeaders() })
  if (!res.ok) throw new Error('Failed to check question limit')
  return res.json()
}

export async function initiateUpgrade(planType: string, billingCycle: string = 'monthly') {
  const res = await fetch(`${BASE}/subscription/upgrade`, {
    method: 'POST',
    headers: await authHeaders(),
    body: JSON.stringify({ plan_type: planType, billing_cycle: billingCycle }),
  })
  if (!res.ok) throw new Error('Failed to initiate upgrade')
  return res.json()
}
