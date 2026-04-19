"use client"
import { useCallback, useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { ChatPanel } from "@/components/ChatPanel"
import { IngestionPanel } from "@/components/IngestionPanel"
import { Sidebar } from "@/components/Sidebar"
import { getSources, fetchSessions, createDBSession, updateDBSession, deleteDBSession } from "@/lib/api"
import { useAuth } from "@/context/AuthContext"
import { useAppState } from "@/context/AppStateContext"
import type { ChatSession, IntroData, Message, Source } from "@/types"

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
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const { state, updateSessions, updateSources, updateActiveKb, updateActiveSourceId, updateChunkCounts, updateLastFetched } = useAppState()
  
  const [allSources, setAllSources] = useState<Source[]>(state.sources)
  const [pendingIntro, setPendingIntro] = useState<IntroData | null>(null)
  const [mobileTab, setMobileTab] = useState<"chat" | "add" | "library">("chat")
  const [generatingSummary, setGeneratingSummary] = useState(false)
  const [initialLoadDone, setInitialLoadDone] = useState(false)
  const isMobile = useIsMobile()
  
  // Use ref to track if sources are currently being loaded
  const loadingSourcesRef = useRef(false)

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) router.push("/login")
  }, [user, authLoading, router])

  // Load sessions from Supabase only once on mount if not already loaded
  useEffect(() => {
    if (!user || initialLoadDone) return
    
    const hasExistingSessions = Object.keys(state.sessions).length > 0
    
    if (!hasExistingSessions) {
      fetchSessions().then(dbSessions => {
        const map: Record<string, ChatSession> = {}
        for (const s of dbSessions) {
          const key = s.source_id
          map[key] = {
            sourceId: s.source_id,
            sourceTitle: s.source_title,
            kbId: s.kb_name,
            messages: (s.messages as Message[]) ?? [],
            createdAt: s.created_at,
            dbId: s.id,
          }
        }
        updateSessions(map)
        setInitialLoadDone(true)
      })
    } else {
      setInitialLoadDone(true)
    }
  }, [user, state.sessions, updateSessions, initialLoadDone])

  const loadSources = useCallback(async (force = false) => {
    // Prevent concurrent loads
    if (loadingSourcesRef.current) return
    
    // Use cached data if available and recent (within 30 seconds)
    const now = Date.now()
    const lastFetch = state.lastFetched
    const cachedSources = state.sources
    
    if (!force && now - lastFetch < 30_000 && cachedSources.length > 0) {
      setAllSources(cachedSources)
      return
    }
    
    loadingSourcesRef.current = true
    
    try {
      const all = await getSources()
      setAllSources(all)
      updateSources(all)
      
      const counts: Record<string, number> = {}
      for (const s of all) {
        const key = s.kb_name ?? s.kb_id
        counts[key] = (counts[key] ?? 0) + s.chunk_count
      }
      updateChunkCounts(counts)
      updateLastFetched(now)
    } catch { /* API not ready */ } finally {
      loadingSourcesRef.current = false
    }
  }, [updateSources, updateChunkCounts, updateLastFetched]) // Remove state dependencies

  useEffect(() => { 
    if (!user || !initialLoadDone) return // Wait for initial load
    
    // Only load once on mount
    if (state.sources.length === 0 || Date.now() - state.lastFetched > 30_000) {
      loadSources(false)
    } else {
      setAllSources(state.sources)
    }
  }, [user, initialLoadDone]) // Remove loadSources dependency - only run once

  function handleMessagesChange(sourceId: string, messages: Message[]) {
    const existing = state.sessions[sourceId]
    const session = existing ?? {
      sourceId,
      sourceTitle: allSources.find(s => s.id === sourceId)?.title ?? sourceId,
      kbId: state.activeKb,
      messages: [],
      createdAt: new Date().toISOString(),
    }
    const updatedSessions = { ...state.sessions, [sourceId]: { ...session, messages } }
    updateSessions(updatedSessions)
    
    // Only save to Supabase when streaming is complete
    const isStillStreaming = messages.some(m => m.isStreaming)
    if (!isStillStreaming && existing?.dbId) {
      updateDBSession(existing.dbId, messages).catch(e => console.warn("Session save failed:", e))
    }
  }

  async function handleIntroReady(intro: IntroData) {
    setGeneratingSummary(false)
    await loadSources(true) // Force refresh after ingestion
    const source = allSources.find(s => s.id === intro.source_id)
    const title = intro.source_title || source?.title || intro.source_id

    const existingSession = state.sessions[intro.source_id]
    
    if (existingSession) {
      const summaryMessage: Message = {
        id: crypto.randomUUID(),
        role: "summary",
        content: intro.intro,
        summaryData: intro,
      }
      const updatedMessages = [...existingSession.messages, summaryMessage]
      handleMessagesChange(intro.source_id, updatedMessages)
      updateActiveSourceId(intro.source_id)
      setMobileTab("chat")
      return
    }

    setPendingIntro(intro)
    setMobileTab("chat")

    try {
      const dbSession = await createDBSession(intro.source_id, title, state.activeKb)
      const updatedSessions = {
        ...state.sessions,
        [intro.source_id]: {
          sourceId: intro.source_id,
          sourceTitle: title,
          kbId: state.activeKb,
          messages: [],
          createdAt: dbSession.created_at,
          dbId: dbSession.id,
        }
      }
      updateSessions(updatedSessions)
    } catch (e) {
      console.warn("Session creation failed, using local:", e)
      const updatedSessions = {
        ...state.sessions,
        [intro.source_id]: {
          sourceId: intro.source_id,
          sourceTitle: title,
          kbId: state.activeKb,
          messages: [],
          createdAt: new Date().toISOString(),
        }
      }
      updateSessions(updatedSessions)
    }
    updateActiveSourceId(intro.source_id)
  }

  function handleSelectSession(sourceId: string) {
    updateActiveSourceId(sourceId)
    setPendingIntro(null)
    const session = state.sessions[sourceId]
    if (session && session.kbId !== state.activeKb) updateActiveKb(session.kbId)
    setMobileTab("chat")
  }

  function handleDeleteSession(sourceId: string) {
    const session = state.sessions[sourceId]
    if (session?.dbId) {
      deleteDBSession(session.dbId).catch(e => console.warn("Session delete failed:", e))
    }
    const updated = { ...state.sessions }
    delete updated[sourceId]
    updateSessions(updated)
    if (state.activeSourceId === sourceId) {
      updateActiveSourceId(null)
      setPendingIntro(null)
    }
  }

  function handleKbChange(kb: string) {
    updateActiveKb(kb)
    updateActiveSourceId(null)
    setPendingIntro(null)
    setMobileTab("chat")
  }

  const activeSession = state.activeSourceId ? state.sessions[state.activeSourceId] : null
  const activeMessages = activeSession?.messages ?? []
  const activeKbForChat = activeSession?.kbId ?? state.activeKb
  const filteredSources = allSources.filter(s => (s.kb_name ?? s.kb_id) === state.activeKb)

  const sidebarProps = {
    activeKb: state.activeKb,
    activeSourceId: state.activeSourceId,
    chunkCounts: state.chunkCounts,
    sessions: state.sessions,
    onKbChange: handleKbChange,
    onSelectSession: handleSelectSession,
    onDeleteSession: handleDeleteSession,
  }

  const chatProps = {
    activeKb: activeKbForChat,
    activeSourceId: state.activeSourceId,
    pendingIntro,
    generatingSummary,
    onIntroDismiss: () => setPendingIntro(null),
    messages: activeMessages,
    onMessagesChange: (msgs: Message[]) => state.activeSourceId && handleMessagesChange(state.activeSourceId, msgs),
  }

  const ingestProps = {
    sources: filteredSources,
    activeKb: state.activeKb,
    onSourcesChange: () => loadSources(true),
    onIntroReady: handleIntroReady,
    onSummarising: () => { setGeneratingSummary(true); setMobileTab("chat") },
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
