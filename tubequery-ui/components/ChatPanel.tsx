"use client"
import { useEffect, useRef, useState } from "react"
import { streamChat } from "@/lib/api"
import { IntroCard } from "./IntroCard"
import { MessageBubble } from "./MessageBubble"
import { UpgradeModal } from "./UpgradeModal"
import { useUsage } from "@/context/UsageContext"
import type { Citation, IntroData, Message } from "@/types"

interface Props {
  activeKb: string
  activeSourceId: string | null
  pendingIntro: IntroData | null
  generatingSummary: boolean
  onIntroDismiss: () => void
  messages: Message[]
  onMessagesChange: (messages: Message[]) => void
}

export function ChatPanel({ activeKb, activeSourceId, pendingIntro, generatingSummary, onIntroDismiss: _, messages, onMessagesChange }: Props) {
  const [input, setInput] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [upgradeModal, setUpgradeModal] = useState<{
    show: boolean
    reason?: string
    upgradeMessage?: any
  }>({ show: false })
  const { refreshUsage } = useUsage()
  const bottomRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  // Ref to always have latest messages in streaming callbacks
  const messagesRef = useRef<Message[]>(messages)
  useEffect(() => { messagesRef.current = messages }, [messages])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = "auto"
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px"
  }, [input])

  async function sendMessage(question: string) {
    if (!question.trim() || isStreaming) return

    const history = messagesRef.current
    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: question.trim() }
    const assistantId = crypto.randomUUID()
    const assistantMsg: Message = { id: assistantId, role: "assistant", content: "", citations: [], isStreaming: true }

    onMessagesChange([...history, userMsg, assistantMsg])
    setInput("")
    setIsStreaming(true)

    const controller = new AbortController()
    abortRef.current = controller

    // Track citations separately so we can save them all at once on done
    const collectedCitations: Citation[] = []
    // Accumulate content locally to avoid stale closure issues
    let accumulatedContent = ""

    await streamChat(
      question.trim(), activeKb, history,
      {
        onToken: token => {
          accumulatedContent += token
          const latest = messagesRef.current
          onMessagesChange(latest.map(m =>
            m.id === assistantId ? { ...m, content: accumulatedContent } : m
          ))
        },
        onCitation: (citation: Citation) => {
          collectedCitations.push(citation)
          // Also update live so chip appears as soon as it arrives
          const latest = messagesRef.current
          onMessagesChange(latest.map(m =>
            m.id === assistantId ? { ...m, citations: [...collectedCitations] } : m
          ))
        },
        onDone: () => {
          // Keep the sources section instead of stripping it
          const finalContent = accumulatedContent.trim()
          // Use functional update to avoid stale closure — always based on latest state
          onMessagesChange(messagesRef.current.map(m =>
            m.id === assistantId
              ? { ...m, isStreaming: false, citations: [...collectedCitations], content: finalContent }
              : m
          ))
          setIsStreaming(false)
          // Refresh usage after successful question
          refreshUsage()
        },
        onError: (err, upgradeRequired, limitDetails) => {
          const latest = messagesRef.current
          
          if (upgradeRequired && limitDetails?.upgrade_message) {
            setUpgradeModal({
              show: true,
              reason: err,
              upgradeMessage: limitDetails.upgrade_message
            })
            // Remove the streaming message since we're showing upgrade modal
            onMessagesChange(latest.filter(m => m.id !== assistantId))
          } else {
            onMessagesChange(latest.map(m =>
              m.id === assistantId ? { ...m, content: `Error: ${err}`, isStreaming: false } : m
            ))
          }
          setIsStreaming(false)
        },
      },
      controller.signal,
      activeSourceId ? [activeSourceId] : undefined
    )
  }

  function stopStream() {
    abortRef.current?.abort()
    onMessagesChange(messagesRef.current.map(m => m.isStreaming ? { ...m, isStreaming: false } : m))
    setIsStreaming(false)
  }

  return (
    <>
      <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
        {/* Messages area */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px 0 16px" }}>
          <div style={{ maxWidth: "780px", margin: "0 auto", padding: "0 16px" }}>

            {/* Summary generating skeleton */}
            {generatingSummary && !pendingIntro && (
              <div className="animate-fade-in animate-glow-breathe" style={{
                borderRadius: "16px", border: "1px solid var(--border-warm)",
                background: "linear-gradient(135deg, rgba(245,158,11,0.05) 0%, var(--bg-surface) 60%)",
                padding: "20px", marginBottom: "24px",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
                  <div style={{ width: "24px", height: "24px", borderRadius: "7px", background: "var(--amber-dim)", border: "1px solid var(--border-warm)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-syne), sans-serif", fontWeight: 700, fontSize: "0.6rem", color: "var(--amber)" }}>TQ</div>
                  <span style={{ fontFamily: "var(--font-syne), sans-serif", fontWeight: 600, fontSize: "0.8rem", color: "var(--text-secondary)", letterSpacing: "0.02em" }}>GENERATING SUMMARY</span>
                  <svg className="animate-spin-slow" width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ marginLeft: "auto" }}>
                    <circle cx="7" cy="7" r="5.5" stroke="var(--amber)" strokeWidth="1.5" strokeOpacity="0.2" />
                    <path d="M7 1.5A5.5 5.5 0 0 1 12.5 7" stroke="var(--amber)" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </div>
                {[100, 85, 92, 70].map((w, i) => (
                  <div key={i} style={{ height: "10px", borderRadius: "5px", background: "var(--border)", marginBottom: "8px", width: `${w}%`, opacity: 0.3 + i * 0.05 }} />
                ))}
              </div>
            )}

            {!pendingIntro && !generatingSummary && messages.length === 0 && (
              <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", paddingTop: "80px", paddingBottom: "60px" }}>
                <div style={{
                  width: "52px", height: "52px", borderRadius: "14px",
                  background: "var(--amber-dim)", border: "1px solid var(--border-warm)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontFamily: "var(--font-syne), sans-serif", fontWeight: 800, fontSize: "1.1rem",
                  color: "var(--amber)", marginBottom: "20px",
                  boxShadow: "0 0 40px rgba(245,158,11,0.1)",
                }}>
                  TQ
                </div>
                <p style={{ fontFamily: "var(--font-syne), sans-serif", fontWeight: 700, fontSize: "1.2rem", color: "var(--text-primary)", marginBottom: "8px", letterSpacing: "-0.02em" }}>
                  TubeQuery
                </p>
                <p style={{ fontSize: "0.92rem", color: "var(--text-muted)", maxWidth: "260px", lineHeight: 1.6 }}>
                  Add a YouTube video on the right, then chat with it!
                </p>
              </div>
            )}

            {pendingIntro && (
              <IntroCard intro={pendingIntro} onQuestionSelect={q => sendMessage(q)} />
            )}

            {messages.map(msg => <MessageBubble key={msg.id} message={msg} onQuestionSelect={q => sendMessage(q)} />)}

            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input */}
        <div style={{ padding: "16px 0 28px" }}>
          <div style={{ maxWidth: "780px", margin: "0 auto", padding: "0 16px" }}>
            <div
              style={{
                display: "flex", alignItems: "center", gap: "12px",
                padding: "12px 16px", borderRadius: "16px",
                border: "1px solid rgba(255,255,255,0.06)", 
                background: "rgba(34,42,61,0.7)",
                backdropFilter: "blur(20px)",
                transition: "border-color 0.2s, box-shadow 0.2s",
              }}
              onFocusCapture={e => {
                const el = e.currentTarget as HTMLElement
                el.style.borderColor = "rgba(208,188,255,0.3)"
                el.style.boxShadow = "0 0 0 3px rgba(208,188,255,0.08)"
              }}
              onBlurCapture={e => {
                const el = e.currentTarget as HTMLElement
                el.style.borderColor = "rgba(255,255,255,0.06)"
                el.style.boxShadow = "none"
              }}
            >
              <textarea
                ref={textareaRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input) } }}
                placeholder="Ask me anything..."
                rows={1}
                style={{
                  flex: 1, background: "transparent", border: "none", outline: "none",
                  resize: "none", fontSize: "0.95rem", color: "var(--text-primary)",
                  fontFamily: "var(--font-dm-sans), sans-serif", lineHeight: 1.6,
                  padding: 0,
                }}
              />
              <button
                onClick={isStreaming ? stopStream : () => sendMessage(input)}
                disabled={!isStreaming && !input.trim()}
                style={{
                  flexShrink: 0, 
                  padding: "10px 20px", 
                  borderRadius: "10px",
                  border: "none",
                  background: isStreaming 
                    ? "rgba(248,113,113,0.15)" 
                    : "linear-gradient(135deg, #ffb95f 0%, #b17000 100%)",
                  color: isStreaming ? "#fca5a5" : "#472a00",
                  cursor: (!isStreaming && !input.trim()) ? "not-allowed" : "pointer",
                  opacity: (!isStreaming && !input.trim()) ? 0.4 : 1,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "0.75rem", 
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  transition: "all 0.2s",
                  fontFamily: "var(--font-syne), sans-serif",
                }}
                onMouseEnter={e => {
                  if (!isStreaming && input.trim()) {
                    (e.currentTarget as HTMLElement).style.transform = "scale(1.02)"
                  }
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.transform = "scale(1)"
                }}
              >
                {isStreaming ? "Stop" : "Send"}
              </button>
            </div>
            <p style={{ textAlign: "center", fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "10px", fontFamily: "var(--font-dm-mono), monospace", letterSpacing: "0.15em", textTransform: "uppercase" }}>
              AI-Powered • Press Enter to send
            </p>
          </div>
        </div>
      </div>

      {/* Upgrade Modal */}
      {upgradeModal.show && (
        <UpgradeModal
          onClose={() => setUpgradeModal({ show: false })}
          reason={upgradeModal.reason}
          upgradeMessage={upgradeModal.upgradeMessage}
        />
      )}
    </>
  )
}
