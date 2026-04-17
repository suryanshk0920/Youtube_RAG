"use client"
import type { Citation } from "@/types"

export function CitationChip({ citation }: { citation: Citation }) {
  const shortTitle = citation.video_title.length > 28
    ? citation.video_title.slice(0, 28) + "…"
    : citation.video_title

  return (
    <a
      href={citation.youtube_url}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: "4px 10px 4px 8px",
        borderRadius: "6px",
        border: "1px solid var(--border-warm)",
        background: "var(--amber-glow)",
        textDecoration: "none",
        transition: "all 0.18s ease",
        cursor: "pointer",
      }}
      onMouseEnter={e => {
        const el = e.currentTarget as HTMLElement
        el.style.background = "var(--amber-dim)"
        el.style.borderColor = "rgba(245,158,11,0.35)"
      }}
      onMouseLeave={e => {
        const el = e.currentTarget as HTMLElement
        el.style.background = "var(--amber-glow)"
        el.style.borderColor = "var(--border-warm)"
      }}
    >
      {/* Play triangle */}
      <span style={{ color: "var(--amber)", fontSize: "0.65rem", lineHeight: 1 }}>▶</span>
      <span style={{ fontSize: "0.82rem", color: "var(--text-secondary)", fontFamily: "'DM Sans', sans-serif" }}>
        {shortTitle}
      </span>
      <span style={{ fontSize: "0.78rem", color: "var(--amber)", fontFamily: "'DM Mono', monospace", fontWeight: 500 }}>
        {citation.timestamp_label}
      </span>
    </a>
  )
}
