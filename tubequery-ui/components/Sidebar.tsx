"use client"
import { useEffect, useState } from "react"
import { useAuth } from "@/context/AuthContext"
import { createKB, deleteKB, fetchKBs, type KB } from "@/lib/api"
import type { ChatSession } from "@/types"

interface Props {
  activeKb: string
  activeSourceId: string | null
  chunkCounts: Record<string, number>
  sessions: Record<string, ChatSession>
  onKbChange: (kb: string) => void
  onSelectSession: (sourceId: string) => void
  onDeleteSession: (sourceId: string) => void
}

const KB_ICONS = ["◈", "◉", "◎", "◍", "◆", "◇", "○", "●"]

export function Sidebar({ activeKb, activeSourceId, chunkCounts, sessions, onKbChange, onSelectSession, onDeleteSession }: Props) {
  const [hoveredSession, setHoveredSession] = useState<string | null>(null)
  const [kbs, setKbs] = useState<KB[]>([])
  const [showNewKb, setShowNewKb] = useState(false)
  const [newKbName, setNewKbName] = useState("")
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState("")
  const { user } = useAuth()

  useEffect(() => {
    if (!user) return
    fetchKBs().then(setKbs)
  }, [user])

  async function handleCreateKb() {
    if (!newKbName.trim()) return
    setCreating(true)
    setCreateError("")
    try {
      const kb = await createKB(newKbName.trim())
      if (kb) {
        setKbs(prev => [...prev, kb])
        onKbChange(kb.name)
        setNewKbName("")
        setShowNewKb(false)
      }
    } catch (e: unknown) {
      setCreateError(e instanceof Error ? e.message : "Failed to create library")
    } finally {
      setCreating(false)
    }
  }

  const sessionList = Object.values(sessions).sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  )

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", padding: "24px 12px" }}>
      {/* Wordmark */}
      <div style={{ padding: "0 12px", marginBottom: "28px" }}>
        <p style={{ fontFamily: "var(--font-syne), sans-serif", fontWeight: 800, fontSize: "1.25rem", letterSpacing: "-0.03em", color: "var(--text-primary)", margin: 0 }}>
          Tube<span style={{ color: "var(--amber)" }}>Query</span>
        </p>
        <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "2px", fontFamily: "var(--font-dm-mono), monospace" }}>
          v1.0 · rag assistant
        </p>
      </div>

      {/* Libraries section */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 12px", marginBottom: "6px" }}>
        <p style={{ fontSize: "0.68rem", fontWeight: 600, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase", margin: 0 }}>
          Libraries
        </p>
        <button
          onClick={() => { setShowNewKb(!showNewKb); setCreateError("") }}
          title="New library"
          style={{
            width: "20px", height: "20px", borderRadius: "5px",
            border: "1px solid var(--border)", background: showNewKb ? "var(--amber-dim)" : "transparent",
            color: showNewKb ? "var(--amber)" : "var(--text-muted)",
            cursor: "pointer", fontSize: "0.9rem", display: "flex", alignItems: "center", justifyContent: "center",
            transition: "all 0.15s",
          }}
        >
          +
        </button>
      </div>

      {/* New KB input */}
      {showNewKb && (
        <div className="animate-fade-in" style={{ padding: "0 4px", marginBottom: "8px" }}>
          <div style={{ display: "flex", gap: "4px" }}>
            <input
              autoFocus
              value={newKbName}
              onChange={e => setNewKbName(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter") handleCreateKb(); if (e.key === "Escape") setShowNewKb(false) }}
              placeholder="library name…"
              style={{
                flex: 1, padding: "6px 8px", borderRadius: "7px",
                border: "1px solid var(--border-warm)", background: "var(--bg-elevated)",
                color: "var(--text-primary)", fontSize: "0.78rem", outline: "none",
                fontFamily: "var(--font-dm-sans), sans-serif",
              }}
            />
            <button
              onClick={handleCreateKb}
              disabled={creating || !newKbName.trim()}
              style={{
                padding: "6px 10px", borderRadius: "7px",
                border: "1px solid var(--border-warm)", background: "var(--amber-dim)",
                color: "var(--amber)", fontSize: "0.75rem", cursor: creating ? "not-allowed" : "pointer",
                opacity: !newKbName.trim() ? 0.4 : 1,
              }}
            >
              {creating ? "…" : "✓"}
            </button>
          </div>
          {createError && (
            <p style={{ fontSize: "0.7rem", color: "#fca5a5", margin: "4px 4px 0", fontFamily: "var(--font-dm-mono), monospace" }}>
              {createError}
            </p>
          )}
        </div>
      )}

      {/* KB list */}
      <div style={{ display: "flex", flexDirection: "column", gap: "2px", marginBottom: "20px" }}>
        {kbs.map((kb, i) => {
          const active = activeKb === kb.name
          const count = chunkCounts[kb.name] ?? 0
          return (
            <button
              key={kb.id}
              onClick={() => onKbChange(kb.name)}
              style={{
                width: "100%", display: "flex", alignItems: "center", gap: "10px",
                padding: "8px 12px", borderRadius: "9px",
                border: active ? "1px solid var(--border-warm)" : "1px solid transparent",
                background: active ? "var(--amber-dim)" : "transparent",
                cursor: "pointer", transition: "all 0.15s", textAlign: "left",
              }}
              onMouseEnter={e => { if (!active) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)" }}
              onMouseLeave={e => { if (!active) (e.currentTarget as HTMLElement).style.background = "transparent" }}
            >
              <span style={{ fontSize: "0.8rem", color: active ? "var(--amber)" : "var(--text-muted)", lineHeight: 1 }}>
                {KB_ICONS[i % KB_ICONS.length]}
              </span>
              <span style={{ flex: 1, fontSize: "0.85rem", fontWeight: active ? 500 : 400, color: active ? "var(--text-primary)" : "var(--text-secondary)", textTransform: "capitalize" }}>
                {kb.name.replace(/_/g, " ")}
              </span>
              {count > 0 && (
                <span style={{ fontSize: "0.68rem", fontFamily: "var(--font-dm-mono), monospace", color: active ? "var(--amber)" : "var(--text-muted)", opacity: 0.7 }}>
                  {count.toLocaleString()}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Divider */}
      <div style={{ height: "1px", background: "var(--border)", margin: "0 12px 16px" }} />

      {/* Chats section */}
      <p style={{ fontSize: "0.68rem", fontWeight: 600, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase", padding: "0 12px", marginBottom: "6px" }}>
        Chats
      </p>

      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "2px" }} className="scrollbar-hide">
        {sessionList.length === 0 && (
          <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", padding: "8px 12px", lineHeight: 1.5 }}>
            No chats yet. Ingest a video to start.
          </p>
        )}

        {sessionList.map(session => {
          const isActive = activeSourceId === session.sourceId
          const msgCount = Math.floor(session.messages.length / 2)
          const isHovered = hoveredSession === session.sourceId

          return (
            <div
              key={session.sourceId}
              style={{ position: "relative" }}
              onMouseEnter={() => setHoveredSession(session.sourceId)}
              onMouseLeave={() => setHoveredSession(null)}
            >
              <button
                onClick={() => onSelectSession(session.sourceId)}
                style={{
                  width: "100%", display: "flex", flexDirection: "column", alignItems: "flex-start",
                  gap: "2px", padding: "9px 12px", borderRadius: "9px",
                  border: isActive ? "1px solid var(--border-warm)" : "1px solid transparent",
                  background: isActive ? "var(--amber-dim)" : isHovered ? "rgba(255,255,255,0.03)" : "transparent",
                  cursor: "pointer", transition: "all 0.15s", textAlign: "left",
                  paddingRight: isHovered ? "32px" : "12px",
                }}
              >
                <span style={{ fontSize: "0.82rem", fontWeight: isActive ? 500 : 400, color: isActive ? "var(--text-primary)" : "var(--text-secondary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", width: "100%", display: "block" }}>
                  {session.sourceTitle}
                </span>
                <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", fontFamily: "var(--font-dm-mono), monospace" }}>
                  {msgCount > 0 ? `${msgCount} message${msgCount !== 1 ? "s" : ""}` : "no messages yet"}
                  {" · "}{session.kbId}
                </span>
              </button>

              {isHovered && (
                <button
                  onClick={e => { e.stopPropagation(); onDeleteSession(session.sourceId) }}
                  style={{
                    position: "absolute", right: "8px", top: "50%", transform: "translateY(-50%)",
                    width: "20px", height: "20px", borderRadius: "5px",
                    border: "none", background: "transparent",
                    color: "var(--text-muted)", fontSize: "0.7rem",
                    cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                  }}
                  onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#fca5a5"; (e.currentTarget as HTMLElement).style.background = "rgba(248,113,113,0.1)" }}
                  onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "var(--text-muted)"; (e.currentTarget as HTMLElement).style.background = "transparent" }}
                >
                  ✕
                </button>
              )}
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <div style={{ padding: "16px 12px 0", borderTop: "1px solid var(--border)", marginTop: "8px" }}>
        <a href="/profile" style={{ display: "flex", alignItems: "center", gap: "10px", padding: "8px 0", textDecoration: "none", cursor: "pointer" }}>
          <div style={{ width: "28px", height: "28px", borderRadius: "50%", background: "var(--amber-dim)", border: "1px solid var(--border-warm)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.7rem", fontWeight: 700, color: "var(--amber)", fontFamily: "var(--font-syne), sans-serif", flexShrink: 0 }}>
            {(user?.displayName || user?.email || "?")[0]?.toUpperCase()}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: "0.78rem", color: "var(--text-primary)", margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {user?.displayName || user?.email?.split("@")[0] || "Account"}
            </p>
            <p style={{ fontSize: "0.65rem", color: "var(--text-muted)", margin: 0, fontFamily: "var(--font-dm-mono), monospace" }}>
              View profile →
            </p>
          </div>
        </a>
      </div>
    </div>
  )
}
