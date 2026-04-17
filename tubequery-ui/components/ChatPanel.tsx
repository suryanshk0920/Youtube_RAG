"use client"
import { useEffect, useRef, useState } from "react"
import { streamChat } from "@/lib/api"
import { IntroCard } from "./IntroCard"
import { MessageBubble } from "./MessageBubble"
import type { Citation, IntroData, Message } from "@/types"

interface Props {
  activeKb: string
  activeSourceId: string | null
  pendingIntro: IntroData | null
  onIntroDismiss: () => void
  messages: Message[]
  onMessagesChange: (messages: Message[]) => void
}

export function ChatPanel({ activeKb, activeSourceId, pendingIntro, onIntroDismiss: _, messages, onMessagesChange }: Props) {
  const [input, setInput] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
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

    await streamChat(
      question.trim(), activeKb, history,
      {
        onToken: token => {
          const latest = messagesRef.current
          onMessagesChange(latest.map(m =>
            m.id === assistantId ? { ...m, content: m.content + token } : m
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
          const latest = messagesRef.current
          // Strip SOURCES block from the complete answer before saving
          const stripSources = (text: string) =>
            text.replace(/\n*SOURCES:\s*\n(?:[\s\S]*?)(?=\n\n|$)/i, "").trim()
          onMessagesChange(latest.map(m =>
            m.id === assistantId
              ? { ...m, isStreaming: false, citations: [...collectedCitations], content: stripSources(m.content) }
              : m
          ))
          setIsStreaming(false)
        },
        onError: err => {
          const latest = messagesRef.current
          onMessagesChange(latest.map(m =>
            m.id === assistantId ? { ...m, content: `Error: ${err}`, isStreaming: false } : m
          ))
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
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Messages area */}
      <div style={{ flex: 1, overflowY: "auto", padding: "20px 0 16px" }}>
        <div style={{ maxWidth: "780px", margin: "0 auto", padding: "0 16px" }}>

          {pendingIntro && (
            <IntroCard intro={pendingIntro} onQuestionSelect={q => sendMessage(q)} />
          )}

          {!pendingIntro && messages.length === 0 && (
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
                Ingest a YouTube video on the right, then ask anything about its content.
              </p>
            </div>
          )}

          {messages.map(msg => <MessageBubble key={msg.id} message={msg} />)}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div style={{ padding: "12px 0 24px" }}>
        <div style={{ maxWidth: "780px", margin: "0 auto", padding: "0 16px" }}>
          <div
            style={{
              display: "flex", alignItems: "flex-end", gap: "10px",
              padding: "12px 14px", borderRadius: "14px",
              border: "1px solid var(--border)", background: "var(--bg-elevated)",
              transition: "border-color 0.18s, box-shadow 0.18s",
            }}
            onFocusCapture={e => {
              const el = e.currentTarget as HTMLElement
              el.style.borderColor = "rgba(245,158,11,0.3)"
              el.style.boxShadow = "0 0 0 3px rgba(245,158,11,0.05)"
            }}
            onBlurCapture={e => {
              const el = e.currentTarget as HTMLElement
              el.style.borderColor = "var(--border)"
              el.style.boxShadow = "none"
            }}
          >
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input) } }}
              placeholder="Ask anything about your videos…"
              rows={1}
              style={{
                flex: 1, background: "transparent", border: "none", outline: "none",
                resize: "none", fontSize: "0.975rem", color: "var(--text-primary)",
                fontFamily: "var(--font-dm-sans), sans-serif", lineHeight: 1.6,
              }}
            />
            <button
              onClick={isStreaming ? stopStream : () => sendMessage(input)}
              disabled={!isStreaming && !input.trim()}
              style={{
                flexShrink: 0, width: "32px", height: "32px", borderRadius: "9px",
                border: "1px solid var(--border-warm)",
                background: isStreaming ? "rgba(248,113,113,0.1)" : "var(--amber-dim)",
                color: isStreaming ? "#fca5a5" : "var(--amber)",
                cursor: (!isStreaming && !input.trim()) ? "not-allowed" : "pointer",
                opacity: (!isStreaming && !input.trim()) ? 0.3 : 1,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "0.85rem", transition: "all 0.18s",
              }}
            >
              {isStreaming ? "■" : "↑"}
            </button>
          </div>
          <p style={{ textAlign: "center", fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "8px", fontFamily: "var(--font-dm-mono), monospace" }}>
            enter to send · shift+enter for newline
          </p>
        </div>
      </div>
    </div>
  )
}
