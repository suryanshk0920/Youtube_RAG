"use client"
import { useState } from "react"
import ReactMarkdown from "react-markdown"
import { CitationChip } from "./CitationChip"
import type { Message } from "@/types"

function StreamingCursor() {
  return (
    <span
      className="animate-pulse-amber"
      style={{
        display: "inline-block", width: "2px", height: "14px",
        background: "var(--amber)", borderRadius: "1px",
        marginLeft: "2px", verticalAlign: "middle",
      }}
    />
  )
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch { /* silent */ }
  }

  return (
    <button
      onClick={copy}
      title="Copy answer"
      style={{
        padding: "3px 8px", borderRadius: "5px", fontSize: "0.7rem",
        border: "1px solid var(--border)", background: "transparent",
        color: copied ? "#6ee7b7" : "var(--text-muted)",
        cursor: "pointer", transition: "all 0.15s",
        fontFamily: "var(--font-dm-mono), monospace",
      }}
      onMouseEnter={e => (e.currentTarget as HTMLElement).style.borderColor = "var(--border-warm)"}
      onMouseLeave={e => (e.currentTarget as HTMLElement).style.borderColor = "var(--border)"}
    >
      {copied ? "✓ copied" : "⎘ copy"}
    </button>
  )
}

export function MessageBubble({ message, onQuestionSelect }: { message: Message; onQuestionSelect?: (q: string) => void }) {
  const isUser = message.role === "user"
  const isSummary = message.role === "summary"

  if (isUser) {
    return (
      <div className="animate-fade-up" style={{ display: "flex", justifyContent: "flex-end", marginBottom: "20px" }}>
        <div style={{
          maxWidth: "70%", padding: "14px 18px",
          borderRadius: "16px 16px 4px 16px",
          background: "var(--bg-elevated)", 
          border: "1px solid rgba(255,255,255,0.04)",
          fontSize: "0.95rem", lineHeight: 1.65, color: "var(--text-primary)",
        }}>
          {message.content}
        </div>
      </div>
    )
  }

  if (isSummary && message.summaryData) {
    const intro = message.summaryData
    return (
      <div className="animate-fade-up" style={{ marginBottom: "28px" }}>
        <div
          style={{
            borderRadius: "16px",
            border: "1px solid rgba(208,188,255,0.1)",
            borderLeft: "2px solid var(--amber)",
            background: "linear-gradient(135deg, rgba(255,185,95,0.04) 0%, var(--bg-surface) 60%)",
            padding: "24px",
          }}
        >
          {/* Header */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
            <div style={{
              width: "28px", height: "28px", borderRadius: "8px",
              background: "rgba(255,185,95,0.15)", 
              display: "flex", alignItems: "center", justifyContent: "center",
              fontFamily: "'Manrope', sans-serif", fontWeight: 700, fontSize: "0.7rem",
              color: "var(--amber)",
            }}>
              TQ
            </div>
            <span style={{ fontFamily: "'Manrope', sans-serif", fontWeight: 600, fontSize: "0.7rem", color: "var(--amber)", letterSpacing: "0.15em", textTransform: "uppercase" }}>
              Video Summary
            </span>
          </div>

          {/* Overview */}
          <p style={{ fontSize: "0.95rem", color: "var(--text-primary)", lineHeight: 1.7, marginBottom: "20px" }}>
            {intro.intro}
          </p>

          {/* Topics */}
          {intro.topics.length > 0 && (
            <div style={{ marginBottom: "20px" }}>
              <p style={{ fontSize: "0.7rem", fontWeight: 600, letterSpacing: "0.15em", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "12px" }}>
                Topics Covered
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {intro.topics.map((t, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
                    <span style={{ color: "var(--amber)", fontSize: "0.6rem", marginTop: "6px", flexShrink: 0 }}>●</span>
                    <span style={{ fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>{t}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Divider */}
          {intro.questions.length > 0 && (
            <div style={{ height: "1px", background: "rgba(255,255,255,0.05)", marginBottom: "16px" }} />
          )}

          {/* Suggested questions */}
          {intro.questions.length > 0 && (
            <div>
              <p style={{ fontSize: "0.7rem", fontWeight: 600, letterSpacing: "0.15em", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "10px" }}>
                Ask Something
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {intro.questions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => onQuestionSelect?.(q)}
                    style={{
                      textAlign: "left",
                      padding: "10px 14px",
                      borderRadius: "10px",
                      border: "1px solid rgba(255,255,255,0.06)",
                      background: "rgba(255,255,255,0.02)",
                      fontSize: "0.88rem",
                      color: "var(--text-secondary)",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                      lineHeight: 1.5,
                    }}
                    onMouseEnter={e => {
                      const el = e.currentTarget as HTMLElement
                      el.style.background = "rgba(255,185,95,0.08)"
                      el.style.borderColor = "rgba(208,188,255,0.2)"
                      el.style.color = "var(--text-primary)"
                    }}
                    onMouseLeave={e => {
                      const el = e.currentTarget as HTMLElement
                      el.style.background = "rgba(255,255,255,0.02)"
                      el.style.borderColor = "rgba(255,255,255,0.06)"
                      el.style.color = "var(--text-secondary)"
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="animate-fade-up" style={{ display: "flex", gap: "12px", marginBottom: "28px" }}>
      {/* Avatar */}
      <div style={{
        flexShrink: 0, width: "28px", height: "28px", borderRadius: "8px",
        background: "rgba(255,185,95,0.15)",
        display: "flex", alignItems: "center", justifyContent: "center",
        marginTop: "2px", fontFamily: "var(--font-syne), sans-serif",
        fontWeight: 700, fontSize: "0.7rem", color: "var(--amber)",
      }}>
        TQ
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          background: "var(--bg-surface)",
          border: "1px solid rgba(255,255,255,0.04)",
          borderLeft: "2px solid rgba(208,188,255,0.2)",
          padding: "16px 18px",
          borderRadius: "16px",
          borderTopLeftRadius: "4px",
        }}>
          <div className="tq-prose" style={{ fontSize: "0.95rem" }}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {message.isStreaming && <StreamingCursor />}
          </div>
        </div>

        {/* Footer: citations + copy */}
        {!message.isStreaming && message.content && (
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginTop: "12px", flexWrap: "wrap", gap: "8px", minWidth: 0, overflow: "hidden" }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", minWidth: 0, flex: 1, overflow: "hidden" }}>
              {message.citations?.map((c, i) => (
                <CitationChip key={i} citation={c} />
              ))}
            </div>
            <CopyButton text={message.content} />
          </div>
        )}
      </div>
    </div>
  )
}
