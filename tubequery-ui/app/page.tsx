"use client"
import { useCallback, useEffect, useState } from "react"
import { ChatPanel } from "@/components/ChatPanel"
import { IngestionPanel } from "@/components/IngestionPanel"
import { Sidebar } from "@/components/Sidebar"
import { getSources } from "@/lib/api"
import type { IntroData, Source } from "@/types"

export default function Home() {
  const [activeKb, setActiveKb] = useState("default")
  const [sources, setSources] = useState<Source[]>([])
  const [pendingIntro, setPendingIntro] = useState<IntroData | null>(null)
  const [chunkCounts, setChunkCounts] = useState<Record<string, number>>({})

  const loadSources = useCallback(async () => {
    try {
      const all = await getSources()
      setSources(all.filter((s) => s.kb_id === activeKb))

      // Compute chunk counts per KB
      const counts: Record<string, number> = {}
      for (const s of all) {
        counts[s.kb_id] = (counts[s.kb_id] ?? 0) + s.chunk_count
      }
      setChunkCounts(counts)
    } catch {
      // API not reachable yet
    }
  }, [activeKb])

  useEffect(() => {
    loadSources()
  }, [loadSources])

  function handleKbChange(kb: string) {
    setActiveKb(kb)
    setPendingIntro(null)
  }

  return (
    <div className="flex h-screen bg-[#0a0a0f] text-white overflow-hidden">
      {/* Sidebar */}
      <div className="w-52 flex-shrink-0 border-r border-white/5 bg-white/[0.02]">
        <Sidebar
          activeKb={activeKb}
          chunkCounts={chunkCounts}
          onKbChange={handleKbChange}
        />
      </div>

      {/* Chat */}
      <div className="flex-1 min-w-0">
        <ChatPanel
          activeKb={activeKb}
          pendingIntro={pendingIntro}
          onIntroDismiss={() => setPendingIntro(null)}
        />
      </div>

      {/* Ingestion panel */}
      <div className="w-72 flex-shrink-0 border-l border-white/5 bg-white/[0.02]">
        <IngestionPanel
          sources={sources}
          activeKb={activeKb}
          onSourcesChange={loadSources}
          onIntroReady={(intro) => {
            setPendingIntro(intro)
          }}
        />
      </div>
    </div>
  )
}
