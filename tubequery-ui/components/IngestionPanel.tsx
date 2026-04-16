"use client"
import { useState } from "react"
import { Plus, Trash2, Video, Loader2, ChevronDown } from "lucide-react"
import { deleteSource, getIntro, ingestUrl } from "@/lib/api"
import type { IntroData, Source } from "@/types"

interface Props {
  sources: Source[]
  activeKb: string
  onSourcesChange: () => void
  onIntroReady: (intro: IntroData) => void
}

export function IngestionPanel({ sources, activeKb, onSourcesChange, onIntroReady }: Props) {
  const [url, setUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<{ type: "success" | "error"; msg: string } | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)

  async function handleIngest() {
    if (!url.trim()) return
    setLoading(true)
    setStatus(null)
    try {
      const result = await ingestUrl(url.trim(), activeKb)
      setStatus({ type: "success", msg: `✓ ${result.chunk_count} chunks indexed` })
      setUrl("")
      onSourcesChange()
      // Auto-generate intro
      const intro = await getIntro(result.source_id)
      onIntroReady(intro)
    } catch (e: unknown) {
      setStatus({ type: "error", msg: e instanceof Error ? e.message : "Ingestion failed" })
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(source: Source) {
    try {
      await deleteSource(source.id, source.kb_id)
      onSourcesChange()
    } catch {
      // silent
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-5 pt-5 pb-4 border-b border-white/5">
        <h2 className="text-sm font-semibold text-white/80">Add Content</h2>
        <p className="text-xs text-white/40 mt-0.5">Paste a YouTube URL to ingest</p>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        {/* URL input */}
        <div className="space-y-2">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleIngest()}
            placeholder="https://youtube.com/watch?v=..."
            className="w-full px-3 py-2.5 rounded-xl text-sm
              bg-white/5 border border-white/10 text-white placeholder-white/30
              focus:outline-none focus:border-violet-500/50 focus:bg-white/8
              transition-all duration-200"
          />
          <button
            onClick={handleIngest}
            disabled={loading || !url.trim()}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium
              bg-gradient-to-r from-violet-600 to-indigo-600 text-white
              hover:from-violet-500 hover:to-indigo-500
              disabled:opacity-40 disabled:cursor-not-allowed
              transition-all duration-200 shadow-lg shadow-violet-500/20"
          >
            {loading ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Ingesting...</>
            ) : (
              <><Plus className="w-4 h-4" /> Ingest</>
            )}
          </button>

          {status && (
            <p className={`text-xs px-3 py-2 rounded-lg ${
              status.type === "success"
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : "bg-red-500/10 text-red-400 border border-red-500/20"
            }`}>
              {status.msg}
            </p>
          )}
        </div>

        {/* Sources list */}
        {sources.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-2">
              Ingested · {sources.length}
            </p>
            <div className="space-y-2">
              {sources.map((s) => (
                <div key={s.id} className="rounded-xl border border-white/8 bg-white/3 overflow-hidden">
                  <button
                    onClick={() => setExpanded(expanded === s.id ? null : s.id)}
                    className="w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-white/5 transition-colors"
                  >
                    <Video className="w-4 h-4 text-violet-400 flex-shrink-0" />
                    <span className="flex-1 text-sm text-white/80 truncate">{s.title}</span>
                    <ChevronDown className={`w-3.5 h-3.5 text-white/30 transition-transform ${expanded === s.id ? "rotate-180" : ""}`} />
                  </button>

                  {expanded === s.id && (
                    <div className="px-3 pb-3 border-t border-white/5 pt-2 space-y-2">
                      <div className="flex gap-3 text-xs text-white/50">
                        <span>{s.video_count} video{s.video_count !== 1 ? "s" : ""}</span>
                        <span>·</span>
                        <span>{s.chunk_count} chunks</span>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={async () => {
                            const intro = await getIntro(s.id)
                            onIntroReady(intro)
                          }}
                          className="flex-1 py-1.5 rounded-lg text-xs font-medium
                            bg-violet-500/15 text-violet-300 border border-violet-500/20
                            hover:bg-violet-500/25 transition-colors"
                        >
                          ✨ Summary
                        </button>
                        <button
                          onClick={() => handleDelete(s)}
                          className="p-1.5 rounded-lg text-xs
                            bg-red-500/10 text-red-400 border border-red-500/20
                            hover:bg-red-500/20 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {sources.length === 0 && !loading && (
          <div className="text-center py-8 text-white/25 text-sm">
            <Video className="w-8 h-8 mx-auto mb-2 opacity-30" />
            No videos yet
          </div>
        )}
      </div>
    </div>
  )
}
