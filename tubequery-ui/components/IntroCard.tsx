"use client"
import { BookOpen, ChevronRight } from "lucide-react"
import type { IntroData } from "@/types"

interface Props {
  intro: IntroData
  onQuestionSelect: (q: string) => void
}

export function IntroCard({ intro, onQuestionSelect }: Props) {
  return (
    <div className="rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-500/10 to-indigo-500/5 p-5 mb-6">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-indigo-500
          flex items-center justify-center text-xs font-bold text-white">
          T
        </div>
        <span className="text-sm font-semibold text-white/80">Video Summary</span>
      </div>

      {/* Overview */}
      <p className="text-sm text-white/75 leading-relaxed mb-4">{intro.intro}</p>

      {/* Topics */}
      {intro.topics.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">
            Topics covered
          </p>
          <ul className="space-y-1">
            {intro.topics.map((t, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-white/70">
                <ChevronRight className="w-3.5 h-3.5 text-violet-400 flex-shrink-0 mt-0.5" />
                {t}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggested questions */}
      {intro.questions.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">
            Ask something
          </p>
          <div className="flex flex-col gap-2">
            {intro.questions.map((q, i) => (
              <button
                key={i}
                onClick={() => onQuestionSelect(q)}
                className="text-left px-3 py-2 rounded-xl text-sm text-white/70
                  bg-white/5 border border-white/10
                  hover:bg-violet-500/20 hover:border-violet-500/40 hover:text-white
                  transition-all duration-200"
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
