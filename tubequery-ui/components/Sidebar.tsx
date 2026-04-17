"use client"
import { useState } from "react"
import type { ChatSession } from "@/types"

const KBS = ["default", "health", "tech", "finance"]
const KB_ICONS: Record<string, string> = { default: "◈", health: "◉", tech: "◎", finance: "◍" }

interface Props {
  activeKb: string
  activeSourceId: string | null
  chunkCounts: Record<string, number>
  sessions: Record<string, ChatSession>
  onKbChange: (kb: string) => void
  onSelectSession: (sourceId: string) => void
  onDeleteSession: (sourceId: string) => void
}

export function Sidebar({ activeKb, activeSourceId, chunkCounts, sessions, onKbChange, onSelectSession, onDeleteSession }: Props) {
  const [hoveredSession, setHoveredSession] = useState<string | null>(null)

  // Group sessions by KB, sorted newest first
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
      <p style={{ fontSize: "0.68rem", fontWeight: 600, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase", padding: "0 12px", marginBottom: "6px" }}>
        Libraries
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: "2px", marginBottom: "20px" }}>
        {KBS.map(kb => {
          const active = activeKb === kb
          const count = chunkCounts[kb] ?? 0
          return (
            <button
              key={kb}
              onClick={() => onKbChange(kb)}
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
                {KB_ICONS[kb] ?? "◇"}
              </span>
              <span style={{ flex: 1, fontSize: "0.85rem", fontWeight: active ? 500 : 400, color: active ? "var(--text-primary)" : "var(--text-secondary)", textTransform: "capitalize" }}>
                {kb}
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

      {/* Chats section — Claude-style */}
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
                <span style={{
                  fontSize: "0.82rem", fontWeight: isActive ? 500 : 400,
                  color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                  width: "100%", display: "block",
                }}>
                  {session.sourceTitle}
                </span>
                <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", fontFamily: "var(--font-dm-mono), monospace" }}>
                  {msgCount > 0 ? `${msgCount} message${msgCount !== 1 ? "s" : ""}` : "no messages yet"}
                  {" · "}{session.kbId}
                </span>
              </button>

              {/* Delete button on hover */}
              {isHovered && (
                <button
                  onClick={e => { e.stopPropagation(); onDeleteSession(session.sourceId) }}
                  style={{
                    position: "absolute", right: "8px", top: "50%", transform: "translateY(-50%)",
                    width: "20px", height: "20px", borderRadius: "5px",
                    border: "none", background: "transparent",
                    color: "var(--text-muted)", fontSize: "0.7rem",
                    cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                    transition: "all 0.15s",
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
        <p style={{ fontSize: "0.68rem", color: "var(--text-muted)", fontFamily: "var(--font-dm-mono), monospace", lineHeight: 1.6, margin: 0 }}>
          embeddings run locally<br />
          llm via openrouter
        </p>
      </div>
    </div>
  )
}
