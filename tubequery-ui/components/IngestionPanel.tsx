"use client"
import { useState } from "react"
import { deleteSource, getIntro, ingestUrl } from "@/lib/api"
import type { IntroData, Source } from "@/types"

interface Props {
  sources: Source[]
  activeKb: string
  onSourcesChange: () => void
  onIntroReady: (intro: IntroData) => void
}

function Spinner() {
  return (
    <svg className="animate-spin-slow" width="14" height="14" viewBox="0 0 14 14" fill="none">
      <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.2" />
      <path d="M7 1.5A5.5 5.5 0 0 1 12.5 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

export function IngestionPanel({ sources, activeKb, onSourcesChange, onIntroReady }: Props) {
  const [url, setUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [summaryLoadingId, setSummaryLoadingId] = useState<string | null>(null)
  const [status, setStatus] = useState<{ type: "success" | "error"; msg: string } | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)

  async function handleIngest() {
    if (!url.trim()) return
    setLoading(true)
    setStatus(null)
    try {
      const result = await ingestUrl(url.trim(), activeKb)
      setStatus({ type: "success", msg: `${result.chunk_count} chunks indexed` })
      setUrl("")
      onSourcesChange()
      const intro = await getIntro(result.source_id)
      onIntroReady(intro)
    } catch (e: unknown) {
      setStatus({ type: "error", msg: e instanceof Error ? e.message : "Ingestion failed" })
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(source: Source) {
    try {
      await deleteSource(source.id, source.kb_id)
      onSourcesChange()
    } catch { /* silent */ }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Header */}
      <div style={{ padding: "22px 20px 16px", borderBottom: "1px solid var(--border)" }}>
        <p style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: "1.1rem", color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
          Add Content
        </p>
        <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginTop: "2px" }}>
          Paste a YouTube URL
        </p>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px", display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Input area */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <input
            type="text"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleIngest()}
            placeholder="youtube.com/watch?v=..."
            style={{
              width: "100%",
              padding: "10px 12px",
              borderRadius: "10px",
              border: "1px solid var(--border)",
              background: "var(--bg-elevated)",
              color: "var(--text-primary)",
              fontSize: "0.9rem",
              outline: "none",
              transition: "border-color 0.18s",
              fontFamily: "'DM Sans', sans-serif",
            }}
            onFocus={e => (e.target.style.borderColor = "rgba(245,158,11,0.4)")}
            onBlur={e => (e.target.style.borderColor = "var(--border)")}
          />

          <button
            onClick={handleIngest}
            disabled={loading || !url.trim()}
            style={{
              width: "100%",
              padding: "10px",
              borderRadius: "10px",
              border: "1px solid var(--border-warm)",
              background: loading ? "var(--amber-dim)" : "var(--amber-dim)",
              color: "var(--amber)",
              fontSize: "0.9rem",
              fontWeight: 600,
              fontFamily: "'Syne', sans-serif",
              cursor: loading || !url.trim() ? "not-allowed" : "pointer",
              opacity: !url.trim() && !loading ? 0.4 : 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "7px",
              transition: "all 0.18s ease",
              letterSpacing: "0.02em",
            }}
            onMouseEnter={e => { if (!loading && url.trim()) (e.currentTarget as HTMLElement).style.background = "rgba(245,158,11,0.18)" }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "var(--amber-dim)" }}
          >
            {loading ? <><Spinner /> Ingesting…</> : "↑ Ingest"}
          </button>

          {status && (
            <div
              className="animate-fade-in"
              style={{
                padding: "8px 12px",
                borderRadius: "8px",
                fontSize: "0.85rem",
                border: `1px solid ${status.type === "success" ? "rgba(52,211,153,0.2)" : "rgba(248,113,113,0.2)"}`,
                background: status.type === "success" ? "rgba(52,211,153,0.06)" : "rgba(248,113,113,0.06)",
                color: status.type === "success" ? "#6ee7b7" : "#fca5a5",
              }}
            >
              {status.type === "success" ? "✓ " : "✕ "}{status.msg}
            </div>
          )}
        </div>

        {/* Sources */}
        {sources.length > 0 && (
          <div>
            <p style={{ fontSize: "0.75rem", fontWeight: 600, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "8px" }}>
              Ingested · {sources.length}
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              {sources.map(s => (
                <div
                  key={s.id}
                  className="animate-fade-up"
                  style={{ borderRadius: "10px", border: "1px solid var(--border)", background: "var(--bg-surface)", overflow: "hidden" }}
                >
                  <button
                    onClick={() => setExpanded(expanded === s.id ? null : s.id)}
                    style={{
                      width: "100%", display: "flex", alignItems: "center", gap: "8px",
                      padding: "10px 12px", background: "transparent", border: "none",
                      cursor: "pointer", textAlign: "left", transition: "background 0.15s",
                    }}
                    onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.02)"}
                    onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}
                  >
                    <span style={{ color: "var(--amber)", fontSize: "0.7rem", flexShrink: 0 }}>▶</span>
                    <span style={{ flex: 1, fontSize: "0.88rem", color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {s.title}
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", transition: "transform 0.2s", transform: expanded === s.id ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block" }}>
                      ▾
                    </span>
                  </button>

                  {expanded === s.id && (
                    <div className="animate-fade-in" style={{ padding: "0 12px 12px", borderTop: "1px solid var(--border)" }}>
                      <div style={{ display: "flex", gap: "12px", padding: "8px 0", fontSize: "0.8rem", color: "var(--text-muted)", fontFamily: "'DM Mono', monospace" }}>
                        <span>{s.video_count}v</span>
                        <span>·</span>
                        <span>{s.chunk_count} chunks</span>
                      </div>
                      <div style={{ display: "flex", gap: "6px" }}>
                        <button
                          onClick={async () => {
                            setSummaryLoadingId(s.id)
                            try {
                              const intro = await getIntro(s.id)
                              onIntroReady(intro)
                            } finally {
                              setSummaryLoadingId(null)
                            }
                          }}
                          disabled={summaryLoadingId === s.id}
                          style={{
                            flex: 1, padding: "7px", borderRadius: "7px",
                            border: "1px solid var(--border-warm)", background: "var(--amber-glow)",
                            color: "var(--amber)", fontSize: "0.82rem", fontWeight: 600,
                            cursor: summaryLoadingId === s.id ? "not-allowed" : "pointer",
                            display: "flex", alignItems: "center", justifyContent: "center", gap: "5px",
                            opacity: summaryLoadingId === s.id ? 0.6 : 1,
                            transition: "all 0.15s",
                            fontFamily: "'Syne', sans-serif",
                          }}
                        >
                          {summaryLoadingId === s.id ? <><Spinner /> Loading</> : "✦ Summary"}
                        </button>
                        <button
                          onClick={() => handleDelete(s)}
                          style={{
                            padding: "7px 10px", borderRadius: "7px",
                            border: "1px solid rgba(248,113,113,0.15)", background: "rgba(248,113,113,0.05)",
                            color: "rgba(248,113,113,0.7)", fontSize: "0.82rem",
                            cursor: "pointer", transition: "all 0.15s",
                          }}
                          onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(248,113,113,0.12)"}
                          onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "rgba(248,113,113,0.05)"}
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {sources.length === 0 && !loading && (
          <div style={{ textAlign: "center", padding: "32px 0", color: "var(--text-muted)", fontSize: "0.88rem" }}>
            <div style={{ fontSize: "1.6rem", marginBottom: "8px", opacity: 0.3 }}>◈</div>
            No videos yet
          </div>
        )}
      </div>
    </div>
  )
}
