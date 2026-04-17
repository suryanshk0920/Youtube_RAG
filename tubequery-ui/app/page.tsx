"use client"
import { useCallback, useEffect, useState } from "react"
import { ChatPanel } from "@/components/ChatPanel"
import { IngestionPanel } from "@/components/IngestionPanel"
import { Sidebar } from "@/components/Sidebar"
import { getSources } from "@/lib/api"
import type { ChatSession, IntroData, Message, Source } from "@/types"

const STORAGE_KEY = "tubequery_sessions_v2"

function loadSessions(): Record<string, ChatSession> {
  if (typeof window === "undefined") return {}
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch { return {} }
}

function saveSessions(s: Record<string, ChatSession>) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)) } catch { /* quota */ }
}

export default function Home() {
  const [activeKb, setActiveKb] = useState("default")
  const [activeSourceId, setActiveSourceId] = useState<string | null>(null)
  const [sources, setSources] = useState<Source[]>([])
  const [allSources, setAllSources] = useState<Source[]>([])
  const [pendingIntro, setPendingIntro] = useState<IntroData | null>(null)
  const [chunkCounts, setChunkCounts] = useState<Record<string, number>>({})
  const [sessions, setSessions] = useState<Record<string, ChatSession>>({})

  useEffect(() => { setSessions(loadSessions()) }, [])

  const loadSources = useCallback(async () => {
    try {
      const all = await getSources()
      setAllSources(all)
      setSources(all.filter(s => s.kb_id === activeKb))
      const counts: Record<string, number> = {}
      for (const s of all) counts[s.kb_id] = (counts[s.kb_id] ?? 0) + s.chunk_count
      setChunkCounts(counts)
    } catch { /* API not ready */ }
  }, [activeKb])

  useEffect(() => { loadSources() }, [loadSources])

  function getOrCreateSession(sourceId: string, sourceTitle: string, kbId: string): ChatSession {
    if (sessions[sourceId]) return sessions[sourceId]
    return { sourceId, sourceTitle, kbId, messages: [], createdAt: new Date().toISOString() }
  }

  function handleMessagesChange(sourceId: string, messages: Message[]) {
    const existing = sessions[sourceId]
    // Auto-create session if it doesn't exist yet (user chatted without selecting a session)
    const session = existing ?? {
      sourceId,
      sourceTitle: allSources.find(s => s.id === sourceId)?.title ?? sourceId,
      kbId: activeKb,
      messages: [],
      createdAt: new Date().toISOString(),
    }
    const updated = { ...sessions, [sourceId]: { ...session, messages } }
    setSessions(updated)
    saveSessions(updated)
  }

  function handleIntroReady(intro: IntroData) {
    // Find the source title
    const source = allSources.find(s => s.id === intro.source_id)
    const title = source?.title ?? intro.source_id

    // Create session if not exists, clear messages for fresh start
    const session: ChatSession = {
      sourceId: intro.source_id,
      sourceTitle: title,
      kbId: activeKb,
      messages: [],
      createdAt: new Date().toISOString(),
    }
    const updated = { ...sessions, [intro.source_id]: session }
    setSessions(updated)
    saveSessions(updated)

    setActiveSourceId(intro.source_id)
    setPendingIntro(intro)
  }

  function handleSelectSession(sourceId: string) {
    setActiveSourceId(sourceId)
    setPendingIntro(null)
    // Switch KB if needed
    const session = sessions[sourceId]
    if (session && session.kbId !== activeKb) setActiveKb(session.kbId)
  }

  function handleDeleteSession(sourceId: string) {
    const updated = { ...sessions }
    delete updated[sourceId]
    setSessions(updated)
    saveSessions(updated)
    if (activeSourceId === sourceId) {
      setActiveSourceId(null)
      setPendingIntro(null)
    }
  }

  function handleKbChange(kb: string) {
    setActiveKb(kb)
    setActiveSourceId(null)
    setPendingIntro(null)
  }

  const activeSession = activeSourceId ? sessions[activeSourceId] : null
  const activeMessages = activeSession?.messages ?? []
  const activeKbForChat = activeSession?.kbId ?? activeKb

  return (
    <div style={{ display: "flex", height: "100dvh", background: "var(--bg-base)", overflow: "hidden" }}>
      {/* Sidebar — hidden on mobile */}
      <div className="sidebar-panel" style={{ width: "240px", flexShrink: 0, borderRight: "1px solid var(--border)", background: "var(--bg-surface)" }}>
        <Sidebar
          activeKb={activeKb}
          activeSourceId={activeSourceId}
          chunkCounts={chunkCounts}
          sessions={sessions}
          onKbChange={handleKbChange}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
        />
      </div>

      {/* Chat */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <ChatPanel
          activeKb={activeKbForChat}
          pendingIntro={pendingIntro}
          onIntroDismiss={() => setPendingIntro(null)}
          messages={activeMessages}
          onMessagesChange={(msgs) => activeSourceId && handleMessagesChange(activeSourceId, msgs)}
        />
      </div>

      {/* Right panel — collapsible on mobile */}
      <div className="ingest-panel" style={{ width: "340px", flexShrink: 0, borderLeft: "1px solid var(--border)", background: "var(--bg-surface)" }}>
        <IngestionPanel
          sources={sources}
          activeKb={activeKb}
          onSourcesChange={loadSources}
          onIntroReady={handleIntroReady}
        />
      </div>
    </div>
  )
}
