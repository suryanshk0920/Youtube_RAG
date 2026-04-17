"use client"
import type { IntroData } from "@/types"

interface Props {
  intro: IntroData
  onQuestionSelect: (q: string) => void
}

export function IntroCard({ intro, onQuestionSelect }: Props) {
  return (
    <div
      className="animate-fade-up animate-glow-breathe stagger"
      style={{
        borderRadius: "16px",
        border: "1px solid var(--border-warm)",
        background: "linear-gradient(135deg, rgba(245,158,11,0.05) 0%, var(--bg-surface) 60%)",
        padding: "20px",
        marginBottom: "24px",
      }}
    >
      {/* Header */}
      <div className="animate-fade-up" style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
        <div style={{
          width: "24px", height: "24px", borderRadius: "7px",
          background: "var(--amber-dim)", border: "1px solid var(--border-warm)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: "0.6rem",
          color: "var(--amber)",
        }}>
          TQ
        </div>
        <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 600, fontSize: "0.8rem", color: "var(--text-secondary)", letterSpacing: "0.02em" }}>
          VIDEO SUMMARY
        </span>
      </div>

      {/* Overview */}
      <p className="animate-fade-up" style={{ fontSize: "0.875rem", color: "var(--text-primary)", lineHeight: 1.75, marginBottom: "18px" }}>
        {intro.intro}
      </p>

      {/* Topics */}
      {intro.topics.length > 0 && (
        <div className="animate-fade-up" style={{ marginBottom: "18px" }}>
          <p style={{ fontSize: "0.65rem", fontWeight: 600, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "10px" }}>
            Topics covered
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }} className="stagger">
            {intro.topics.map((t, i) => (
              <div key={i} className="animate-fade-up" style={{ display: "flex", alignItems: "flex-start", gap: "8px" }}>
                <span style={{ color: "var(--amber)", fontSize: "0.5rem", marginTop: "6px", flexShrink: 0 }}>◆</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>{t}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Divider */}
      {intro.questions.length > 0 && (
        <div style={{ height: "1px", background: "var(--border)", marginBottom: "14px" }} />
      )}

      {/* Suggested questions */}
      {intro.questions.length > 0 && (
        <div className="animate-fade-up">
          <p style={{ fontSize: "0.65rem", fontWeight: 600, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "8px" }}>
            Ask something
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "5px" }} className="stagger">
            {intro.questions.map((q, i) => (
              <button
                key={i}
                onClick={() => onQuestionSelect(q)}
                className="animate-fade-up"
                style={{
                  textAlign: "left",
                  padding: "9px 12px",
                  borderRadius: "9px",
                  border: "1px solid var(--border)",
                  background: "transparent",
                  fontSize: "0.8rem",
                  color: "var(--text-secondary)",
                  cursor: "pointer",
                  transition: "all 0.18s ease",
                  lineHeight: 1.4,
                }}
                onMouseEnter={e => {
                  const el = e.currentTarget as HTMLElement
                  el.style.background = "var(--amber-glow)"
                  el.style.borderColor = "var(--border-warm)"
                  el.style.color = "var(--text-primary)"
                }}
                onMouseLeave={e => {
                  const el = e.currentTarget as HTMLElement
                  el.style.background = "transparent"
                  el.style.borderColor = "var(--border)"
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
  )
}
