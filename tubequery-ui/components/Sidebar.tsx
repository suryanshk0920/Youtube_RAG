"use client"
import clsx from "clsx"

const KBS = ["default", "health", "tech", "finance"]

const KB_ICONS: Record<string, string> = {
  default: "◈",
  health:  "◉",
  tech:    "◎",
  finance: "◍",
}

interface Props {
  activeKb: string
  chunkCounts: Record<string, number>
  onKbChange: (kb: string) => void
}

export function Sidebar({ activeKb, chunkCounts, onKbChange }: Props) {
  return (
    <div className="flex flex-col h-full py-6 px-3">
      {/* Wordmark */}
      <div className="px-3 mb-8">
        <p style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: "1.1rem", letterSpacing: "-0.03em", color: "var(--text-primary)" }}>
          Tube<span style={{ color: "var(--amber)" }}>Query</span>
        </p>
        <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "2px", fontFamily: "'DM Mono', monospace" }}>
          v1.0 · rag assistant
        </p>
      </div>

      {/* Section label */}
      <p style={{ fontSize: "0.65rem", fontWeight: 600, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase", padding: "0 12px", marginBottom: "8px" }}>
        Libraries
      </p>

      {/* KB list */}
      <div className="space-y-0.5 stagger">
        {KBS.map((kb) => {
          const active = activeKb === kb
          const count = chunkCounts[kb] ?? 0
          return (
            <button
              key={kb}
              onClick={() => onKbChange(kb)}
              className="animate-fade-up"
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "9px 12px",
                borderRadius: "10px",
                border: active ? "1px solid var(--border-warm)" : "1px solid transparent",
                background: active ? "var(--amber-dim)" : "transparent",
                cursor: "pointer",
                transition: "all 0.18s ease",
                textAlign: "left",
              }}
              onMouseEnter={e => { if (!active) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)" }}
              onMouseLeave={e => { if (!active) (e.currentTarget as HTMLElement).style.background = "transparent" }}
            >
              <span style={{
                fontSize: "0.85rem",
                color: active ? "var(--amber)" : "var(--text-muted)",
                transition: "color 0.18s",
                lineHeight: 1,
              }}>
                {KB_ICONS[kb] ?? "◇"}
              </span>
              <span style={{
                flex: 1,
                fontSize: "0.8rem",
                fontWeight: active ? 500 : 400,
                color: active ? "var(--text-primary)" : "var(--text-secondary)",
                textTransform: "capitalize",
                transition: "color 0.18s",
              }}>
                {kb}
              </span>
              {count > 0 && (
                <span style={{
                  fontSize: "0.65rem",
                  fontFamily: "'DM Mono', monospace",
                  color: active ? "var(--amber)" : "var(--text-muted)",
                  opacity: 0.8,
                }}>
                  {count.toLocaleString()}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Footer */}
      <div style={{ marginTop: "auto", padding: "0 12px" }}>
        <div style={{ height: "1px", background: "var(--border)", marginBottom: "16px" }} />
        <p style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontFamily: "'DM Mono', monospace", lineHeight: 1.6 }}>
          embeddings run locally<br />
          llm via openrouter
        </p>
      </div>
    </div>
  )
}
