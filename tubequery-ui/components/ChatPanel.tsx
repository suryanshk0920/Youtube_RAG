"use client"
import { useEffect, useRef, useState } from "react"
import { Send, Square } from "lucide-react"
import { streamChat } from "@/lib/api"
import { IntroCard } from "./IntroCard"
import { MessageBubble } from "./MessageBubble"
import { SuggestedQuestions } from "./SuggestedQuestions"
import type { Citation, IntroData, Message } from "@/types"

interface Props {
  activeKb: string
  pendingIntro: IntroData | null
  onIntroDismiss: () => void
}

export function ChatPanel({ activeKb, pendingIntro, onIntroDismiss }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll on new content
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = "auto"
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px"
  }, [input])

  async function sendMessage(question: string) {
    if (!question.trim() || isStreaming) return
    onIntroDismiss()

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question.trim(),
    }

    const assistantId = crypto.randomUUID()
    const assistantMsg: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      citations: [],
      isStreaming: true,
    }

    setMessages((prev) => [...prev, userMsg, assistantMsg])
    setInput("")
    setIsStreaming(true)

    const controller = new AbortController()
    abortRef.current = controller

    const history = messages.map((m) => ({
      ...m,
      id: m.id,
    }))

    await streamChat(
      question.trim(),
      activeKb,
      history,
      {
        onToken: (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + token }
                : m
            )
          )
        },
        onCitation: (citation: Citation) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, citations: [...(m.citations ?? []), citation] }
                : m
            )
          )
        },
        onDone: () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, isStreaming: false } : m
            )
          )
          setIsStreaming(false)
        },
        onError: (err) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: `Error: ${err}`, isStreaming: false }
                : m
            )
          )
          setIsStreaming(false)
        },
      },
      controller.signal
    )
  }

  function stopStream() {
    abortRef.current?.abort()
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m))
    )
    setIsStreaming(false)
  }

  const showSuggestions =
    pendingIntro && messages.length === 0 && pendingIntro.questions.length > 0

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-1">
        {/* Intro card */}
        {pendingIntro && messages.length === 0 && (
          <IntroCard
            intro={pendingIntro}
            onQuestionSelect={(q) => sendMessage(q)}
          />
        )}

        {/* Empty state */}
        {!pendingIntro && messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-20">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-500
              flex items-center justify-center text-2xl font-bold text-white mb-4 shadow-xl">
              T
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">TubeQuery</h2>
            <p className="text-white/40 text-sm max-w-xs">
              Ingest a YouTube video on the right, then ask anything about it.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        <div ref={bottomRef} />
      </div>

      {/* Suggested questions */}
      {showSuggestions && (
        <div className="px-6 pb-3">
          <SuggestedQuestions
            questions={pendingIntro.questions}
            onSelect={(q) => sendMessage(q)}
          />
        </div>
      )}

      {/* Input */}
      <div className="px-6 pb-6 pt-2">
        <div className="flex items-end gap-3 p-3 rounded-2xl
          bg-white/5 border border-white/10
          focus-within:border-violet-500/40 focus-within:bg-white/8
          transition-all duration-200">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                sendMessage(input)
              }
            }}
            placeholder="Ask anything about your videos..."
            rows={1}
            className="flex-1 bg-transparent text-sm text-white placeholder-white/30
              resize-none focus:outline-none leading-relaxed"
          />
          <button
            onClick={isStreaming ? stopStream : () => sendMessage(input)}
            disabled={!isStreaming && !input.trim()}
            className="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center
              bg-gradient-to-br from-violet-600 to-indigo-600 text-white
              hover:from-violet-500 hover:to-indigo-500
              disabled:opacity-30 disabled:cursor-not-allowed
              transition-all duration-200 shadow-lg shadow-violet-500/25"
          >
            {isStreaming
              ? <Square className="w-3.5 h-3.5 fill-current" />
              : <Send className="w-3.5 h-3.5" />
            }
          </button>
        </div>
        <p className="text-center text-xs text-white/20 mt-2">
          Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
