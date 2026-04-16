"use client"

interface Props {
  questions: string[]
  onSelect: (q: string) => void
}

export function SuggestedQuestions({ questions, onSelect }: Props) {
  if (!questions.length) return null

  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
      {questions.map((q, i) => (
        <button
          key={i}
          onClick={() => onSelect(q)}
          className="flex-shrink-0 px-4 py-2 rounded-xl text-sm
            bg-white/5 border border-white/10 text-white/70
            hover:bg-violet-500/20 hover:border-violet-500/40 hover:text-white
            transition-all duration-200 text-left max-w-[220px] truncate"
        >
          💬 {q}
        </button>
      ))}
    </div>
  )
}
