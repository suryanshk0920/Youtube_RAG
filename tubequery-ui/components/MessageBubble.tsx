"use client"
import ReactMarkdown from "react-markdown"
import { CitationChip } from "./CitationChip"
import type { Message } from "@/types"

function TypingCursor() {
  return (
    <span className="inline-block w-0.5 h-4 bg-violet-400 ml-0.5 animate-pulse align-middle" />
  )
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user"

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[75%] px-4 py-3 rounded-2xl rounded-tr-sm
          bg-gradient-to-br from-violet-600 to-indigo-600
          text-white text-sm leading-relaxed shadow-lg">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3 mb-6">
      {/* Avatar */}
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-indigo-500
        flex items-center justify-center text-xs font-bold text-white shadow-md mt-1">
        T
      </div>

      <div className="flex-1 min-w-0">
        {/* Answer text */}
        <div className="prose prose-invert prose-sm max-w-none
          text-white/90 leading-relaxed
          prose-p:my-2 prose-ul:my-2 prose-li:my-0.5
          prose-strong:text-white prose-strong:font-semibold
          prose-headings:text-white prose-headings:font-semibold">
          <ReactMarkdown>{message.content}</ReactMarkdown>
          {message.isStreaming && <TypingCursor />}
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {message.citations.map((c, i) => (
              <CitationChip key={i} citation={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
