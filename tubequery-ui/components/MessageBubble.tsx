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

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user"

  if (isUser) {
    return (
      <div className="animate-fade-up" style={{ display: "flex", justifyContent: "flex-end", marginBottom: "16px" }}>
        <div style={{
          maxWidth: "72%", padding: "10px 16px",
          borderRadius: "16px 16px 4px 16px",
          background: "var(--bg-elevated)", border: "1px solid var(--border)",
          fontSize: "0.975rem", lineHeight: 1.65, color: "var(--text-primary)",
        }}>
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="animate-fade-up" style={{ display: "flex", gap: "12px", marginBottom: "24px" }}>
      {/* Avatar */}
      <div style={{
        flexShrink: 0, width: "26px", height: "26px", borderRadius: "8px",
        background: "var(--amber-dim)", border: "1px solid var(--border-warm)",
        display: "flex", alignItems: "center", justifyContent: "center",
        marginTop: "2px", fontFamily: "var(--font-syne), sans-serif",
        fontWeight: 700, fontSize: "0.75rem", color: "var(--amber)",
      }}>
        TQ
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="tq-prose" style={{ fontSize: "0.975rem" }}>
          <ReactMarkdown>{message.content}</ReactMarkdown>
          {message.isStreaming && <StreamingCursor />}
        </div>

        {/* Footer: citations + copy */}
        {!message.isStreaming && message.content && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "10px", flexWrap: "wrap", gap: "6px" }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
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
