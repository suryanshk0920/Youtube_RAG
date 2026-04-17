"use client"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { fetchProfile, type UserProfile } from "@/lib/api"

const PLAN_COLORS = {
  free:  { bg: "rgba(90,86,80,0.2)",  text: "var(--text-muted)",    border: "var(--border)" },
  pro:   { bg: "rgba(245,158,11,0.1)", text: "var(--amber)",         border: "var(--border-warm)" },
  team:  { bg: "rgba(52,211,153,0.1)", text: "#6ee7b7",              border: "rgba(52,211,153,0.2)" },
}

const PLAN_FEATURES = {
  free:  ["5 videos total", "50 chats/month", "2 knowledge bases"],
  pro:   ["100 videos/month", "Unlimited chats", "Unlimited knowledge bases", "Playlist ingestion"],
  team:  ["Unlimited everything", "Priority processing", "All Pro features"],
}

function UsageBar({ used, limit, label }: { used: number; limit: number; label: string }) {
  const pct = limit === -1 ? 0 : Math.min((used / limit) * 100, 100)
  const isUnlimited = limit === -1
  const isWarning = pct > 80

  return (
    <div style={{ marginBottom: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
        <span style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>{label}</span>
        <span style={{ fontSize: "0.78rem", fontFamily: "var(--font-dm-mono), monospace", color: isUnlimited ? "#6ee7b7" : isWarning ? "#fca5a5" : "var(--text-muted)" }}>
          {isUnlimited ? `${used} · unlimited` : `${used} / ${limit}`}
        </span>
      </div>
      {!isUnlimited && (
        <div style={{ height: "4px", borderRadius: "2px", background: "var(--border)", overflow: "hidden" }}>
          <div style={{
            height: "100%", borderRadius: "2px",
            background: isWarning ? "#fca5a5" : "var(--amber)",
            width: `${pct}%`, transition: "width 0.4s ease",
          }} />
        </div>
      )}
    </div>
  )
}

export default function ProfilePage() {
  const { user, signOut, loading: authLoading } = useAuth()
  const router = useRouter()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) router.push("/login")
  }, [user, authLoading, router])

  useEffect(() => {
    if (!user) return
    fetchProfile().then(p => { setProfile(p); setLoading(false) })
  }, [user])

  async function handleSignOut() {
    await signOut()
    router.push("/login")
  }

  if (authLoading || loading) {
    return (
      <div style={{ minHeight: "100dvh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg-base)" }}>
        <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-dm-mono), monospace", fontSize: "0.82rem" }}>Loading…</div>
      </div>
    )
  }

  const plan = profile?.plan ?? "free"
  const planStyle = PLAN_COLORS[plan]

  return (
    <div style={{ minHeight: "100dvh", background: "var(--bg-base)", padding: "32px 16px" }}>
      <div style={{ maxWidth: "520px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "16px" }}>

        {/* Back */}
        <button
          onClick={() => router.push("/")}
          style={{ alignSelf: "flex-start", background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "0.82rem", fontFamily: "var(--font-dm-mono), monospace", padding: 0 }}
        >
          ← Back
        </button>

        {/* Avatar + name */}
        <div style={{ background: "var(--bg-surface)", borderRadius: "16px", border: "1px solid var(--border)", padding: "24px", display: "flex", alignItems: "center", gap: "16px" }}>
          {profile?.photo_url ? (
            <img src={profile.photo_url} alt="" style={{ width: "56px", height: "56px", borderRadius: "50%", border: "2px solid var(--border-warm)" }} />
          ) : (
            <div style={{ width: "56px", height: "56px", borderRadius: "50%", background: "var(--amber-dim)", border: "1px solid var(--border-warm)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-syne), sans-serif", fontWeight: 700, fontSize: "1.2rem", color: "var(--amber)" }}>
              {(profile?.display_name || profile?.email || "?")[0].toUpperCase()}
            </div>
          )}
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontFamily: "var(--font-syne), sans-serif", fontWeight: 700, fontSize: "1rem", color: "var(--text-primary)", margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {profile?.display_name || "User"}
            </p>
            <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "2px 0 0", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {profile?.email}
            </p>
          </div>
          {/* Plan badge */}
          <span style={{ padding: "4px 10px", borderRadius: "20px", fontSize: "0.72rem", fontWeight: 600, fontFamily: "var(--font-syne), sans-serif", textTransform: "uppercase", letterSpacing: "0.05em", background: planStyle.bg, color: planStyle.text, border: `1px solid ${planStyle.border}`, flexShrink: 0 }}>
            {plan}
          </span>
        </div>

        {/* Usage */}
        <div style={{ background: "var(--bg-surface)", borderRadius: "16px", border: "1px solid var(--border)", padding: "24px" }}>
          <p style={{ fontFamily: "var(--font-syne), sans-serif", fontWeight: 600, fontSize: "0.85rem", color: "var(--text-primary)", margin: "0 0 16px" }}>
            This month's usage
          </p>
          <UsageBar label="Videos ingested" used={profile?.usage.ingest.used ?? 0} limit={profile?.usage.ingest.limit ?? 5} />
          <UsageBar label="Chat messages" used={profile?.usage.chat.used ?? 0} limit={profile?.usage.chat.limit ?? 50} />
        </div>

        {/* Plan features */}
        <div style={{ background: "var(--bg-surface)", borderRadius: "16px", border: "1px solid var(--border)", padding: "24px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
            <p style={{ fontFamily: "var(--font-syne), sans-serif", fontWeight: 600, fontSize: "0.85rem", color: "var(--text-primary)", margin: 0 }}>
              {plan.charAt(0).toUpperCase() + plan.slice(1)} plan
            </p>
            {plan === "free" && (
              <button style={{ padding: "5px 12px", borderRadius: "8px", border: "1px solid var(--border-warm)", background: "var(--amber-dim)", color: "var(--amber)", fontSize: "0.75rem", fontWeight: 600, cursor: "pointer", fontFamily: "var(--font-syne), sans-serif" }}>
                Upgrade →
              </button>
            )}
          </div>
          <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "8px" }}>
            {PLAN_FEATURES[plan].map((f, i) => (
              <li key={i} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                <span style={{ color: plan === "free" ? "var(--amber)" : "#6ee7b7", fontSize: "0.7rem" }}>✓</span>
                {f}
              </li>
            ))}
          </ul>
        </div>

        {/* Account info */}
        <div style={{ background: "var(--bg-surface)", borderRadius: "16px", border: "1px solid var(--border)", padding: "24px" }}>
          <p style={{ fontFamily: "var(--font-syne), sans-serif", fontWeight: 600, fontSize: "0.85rem", color: "var(--text-primary)", margin: "0 0 14px" }}>
            Account
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
              <span style={{ color: "var(--text-muted)" }}>Member since</span>
              <span style={{ color: "var(--text-secondary)", fontFamily: "var(--font-dm-mono), monospace" }}>
                {profile?.created_at ? new Date(profile.created_at).toLocaleDateString("en-US", { month: "short", year: "numeric" }) : "—"}
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
              <span style={{ color: "var(--text-muted)" }}>User ID</span>
              <span style={{ color: "var(--text-muted)", fontFamily: "var(--font-dm-mono), monospace", fontSize: "0.7rem" }}>
                {profile?.uid?.slice(0, 12)}…
              </span>
            </div>
          </div>
        </div>

        {/* Sign out */}
        <button
          onClick={handleSignOut}
          style={{
            width: "100%", padding: "12px", borderRadius: "12px",
            border: "1px solid rgba(248,113,113,0.2)", background: "rgba(248,113,113,0.05)",
            color: "#fca5a5", fontSize: "0.9rem", fontWeight: 600,
            fontFamily: "var(--font-syne), sans-serif", cursor: "pointer",
            transition: "all 0.15s",
          }}
          onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(248,113,113,0.12)"}
          onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "rgba(248,113,113,0.05)"}
        >
          Sign out
        </button>

      </div>
    </div>
  )
}
