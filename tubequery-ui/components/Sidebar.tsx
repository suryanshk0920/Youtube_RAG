"use client"
import { Database } from "lucide-react"
import clsx from "clsx"

const KBS = ["default", "health", "tech", "finance"]

interface Props {
  activeKb: string
  chunkCounts: Record<string, number>
  onKbChange: (kb: string) => void
}

export function Sidebar({ activeKb, chunkCounts, onKbChange }: Props) {
  return (
    <div className="flex flex-col h-full px-3 py-5">
      {/* Logo */}
      <div className="px-2 mb-6">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-500
            flex items-center justify-center text-sm font-bold text-white shadow-lg">
            T
          </div>
          <div>
            <p className="text-sm font-bold text-white">TubeQuery</p>
            <p className="text-xs text-white/40">YouTube RAG</p>
          </div>
        </div>
      </div>

      {/* KB list */}
      <p className="text-xs font-semibold text-white/30 uppercase tracking-wider px-2 mb-2">
        Knowledge Bases
      </p>
      <div className="space-y-1">
        {KBS.map((kb) => (
          <button
            key={kb}
            onClick={() => onKbChange(kb)}
            className={clsx(
              "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200",
              activeKb === kb
                ? "bg-violet-500/20 text-white border border-violet-500/30"
                : "text-white/50 hover:text-white/80 hover:bg-white/5"
            )}
          >
            <Database className={clsx("w-4 h-4", activeKb === kb ? "text-violet-400" : "text-white/30")} />
            <span className="flex-1 text-left capitalize">{kb}</span>
            {chunkCounts[kb] > 0 && (
              <span className="text-xs text-white/30 font-mono">
                {chunkCounts[kb].toLocaleString()}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}
