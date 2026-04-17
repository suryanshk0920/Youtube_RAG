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

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false)
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768)
    check()
    window.addEventListener("resize", check)
    return () => window.removeEventListener("resize", check)
  }, [])
  return isMobile
}

export default function Home() {
  const [activeKb, setActiveKb] = useState("default")
  const [activeSourceId, setActiveSourceId] = useState<string | null>(null)
  const [sources, setSources] = useState<Source[]>([])
  const [allSources, setAllSources] = useState<Source[]>([])
  const [pendingIntro, setPendingIntro] = useState<IntroData | null>(null)
  const [chunkCounts, setChunkCounts] = useState<Record<string, number>>({})
  const [sessions, setSessions] = useState<Record<string, ChatSession>>({})
  // Mobile tab: "chat" | "add" | "library"
  const [mobileTab, setMobileTab] = useState<"chat" | "add" | "library">("chat")
  const isMobile = useIsMobile()

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

  function handleMessagesChange(sourceId: string, messages: Message[]) {
    const existing = sessions[sourceId]
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
    const source = allSources.find(s => s.id === intro.source_id)
    const title = source?.title ?? intro.source_id
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
    setMobileTab("chat") // switch to chat on mobile after ingestion
  }

  function handleSelectSession(sourceId: string) {
    setActiveSourceId(sourceId)
    setPendingIntro(null)  // always clear intro when switching sessions
    const session = sessions[sourceId]
    if (session && session.kbId !== activeKb) setActiveKb(session.kbId)
    setMobileTab("chat")
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
    setMobileTab("chat")
  }

  const activeSession = activeSourceId ? sessions[activeSourceId] : null
  const activeMessages = activeSession?.messages ?? []
  const activeKbForChat = activeSession?.kbId ?? activeKb

  const sidebarProps = {
    activeKb, activeSourceId, chunkCounts, sessions,
    onKbChange: handleKbChange,
    onSelectSession: handleSelectSession,
    onDeleteSession: handleDeleteSession,
  }

  const chatProps = {
    activeKb: activeKbForChat,
    activeSourceId,   // pass so chat scopes to this video's chunks
    pendingIntro,
    onIntroDismiss: () => setPendingIntro(null),
    messages: activeMessages,
    onMessagesChange: (msgs: Message[]) => activeSourceId && handleMessagesChange(activeSourceId, msgs),
  }

  const ingestProps = {
    sources, activeKb,
    onSourcesChange: loadSources,
    onIntroReady: handleIntroReady,
  }

  return (
    <>
      {/* ── Desktop layout ─────────────────────────────────────── */}
      {!isMobile && (
        <div style={{ display: "flex", height: "100dvh", background: "var(--bg-base)", overflow: "hidden" }}>
          <div style={{ width: "240px", flexShrink: 0, borderRight: "1px solid var(--border)", background: "var(--bg-surface)" }}>
            <Sidebar {...sidebarProps} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <ChatPanel {...chatProps} />
          </div>
          <div style={{ width: "340px", flexShrink: 0, borderLeft: "1px solid var(--border)", background: "var(--bg-surface)" }}>
            <IngestionPanel {...ingestProps} />
          </div>
        </div>
      )}

      {/* ── Mobile layout ──────────────────────────────────────── */}
      {isMobile && (
        <div style={{ display: "flex", flexDirection: "column", height: "100dvh", background: "var(--bg-base)" }}>

          {/* Top bar */}
          <div style={{
            display: "flex", alignItems: "center", gap: "0",
            padding: "10px 16px", borderBottom: "1px solid var(--border)",
            background: "var(--bg-surface)", flexShrink: 0,
          }}>
            {/* Hamburger */}
            <button
              onClick={() => setMobileTab(mobileTab === "library" ? "chat" : "library")}
              style={{
                width: "40px", height: "40px", borderRadius: "10px",
                border: "1px solid var(--border-warm)",
                background: mobileTab === "library" ? "var(--amber-dim)" : "rgba(245,158,11,0.06)",
                color: "var(--amber)",
                cursor: "pointer", display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center", gap: "5px",
                transition: "all 0.15s", flexShrink: 0,
              }}
            >
              <span style={{ display: "block", width: "16px", height: "2px", background: "currentColor", borderRadius: "1px" }} />
              <span style={{ display: "block", width: "16px", height: "2px", background: "currentColor", borderRadius: "1px" }} />
              <span style={{ display: "block", width: "16px", height: "2px", background: "currentColor", borderRadius: "1px" }} />
            </button>

            {/* Separator */}
            <div style={{ width: "1px", height: "24px", background: "var(--border)", margin: "0 14px", flexShrink: 0 }} />

            {/* Active session title or wordmark */}
            <div style={{ flex: 1, minWidth: 0 }}>
              {activeSession ? (
                <>
                  <p style={{
                    fontFamily: "var(--font-syne), sans-serif", fontWeight: 600,
                    fontSize: "0.9rem", color: "var(--text-primary)", margin: 0,
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                  }}>
                    {activeSession.sourceTitle}
                  </p>
                  <p style={{
                    fontSize: "0.65rem", color: "var(--text-muted)", margin: 0,
                    fontFamily: "var(--font-dm-mono), monospace",
                  }}>
                    {activeSession.kbId} · {Math.floor(activeSession.messages.length / 2)} messages
                  </p>
                </>
              ) : (
                <p style={{ fontFamily: "var(--font-syne), sans-serif", fontWeight: 800, fontSize: "1.1rem", letterSpacing: "-0.03em", color: "var(--text-primary)", margin: 0 }}>
                  Tube<span style={{ color: "var(--amber)" }}>Query</span>
                </p>
              )}
            </div>
          </div>

          {/* Drawer overlay */}
          {mobileTab === "library" && (
            <div
              onClick={() => setMobileTab("chat")}
              style={{
                position: "fixed", inset: 0, zIndex: 40,
                background: "rgba(0,0,0,0.5)",
                backdropFilter: "blur(2px)",
              }}
            />
          )}

          {/* Slide-in drawer */}
          <div style={{
            position: "fixed", top: 0, left: 0, bottom: 0, zIndex: 50,
            width: "280px",
            background: "var(--bg-surface)",
            borderRight: "1px solid var(--border)",
            transform: mobileTab === "library" ? "translateX(0)" : "translateX(-100%)",
            transition: "transform 0.3s cubic-bezier(0.16,1,0.3,1)",
            overflowY: "auto",
          }}>
            <Sidebar {...sidebarProps} />
          </div>

          {/* Content area */}
          <div style={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
            {mobileTab !== "add"
              ? <ChatPanel {...chatProps} />
              : (
                <div style={{ height: "100%", overflowY: "auto", background: "var(--bg-surface)" }}>
                  <IngestionPanel {...ingestProps} />
                </div>
              )
            }
          </div>

          {/* Bottom tab bar — Chat + Add only */}
          <div style={{
            display: "flex",
            borderTop: "1px solid var(--border)",
            background: "var(--bg-surface)",
            paddingBottom: "env(safe-area-inset-bottom, 0px)",
            flexShrink: 0,
          }}>
            {([
              { id: "chat", icon: "💬", label: "Chat" },
              { id: "add",  icon: "＋", label: "Add" },
            ] as const).map(tab => (
              <button
                key={tab.id}
                onClick={() => setMobileTab(tab.id)}
                style={{
                  flex: 1, display: "flex", flexDirection: "column",
                  alignItems: "center", justifyContent: "center",
                  gap: "3px", padding: "12px 0",
                  border: "none", background: "transparent", cursor: "pointer",
                  color: mobileTab === tab.id ? "var(--amber)" : "var(--text-muted)",
                  transition: "color 0.15s",
                }}
              >
                <span style={{ fontSize: "1.2rem", lineHeight: 1 }}>{tab.icon}</span>
                <span style={{ fontSize: "0.65rem", fontFamily: "var(--font-dm-mono), monospace", letterSpacing: "0.05em" }}>
                  {tab.label}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
