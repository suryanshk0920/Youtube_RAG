"use client"

import { useEffect, useState, useCallback } from "react"
import { getLimits } from "@/lib/api"
import { useUsage } from "@/context/UsageContext"
import { UpgradeModal } from "./UpgradeModal"
import type { UserLimitsSummary } from "@/lib/api"

export function UsageDashboard() {
  const [limits, setLimits] = useState<UserLimitsSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const { refreshTrigger, cachedLimits, setCachedLimits } = useUsage()

  const loadLimits = useCallback(async () => {
    try {
      setError(false)
      const data = await getLimits()
      setLimits(data)
      setCachedLimits(data)
    } catch (error) {
      console.error("Failed to load limits:", error)
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [setCachedLimits])

  useEffect(() => {
    // Use cached limits if available
    if (cachedLimits) {
      setLimits(cachedLimits)
      return
    }
    
    // Otherwise load with delay
    const timer = setTimeout(() => {
      setLoading(true)
      loadLimits()
    }, 1000)

    return () => clearTimeout(timer)
  }, [cachedLimits, loadLimits])

  // Refresh when usage context triggers update (after video ingestion or chat)
  useEffect(() => {
    if (refreshTrigger > 0) {
      loadLimits()
    }
  }, [refreshTrigger, loadLimits])

  if (loading && !limits) {
    return (
      <div style={{ 
        padding: "8px 12px", 
        borderRadius: "8px", 
        border: "1px solid var(--border)",
        background: "var(--bg-surface)",
        opacity: 0.5
      }}>
        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textAlign: "center" }}>
          Loading usage...
        </div>
      </div>
    )
  }

  if (error || !limits) return null

  const videoProgress = (limits.usage.videos_today / limits.usage.videos_limit) * 100
  const questionProgress = (limits.usage.questions_today / limits.usage.questions_limit) * 100

  return (
    <>
    <div style={{ 
      padding: "10px 12px", 
      borderRadius: "8px", 
      border: "1px solid var(--border)",
      background: "var(--bg-surface)"
    }}>
      {/* Plan badge */}
      <div style={{ 
        display: "flex", 
        alignItems: "center", 
        justifyContent: "space-between",
        marginBottom: "10px"
      }}>
        <div style={{
          padding: "3px 6px",
          borderRadius: "4px",
          background: limits.plan.type === "free" ? "rgba(156,163,175,0.1)" : "var(--amber-dim)",
          border: `1px solid ${limits.plan.type === "free" ? "rgba(156,163,175,0.2)" : "var(--border-warm)"}`,
          fontSize: "0.65rem",
          fontWeight: 600,
          color: limits.plan.type === "free" ? "var(--text-muted)" : "var(--amber)",
          textTransform: "uppercase",
          letterSpacing: "0.05em"
        }}>
          {limits.plan.type} Plan
        </div>
        
        {limits.upgrade_required && (
          <div style={{
            fontSize: "0.65rem",
            color: "#fca5a5",
            fontWeight: 500
          }}>
            Limit reached
          </div>
        )}
      </div>

      {/* Usage bars */}
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        {/* Videos */}
        <div>
          <div style={{ 
            display: "flex", 
            justifyContent: "space-between", 
            alignItems: "center",
            marginBottom: "3px"
          }}>
            <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>
              Videos today
            </span>
            <span style={{ 
              fontSize: "0.65rem", 
              color: "var(--text-muted)",
              fontFamily: "var(--font-dm-mono), monospace"
            }}>
              {limits.usage.videos_today}/{limits.usage.videos_limit}
            </span>
          </div>
          <div style={{
            height: "3px",
            borderRadius: "2px",
            background: "var(--border)",
            overflow: "hidden"
          }}>
            <div style={{
              height: "100%",
              borderRadius: "2px",
              background: videoProgress >= 100 ? "#fca5a5" : "var(--amber)",
              width: `${Math.min(videoProgress, 100)}%`,
              transition: "width 0.3s ease"
            }} />
          </div>
        </div>

        {/* Questions */}
        <div>
          <div style={{ 
            display: "flex", 
            justifyContent: "space-between", 
            alignItems: "center",
            marginBottom: "3px"
          }}>
            <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>
              Questions today
            </span>
            <span style={{ 
              fontSize: "0.65rem", 
              color: "var(--text-muted)",
              fontFamily: "var(--font-dm-mono), monospace"
            }}>
              {limits.usage.questions_today}/{limits.usage.questions_limit}
            </span>
          </div>
          <div style={{
            height: "3px",
            borderRadius: "2px",
            background: "var(--border)",
            overflow: "hidden"
          }}>
            <div style={{
              height: "100%",
              borderRadius: "2px",
              background: questionProgress >= 100 ? "#fca5a5" : "var(--amber)",
              width: `${Math.min(questionProgress, 100)}%`,
              transition: "width 0.3s ease"
            }} />
          </div>
        </div>
      </div>

      {/* Reset time */}
      <div style={{ 
        marginTop: "6px",
        fontSize: "0.6rem", 
        color: "var(--text-muted)",
        textAlign: "center",
        fontFamily: "var(--font-dm-mono), monospace"
      }}>
        Resets at midnight UTC
      </div>

      {/* Upgrade button when limit reached */}
      {limits.upgrade_required && limits.plan.type === "free" && (
        <button
          onClick={() => setShowUpgradeModal(true)}
          style={{
            width: "100%",
            marginTop: "10px",
            padding: "8px",
            borderRadius: "8px",
            border: "1px solid var(--border-warm)",
            background: "var(--amber-dim)",
            color: "var(--amber)",
            fontSize: "0.75rem",
            fontWeight: 600,
            cursor: "pointer",
            fontFamily: "var(--font-syne), sans-serif",
            transition: "all 0.15s",
          }}
          onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(245,158,11,0.2)"}
          onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "var(--amber-dim)"}
        >
          Upgrade to Pro →
        </button>
      )}
    </div>
    
    {showUpgradeModal && (
      <UpgradeModal
        onClose={() => setShowUpgradeModal(false)}
        reason="You've reached your daily limit. Upgrade for higher limits!"
      />
    )}
    </>
  )
}