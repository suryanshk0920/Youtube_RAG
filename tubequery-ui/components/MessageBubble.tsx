"use client"
import ReactMarkdown from "react-markdown"
import { CitationChip } from "./CitationChip"
import type { Message } from "@/types"

function StreamingCursor() {
  return (
    <span
      className="animate-pulse-amber"
      style={{
        display: "inline-block",
        width: "2px",
        height: "14px",
        background: "var(--amber)",
        borderRadius: "1px",
        marginLeft: "2px",
        verticalAlign: "middle",
      }}
    />
  )
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user"

  if (isUser) {
    return (
      <div className="animate-fade-up" style={{ display: "flex", justifyContent: "flex-end", marginBottom: "16px" }}>
        <div style={{
          maxWidth: "72%",
          padding: "10px 16px",
          borderRadius: "16px 16px 4px 16px",
          background: "var(--bg-elevated)",
          border: "1px solid var(--border)",
          fontSize: "0.975rem",
          lineHeight: 1.65,
          color: "var(--text-primary)",
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
        flexShrink: 0,
        width: "26px",
        height: "26px",
        borderRadius: "8px",
        background: "var(--amber-dim)",
        border: "1px solid var(--border-warm)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        marginTop: "2px",
        fontFamily: "'Syne', sans-serif",
        fontWeight: 700,
        fontSize: "0.75rem",
        color: "var(--amber)",
        letterSpacing: "-0.02em",
      }}>
        TQ
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Markdown content */}
        <div className="tq-prose" style={{ fontSize: "0.975rem" }}>
          <ReactMarkdown>{message.content}</ReactMarkdown>
          {message.isStreaming && <StreamingCursor />}
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="animate-fade-in" style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "12px" }}>
            {message.citations.map((c, i) => (
              <CitationChip key={i} citation={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
