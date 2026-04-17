import type { Citation, IngestResponse, IntroData, Message, Source } from "@/types"

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// ── Sources ──────────────────────────────────────────────────────────

export async function getSources(kb_id?: string): Promise<Source[]> {
  const url = kb_id ? `${BASE}/sources?kb_id=${kb_id}` : `${BASE}/sources`
  const res = await fetch(url)
  if (!res.ok) throw new Error("Failed to fetch sources")
  return res.json()
}

export async function deleteSource(source_id: string, kb_id: string): Promise<void> {
  const res = await fetch(`${BASE}/sources/${source_id}?kb_id=${kb_id}`, { method: "DELETE" })
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
    headers: { "Content-Type": "application/json" },
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
  const res = await fetch(`${BASE}/ingest/${source_id}/intro`)
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
  onError: (error: string) => void
}

export async function streamChat(
  question: string,
  kb_id: string,
  history: Message[],
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  try {
    const res = await fetch(`${BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        kb_id,
        history: history.map((m) => ({ role: m.role, content: m.content })),
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
      const lines = buffer.split("\n")
      buffer = lines.pop() ?? ""

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue
        const data = line.slice(6).trim()
        if (!data || data === "[DONE]") continue

        try {
          const event = JSON.parse(data)
          if (event.type === "token") callbacks.onToken(event.content)
          else if (event.type === "citation") callbacks.onCitation(event.content)
          else if (event.type === "done") callbacks.onDone()
          else if (event.type === "error") callbacks.onError(event.content)
        } catch {
          // malformed chunk — skip
        }
      }
    }
  } catch (err: unknown) {
    // AbortError is expected when user stops the stream — not a real error
    if (err instanceof Error && err.name === "AbortError") return
    callbacks.onError(err instanceof Error ? err.message : "Stream failed")
  }
}
