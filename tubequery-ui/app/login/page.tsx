"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"

export default function LoginPage() {
  const { signInWithGoogle, signInWithEmail, signUpWithEmail } = useAuth()
  const router = useRouter()
  const [mode, setMode] = useState<"signin" | "signup">("signin")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleGoogle() {
    setError("")
    setLoading(true)
    try {
      await signInWithGoogle()
      router.push("/")
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Sign in failed")
    } finally {
      setLoading(false)
    }
  }

  async function handleEmail(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      if (mode === "signin") await signInWithEmail(email, password)
      else await signUpWithEmail(email, password)
      router.push("/")
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Authentication failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: "100dvh", display: "flex", alignItems: "center", justifyContent: "center",
      background: "var(--bg-base)", padding: "24px",
    }}>
      <div style={{
        width: "100%", maxWidth: "380px",
        background: "var(--bg-surface)", borderRadius: "16px",
        border: "1px solid var(--border)", padding: "36px 32px",
      }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div style={{
            width: "48px", height: "48px", borderRadius: "14px",
            background: "var(--amber-dim)", border: "1px solid var(--border-warm)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: "var(--font-syne), sans-serif", fontWeight: 800,
            fontSize: "1rem", color: "var(--amber)", margin: "0 auto 16px",
          }}>TQ</div>
          <p style={{ fontFamily: "var(--font-syne), sans-serif", fontWeight: 800, fontSize: "1.4rem", letterSpacing: "-0.03em", color: "var(--text-primary)", margin: 0 }}>
            Tube<span style={{ color: "var(--amber)" }}>Query</span>
          </p>
          <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "4px" }}>
            {mode === "signin" ? "Sign in to your account" : "Create your account"}
          </p>
        </div>

        {/* Google */}
        <button
          onClick={handleGoogle}
          disabled={loading}
          style={{
            width: "100%", padding: "11px", borderRadius: "10px",
            border: "1px solid var(--border)", background: "var(--bg-elevated)",
            color: "var(--text-primary)", fontSize: "0.9rem", fontWeight: 500,
            cursor: loading ? "not-allowed" : "pointer", display: "flex",
            alignItems: "center", justifyContent: "center", gap: "10px",
            marginBottom: "20px", transition: "all 0.15s",
          }}
        >
          <svg width="18" height="18" viewBox="0 0 18 18">
            <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"/>
            <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"/>
            <path fill="#FBBC05" d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"/>
            <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/>
          </svg>
          Continue with Google
        </button>

        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "20px" }}>
          <div style={{ flex: 1, height: "1px", background: "var(--border)" }} />
          <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "var(--font-dm-mono), monospace" }}>or</span>
          <div style={{ flex: 1, height: "1px", background: "var(--border)" }} />
        </div>

        {/* Email form */}
        <form onSubmit={handleEmail} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <input
            type="email" value={email} onChange={e => setEmail(e.target.value)}
            placeholder="Email" required
            style={{
              padding: "10px 12px", borderRadius: "9px", border: "1px solid var(--border)",
              background: "var(--bg-elevated)", color: "var(--text-primary)",
              fontSize: "0.9rem", outline: "none",
            }}
            onFocus={e => (e.target.style.borderColor = "rgba(245,158,11,0.4)")}
            onBlur={e => (e.target.style.borderColor = "var(--border)")}
          />
          <input
            type="password" value={password} onChange={e => setPassword(e.target.value)}
            placeholder="Password" required minLength={6}
            style={{
              padding: "10px 12px", borderRadius: "9px", border: "1px solid var(--border)",
              background: "var(--bg-elevated)", color: "var(--text-primary)",
              fontSize: "0.9rem", outline: "none",
            }}
            onFocus={e => (e.target.style.borderColor = "rgba(245,158,11,0.4)")}
            onBlur={e => (e.target.style.borderColor = "var(--border)")}
          />

          {error && (
            <p style={{ fontSize: "0.8rem", color: "#fca5a5", margin: 0 }}>{error}</p>
          )}

          <button
            type="submit" disabled={loading}
            style={{
              padding: "11px", borderRadius: "10px",
              border: "1px solid var(--border-warm)", background: "var(--amber-dim)",
              color: "var(--amber)", fontSize: "0.9rem", fontWeight: 600,
              fontFamily: "var(--font-syne), sans-serif",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "…" : mode === "signin" ? "Sign in" : "Create account"}
          </button>
        </form>

        <p style={{ textAlign: "center", fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "20px" }}>
          {mode === "signin" ? "Don't have an account? " : "Already have an account? "}
          <button
            onClick={() => { setMode(mode === "signin" ? "signup" : "signin"); setError("") }}
            style={{ background: "none", border: "none", color: "var(--amber)", cursor: "pointer", fontSize: "0.8rem" }}
          >
            {mode === "signin" ? "Sign up" : "Sign in"}
          </button>
        </p>
      </div>
    </div>
  )
}
