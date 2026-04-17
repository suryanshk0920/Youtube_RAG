"use client"
import type { Citation } from "@/types"

export function CitationChip({ citation }: { citation: Citation }) {
  // Show the excerpt (the actual dialogue) truncated, not the video title
  const excerpt = citation.excerpt
    ? citation.excerpt.replace(/\.\.\.$/,"").trim().slice(0, 60) + (citation.excerpt.length > 60 ? "…" : "")
    : citation.video_title.slice(0, 40)

  return (
    <a
      href={citation.youtube_url}
      target="_blank"
      rel="noopener noreferrer"
      title={`${citation.video_title} — click to watch at ${citation.timestamp_label}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: "5px 10px 5px 8px",
        borderRadius: "6px",
        border: "1px solid var(--border-warm)",
        background: "var(--amber-glow)",
        textDecoration: "none",
        transition: "all 0.18s ease",
        cursor: "pointer",
        maxWidth: "100%",
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
      <span style={{ color: "var(--amber)", fontSize: "0.65rem", lineHeight: 1, flexShrink: 0 }}>▶</span>
      <span style={{
        fontSize: "0.8rem",
        color: "var(--text-secondary)",
        fontFamily: "var(--font-dm-sans), sans-serif",
        fontStyle: "italic",
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
      }}>
        "{excerpt}"
      </span>
      <span style={{
        fontSize: "0.72rem",
        color: "var(--amber)",
        fontFamily: "var(--font-dm-mono), monospace",
        fontWeight: 500,
        flexShrink: 0,
      }}>
        {citation.timestamp_label}
      </span>
    </a>
  )
}
