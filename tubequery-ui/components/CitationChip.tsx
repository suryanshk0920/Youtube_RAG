"use client"
import { Play } from "lucide-react"
import type { Citation } from "@/types"

export function CitationChip({ citation }: { citation: Citation }) {
  return (
    <a
      href={citation.youtube_url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium
        bg-white/5 border border-white/10 text-white/70
        hover:bg-violet-500/20 hover:border-violet-500/40 hover:text-white
        transition-all duration-200 group"
    >
      <Play className="w-3 h-3 fill-current text-violet-400 group-hover:text-violet-300" />
      <span>{citation.video_title.length > 30
        ? citation.video_title.slice(0, 30) + "…"
        : citation.video_title}
      </span>
      <span className="text-violet-400 group-hover:text-violet-300 font-mono">
        {citation.timestamp_label}
      </span>
    </a>
  )
}
