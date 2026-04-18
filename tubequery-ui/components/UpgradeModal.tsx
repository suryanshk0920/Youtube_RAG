"use client"

interface Props {
  onClose: () => void
  reason?: string  // what triggered the modal
}

const PRO_FEATURES = [
  { icon: "📹", text: "100 videos/month (vs 5 on free)" },
  { icon: "💬", text: "Unlimited chat messages" },
  { icon: "📚", text: "Unlimited knowledge bases" },
  { icon: "📋", text: "Playlist & channel ingestion" },
  { icon: "⚡", text: "Priority processing" },
  { icon: "🔄", text: "Sessions sync across devices" },
]

export function UpgradeModal({ onClose, reason }: Props) {
  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "fixed", inset: 0, zIndex: 100,
          background: "rgba(0,0,0,0.7)",
          backdropFilter: "blur(4px)",
        }}
      />

      {/* Modal */}
      <div
        className="animate-fade-up"
        style={{
          position: "fixed", top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 101,
          width: "min(480px, calc(100vw - 32px))",
          background: "var(--bg-surface)",
          border: "1px solid var(--border-warm)",
          borderRadius: "20px",
          padding: "32px",
          boxShadow: "0 0 60px rgba(245,158,11,0.15)",
        }}
      >
        {/* Close */}
        <button
          onClick={onClose}
          style={{
            position: "absolute", top: "16px", right: "16px",
            width: "28px", height: "28px", borderRadius: "8px",
            border: "1px solid var(--border)", background: "transparent",
            color: "var(--text-muted)", cursor: "pointer", fontSize: "0.8rem",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >
          ✕
        </button>

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div style={{
            width: "52px", height: "52px", borderRadius: "14px",
            background: "var(--amber-dim)", border: "1px solid var(--border-warm)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: "var(--font-syne), sans-serif", fontWeight: 800,
            fontSize: "1rem", color: "var(--amber)", margin: "0 auto 16px",
            boxShadow: "0 0 30px rgba(245,158,11,0.2)",
          }}>
            TQ
          </div>
          <p style={{ fontFamily: "var(--font-syne), sans-serif", fontWeight: 800, fontSize: "1.4rem", letterSpacing: "-0.02em", color: "var(--text-primary)", margin: "0 0 8px" }}>
            Upgrade to Pro
          </p>
          {reason && (
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: 0, lineHeight: 1.5 }}>
              {reason}
            </p>
          )}
        </div>

        {/* Pricing */}
        <div style={{
          background: "linear-gradient(135deg, rgba(245,158,11,0.08), rgba(245,158,11,0.03))",
          border: "1px solid var(--border-warm)",
          borderRadius: "14px",
          padding: "20px",
          marginBottom: "24px",
          textAlign: "center",
        }}>
          <p style={{ fontFamily: "var(--font-syne), sans-serif", fontWeight: 800, fontSize: "2.2rem", color: "var(--amber)", margin: "0 0 4px", letterSpacing: "-0.03em" }}>
            $9<span style={{ fontSize: "1rem", fontWeight: 400, color: "var(--text-muted)" }}>/month</span>
          </p>
          <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", margin: 0, fontFamily: "var(--font-dm-mono), monospace" }}>
            cancel anytime · no contracts
          </p>
        </div>

        {/* Features */}
        <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "28px" }}>
          {PRO_FEATURES.map((f, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "1rem", flexShrink: 0 }}>{f.icon}</span>
              <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{f.text}</span>
            </div>
          ))}
        </div>

        {/* CTA */}
        <button
          onClick={() => {
            // TODO: wire to Stripe checkout
            alert("Stripe billing coming soon! Contact us to upgrade early.")
          }}
          style={{
            width: "100%", padding: "14px",
            borderRadius: "12px",
            border: "1px solid var(--border-warm)",
            background: "linear-gradient(135deg, rgba(245,158,11,0.2), rgba(245,158,11,0.1))",
            color: "var(--amber)", fontSize: "1rem", fontWeight: 700,
            fontFamily: "var(--font-syne), sans-serif",
            cursor: "pointer", letterSpacing: "0.01em",
            transition: "all 0.2s",
          }}
          onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(245,158,11,0.25)"}
          onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "linear-gradient(135deg, rgba(245,158,11,0.2), rgba(245,158,11,0.1))"}
        >
          Upgrade to Pro →
        </button>

        <p style={{ textAlign: "center", fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "12px", fontFamily: "var(--font-dm-mono), monospace" }}>
          Free plan: 5 videos · 50 chats · 2 libraries
        </p>
      </div>
    </>
  )
}
