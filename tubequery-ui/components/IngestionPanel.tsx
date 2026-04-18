"use client"
import { useState } from "react"
import { deleteSource, getIntro, getYoutubeThumbnail, streamIngest } from "@/lib/api"
import type { IntroData, Source } from "@/types"

interface Props {
  sources: Source[]
  activeKb: string
  onSourcesChange: () => void
  onIntroReady: (intro: IntroData) => void
  onSummarising: () => void
}

function Spinner() {
  return (
    <svg className="animate-spin-slow" width="13" height="13" viewBox="0 0 14 14" fill="none">
      <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.2" />
      <path d="M7 1.5A5.5 5.5 0 0 1 12.5 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

const STEP_LABELS: Record<string, string> = {
  fetch:       "Reading transcript…",
  chunk:       "Processing text…",
  embed:       "Building search index…",
  store:       "Saving to library…",
  done:        "Indexed!",
  cached:      "Already in library",
  summarising: "Generating summary…",
}

export function IngestionPanel({ sources, activeKb, onSourcesChange, onIntroReady, onSummarising }: Props) {
  const [url, setUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState<string | null>(null)
  const [progress, setProgress] = useState<{ current: number; total: number; video: string } | null>(null)
  const [summaryLoadingId, setSummaryLoadingId] = useState<string | null>(null)
  const [status, setStatus] = useState<{ type: "success" | "error"; msg: string } | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [retryUrl, setRetryUrl] = useState<string | null>(null)

  async function handleIngest(ingestUrl?: string) {
    const target = (ingestUrl ?? url).trim()
    if (!target) return
    setLoading(true)
    setStatus(null)
    setStep("fetch")
    setProgress(null)

    try {
      await streamIngest(target, activeKb, {
        onStep: (s, detail) => {
          setStep(s)
          if (s === "done") setStatus({ type: "success", msg: detail })
        },
        onProgress: (current, total, video) => {
          setProgress({ current, total, video: video.replace("Processing: ", "") })
        },
        onDone: async (result) => {
          setUrl("")
          setRetryUrl(null)
          onSourcesChange()
          setStep("summarising")
          onSummarising()  // tell chat panel to show loading state
          try {
            const intro = await getIntro(result.source_id)
            onIntroReady(intro)
          } catch { /* non-fatal */ }
        },
        onError: (err) => {
          setStatus({ type: "error", msg: err })
          setRetryUrl(target)
        },
      })
    } catch (e: unknown) {
      setStatus({ type: "error", msg: e instanceof Error ? e.message : "Ingestion failed" })
      setRetryUrl(target)
    } finally {
      setLoading(false)
      setStep(null)
      setProgress(null)
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
        <p style={{ fontFamily: "var(--font-syne), sans-serif", fontWeight: 700, fontSize: "1.1rem", color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
          Add Content
        </p>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "2px" }}>
          Video · Playlist · Channel
        </p>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px", display: "flex", flexDirection: "column", gap: "14px" }}>
        {/* Input */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <input
            type="text"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleIngest()}
            placeholder="youtube.com/watch?v=..."
            disabled={loading}
            style={{
              width: "100%", padding: "10px 12px", borderRadius: "10px",
              border: "1px solid var(--border)", background: "var(--bg-elevated)",
              color: "var(--text-primary)", fontSize: "0.9rem", outline: "none",
              transition: "border-color 0.18s", fontFamily: "var(--font-dm-sans), sans-serif",
              opacity: loading ? 0.5 : 1,
            }}
            onFocus={e => (e.target.style.borderColor = "rgba(245,158,11,0.4)")}
            onBlur={e => (e.target.style.borderColor = "var(--border)")}
          />

          <button
            onClick={() => handleIngest()}
            disabled={loading || !url.trim()}
            style={{
              width: "100%", padding: "10px", borderRadius: "10px",
              border: "1px solid var(--border-warm)", background: "var(--amber-dim)",
              color: "var(--amber)", fontSize: "0.9rem", fontWeight: 600,
              fontFamily: "var(--font-syne), sans-serif",
              cursor: loading || !url.trim() ? "not-allowed" : "pointer",
              opacity: !url.trim() && !loading ? 0.4 : 1,
              display: "flex", alignItems: "center", justifyContent: "center", gap: "7px",
              transition: "all 0.18s ease",
            }}
          >
            {loading ? <><Spinner /> Ingesting…</> : "↑ Ingest"}
          </button>

          {/* Step-by-step progress */}
          {loading && step && (
            <div className="animate-fade-in" style={{
              padding: "10px 12px", borderRadius: "9px",
              border: "1px solid var(--border-warm)", background: "var(--amber-glow)",
              display: "flex", flexDirection: "column", gap: "6px",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.82rem", color: "var(--amber)" }}>
                <Spinner />
                <span>{step === "summarising" ? "Generating summary…" : (STEP_LABELS[step] ?? step)}</span>
              </div>
              {progress && progress.total > 1 && (
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-dm-mono), monospace" }}>
                  {progress.current}/{progress.total} · {progress.video.slice(0, 35)}{progress.video.length > 35 ? "…" : ""}
                </div>
              )}
              {progress && progress.total > 1 && (
                <div style={{ height: "3px", borderRadius: "2px", background: "var(--border)", overflow: "hidden" }}>
                  <div style={{
                    height: "100%", borderRadius: "2px", background: "var(--amber)",
                    width: `${Math.round((progress.current / progress.total) * 100)}%`,
                    transition: "width 0.3s ease",
                  }} />
                </div>
              )}
            </div>
          )}

          {/* Status */}
          {status && !loading && (
            <div className="animate-fade-in" style={{
              padding: "8px 12px", borderRadius: "8px", fontSize: "0.82rem",
              border: `1px solid ${status.type === "success" ? "rgba(52,211,153,0.2)" : "rgba(248,113,113,0.2)"}`,
              background: status.type === "success" ? "rgba(52,211,153,0.06)" : "rgba(248,113,113,0.06)",
              color: status.type === "success" ? "#6ee7b7" : "#fca5a5",
              display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px",
            }}>
              <span>{status.type === "success" ? "✓ " : "✕ "}{status.msg}</span>
              {status.type === "error" && retryUrl && (
                <button
                  onClick={() => handleIngest(retryUrl)}
                  style={{
                    padding: "3px 8px", borderRadius: "5px", fontSize: "0.72rem",
                    border: "1px solid rgba(248,113,113,0.3)", background: "rgba(248,113,113,0.1)",
                    color: "#fca5a5", cursor: "pointer", whiteSpace: "nowrap",
                  }}
                >
                  ↺ Retry
                </button>
              )}
            </div>
          )}
        </div>

        {/* Sources list */}
        {sources.length > 0 && (
          <div>
            <p style={{ fontSize: "0.72rem", fontWeight: 600, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "8px" }}>
              Ingested · {sources.length}
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              {sources.map(s => {
                const thumb = getYoutubeThumbnail(s.url)
                const isOpen = expanded === s.id
                return (
                  <div key={s.id} className="animate-fade-up" style={{ borderRadius: "10px", border: "1px solid var(--border)", background: "var(--bg-surface)", overflow: "hidden" }}>
                    {/* Collapsed row — always visible */}
                    <button
                      onClick={() => setExpanded(isOpen ? null : s.id)}
                      style={{
                        width: "100%", display: "flex", alignItems: "center", gap: "10px",
                        padding: "10px 12px", background: "transparent", border: "none",
                        cursor: "pointer", textAlign: "left", transition: "background 0.15s",
                      }}
                      onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.02)"}
                      onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}
                    >
                      {/* Thumbnail — small in collapsed, hidden when expanded (shown below) */}
                      {thumb && !isOpen && (
                        <img
                          src={thumb}
                          alt=""
                          className="source-thumb"
                          style={{ width: "44px", height: "30px", borderRadius: "4px", objectFit: "cover", flexShrink: 0, opacity: 0.85 }}
                          onError={e => { (e.target as HTMLImageElement).style.display = "none" }}
                        />
                      )}
                      {!thumb && !isOpen && (
                        <span style={{ color: "var(--amber)", fontSize: "0.7rem", flexShrink: 0 }}>▶</span>
                      )}
                      <span style={{ flex: 1, fontSize: "0.82rem", color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {s.title}
                      </span>
                      <span style={{
                        fontSize: "0.72rem", color: "var(--text-muted)", flexShrink: 0,
                        display: "inline-block",
                        transition: "transform 0.3s cubic-bezier(0.16,1,0.3,1)",
                        transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
                      }}>
                        ▾
                      </span>
                    </button>

                    {/* Expanded content — thumbnail hero + title + buttons */}
                    <div className={`source-expand-content${isOpen ? " open" : ""}`}>
                      <div style={{ padding: "0 12px 14px" }}>
                        {/* Big thumbnail */}
                        {thumb && (
                          <img
                            src={thumb}
                            alt={s.title}
                            style={{
                              width: "100%", height: "auto", borderRadius: "7px",
                              objectFit: "cover", display: "block", marginBottom: "10px",
                              opacity: 0.9,
                              transition: "opacity 0.3s ease",
                            }}
                            onError={e => { (e.target as HTMLImageElement).style.display = "none" }}
                          />
                        )}

                        {/* Title */}
                        <p style={{ fontSize: "0.82rem", color: "var(--text-primary)", fontWeight: 500, marginBottom: "6px", lineHeight: 1.4 }}>
                          {s.title}
                        </p>

                        {/* Stats */}
                        <div style={{ display: "flex", gap: "10px", marginBottom: "10px", fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "var(--font-dm-mono), monospace" }}>
                          <span>{s.video_count} video{s.video_count !== 1 ? "s" : ""}</span>
                          <span>·</span>
                          <span>{s.chunk_count} chunks</span>
                          <span>·</span>
                          <span style={{ color: s.status === "complete" ? "#6ee7b7" : s.status === "failed" ? "#fca5a5" : "var(--amber)" }}>
                            {s.status}
                          </span>
                        </div>

                        {/* Action buttons */}
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
                              color: "var(--amber)", fontSize: "0.8rem", fontWeight: 600,
                              cursor: summaryLoadingId === s.id ? "not-allowed" : "pointer",
                              display: "flex", alignItems: "center", justifyContent: "center", gap: "5px",
                              opacity: summaryLoadingId === s.id ? 0.6 : 1,
                              fontFamily: "var(--font-syne), sans-serif",
                              transition: "background 0.15s",
                            }}
                          >
                            {summaryLoadingId === s.id ? <><Spinner /> Generating…</> : "✦ Summary"}
                          </button>
                          {s.status === "failed" && (
                            <button
                              onClick={() => handleIngest(s.url)}
                              style={{
                                padding: "7px 10px", borderRadius: "7px",
                                border: "1px solid rgba(245,158,11,0.2)", background: "var(--amber-glow)",
                                color: "var(--amber)", fontSize: "0.8rem", cursor: "pointer",
                              }}
                              title="Retry ingestion"
                            >
                              ↺
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(s)}
                            style={{
                              padding: "7px 10px", borderRadius: "7px",
                              border: "1px solid rgba(248,113,113,0.15)", background: "rgba(248,113,113,0.05)",
                              color: "rgba(248,113,113,0.7)", fontSize: "0.8rem", cursor: "pointer",
                              transition: "background 0.15s",
                            }}
                            onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(248,113,113,0.12)"}
                            onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "rgba(248,113,113,0.05)"}
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {sources.length === 0 && !loading && (
          <div style={{ textAlign: "center", padding: "32px 0", color: "var(--text-muted)", fontSize: "0.85rem" }}>
            <div style={{ fontSize: "1.6rem", marginBottom: "8px", opacity: 0.3 }}>◈</div>
            No videos yet
          </div>
        )}
      </div>
    </div>
  )
}
