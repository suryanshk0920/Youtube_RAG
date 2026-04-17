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
      setSources(all.filter(s => s.kb_id === activeKb))
      const counts: Record<string, number> = {}
      for (const s of all) counts[s.kb_id] = (counts[s.kb_id] ?? 0) + s.chunk_count
      setChunkCounts(counts)
    } catch { /* API not ready */ }
  }, [activeKb])

  useEffect(() => { loadSources() }, [loadSources])

  return (
    <div style={{ display: "flex", height: "100vh", background: "var(--bg-base)", overflow: "hidden" }}>
      {/* Sidebar */}
      <div style={{ width: "200px", flexShrink: 0, borderRight: "1px solid var(--border)", background: "var(--bg-surface)" }}>
        <Sidebar
          activeKb={activeKb}
          chunkCounts={chunkCounts}
          onKbChange={kb => { setActiveKb(kb); setPendingIntro(null) }}
        />
      </div>

      {/* Chat — main area */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <ChatPanel
          activeKb={activeKb}
          pendingIntro={pendingIntro}
          onIntroDismiss={() => setPendingIntro(null)}
        />
      </div>

      {/* Right panel — ingestion */}
      <div style={{ width: "280px", flexShrink: 0, borderLeft: "1px solid var(--border)", background: "var(--bg-surface)" }}>
        <IngestionPanel
          sources={sources}
          activeKb={activeKb}
          onSourcesChange={loadSources}
          onIntroReady={intro => setPendingIntro(intro)}
        />
      </div>
    </div>
  )
}
