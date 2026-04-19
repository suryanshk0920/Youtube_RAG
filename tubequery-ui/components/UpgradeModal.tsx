"use client"

import { useState } from "react"
import { initiateUpgrade } from "@/lib/api"

interface Props {
  onClose: () => void
  reason?: string  // what triggered the modal
  upgradeMessage?: {
    title: string
    message: string
    cta: string
    benefits: string[]
  }
}

const DEFAULT_FEATURES = [
  { icon: "📹", text: "50 videos per day (vs 3 on free)" },
  { icon: "💬", text: "500 questions per day (vs 20 on free)" },
  { icon: "📚", text: "Unlimited knowledge bases" },
  { icon: "⚡", text: "Priority processing" },
  { icon: "🔄", text: "1 year history retention" },
  { icon: "📤", text: "Export conversations" },
]

export function UpgradeModal({ onClose, reason, upgradeMessage }: Props) {
  const [isLoading, setIsLoading] = useState(false)

  const handleUpgrade = async () => {
    setIsLoading(true)
    try {
      const result = await initiateUpgrade("pro", "monthly")
      // TODO: Redirect to Stripe checkout
      window.open(result.checkout_url, '_blank')
    } catch (error) {
      console.error("Upgrade failed:", error)
      alert("Upgrade failed. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const features = upgradeMessage?.benefits 
    ? upgradeMessage.benefits.map((text, i) => ({ icon: "✨", text }))
    : DEFAULT_FEATURES

  const title = upgradeMessage?.title || "Upgrade to Pro"
  const message = upgradeMessage?.message || reason
  const cta = upgradeMessage?.cta || "Upgrade to Pro"

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "fixed", 
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 100,
          background: "rgba(0,0,0,0.7)",
          backdropFilter: "blur(4px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "16px",
        }}
      >
        {/* Modal */}
        <div
          onClick={(e) => e.stopPropagation()}
          className="animate-fade-up"
          style={{
            width: "min(480px, 100%)",
            maxHeight: "90vh",
            overflowY: "auto",
            background: "var(--bg-surface)",
            border: "1px solid var(--border-warm)",
            borderRadius: "20px",
            padding: "32px",
            boxShadow: "0 0 60px rgba(245,158,11,0.15)",
            position: "relative",
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
            {title}
          </p>
          {message && (
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: 0, lineHeight: 1.5 }}>
              {message}
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
          {features.map((f, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "1rem", flexShrink: 0 }}>{f.icon}</span>
              <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{f.text}</span>
            </div>
          ))}
        </div>

        {/* CTA */}
        <button
          onClick={handleUpgrade}
          disabled={isLoading}
          style={{
            width: "100%", padding: "14px",
            borderRadius: "12px",
            border: "1px solid var(--border-warm)",
            background: isLoading 
              ? "rgba(245,158,11,0.1)" 
              : "linear-gradient(135deg, rgba(245,158,11,0.2), rgba(245,158,11,0.1))",
            color: "var(--amber)", fontSize: "1rem", fontWeight: 700,
            fontFamily: "var(--font-syne), sans-serif",
            cursor: isLoading ? "not-allowed" : "pointer", 
            letterSpacing: "0.01em",
            transition: "all 0.2s",
            opacity: isLoading ? 0.7 : 1,
          }}
          onMouseEnter={e => !isLoading && ((e.currentTarget as HTMLElement).style.background = "rgba(245,158,11,0.25)")}
          onMouseLeave={e => !isLoading && ((e.currentTarget as HTMLElement).style.background = "linear-gradient(135deg, rgba(245,158,11,0.2), rgba(245,158,11,0.1))")}
        >
          {isLoading ? "Processing..." : `${cta} →`}
        </button>

        <p style={{ textAlign: "center", fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "12px", fontFamily: "var(--font-dm-mono), monospace" }}>
          Free plan: 3 videos/day · 20 questions/day · 7 day history
        </p>
        </div>
      </div>
    </>
  )
}
