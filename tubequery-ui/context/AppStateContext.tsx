"use client"

import { createContext, useContext, useCallback, useState, useEffect, ReactNode } from "react"
import type { ChatSession, Source } from "@/types"

interface AppState {
  sessions: Record<string, ChatSession>
  sources: Source[]
  activeKb: string
  activeSourceId: string | null
  chunkCounts: Record<string, number>
  lastFetched: number
}

interface AppStateContextType {
  state: AppState
  updateSessions: (sessions: Record<string, ChatSession>) => void
  updateSources: (sources: Source[]) => void
  updateActiveKb: (kb: string) => void
  updateActiveSourceId: (id: string | null) => void
  updateChunkCounts: (counts: Record<string, number>) => void
  updateLastFetched: (time: number) => void
}

const AppStateContext = createContext<AppStateContextType | null>(null)

const STORAGE_KEY = "tubequery_app_state"

function loadState(): AppState {
  if (typeof window === "undefined") {
    return {
      sessions: {},
      sources: [],
      activeKb: "default",
      activeSourceId: null,
      chunkCounts: {},
      lastFetched: 0,
    }
  }

  try {
    const stored = sessionStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.warn("Failed to load app state:", e)
  }

  return {
    sessions: {},
    sources: [],
    activeKb: "default",
    activeSourceId: null,
    chunkCounts: {},
    lastFetched: 0,
  }
}

function saveState(state: AppState) {
  if (typeof window === "undefined") return
  
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (e) {
    console.warn("Failed to save app state:", e)
  }
}

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(loadState)

  // Save to sessionStorage whenever state changes
  useEffect(() => {
    saveState(state)
  }, [state])

  const updateSessions = useCallback((sessions: Record<string, ChatSession>) => {
    setState(prev => ({ ...prev, sessions }))
  }, [])

  const updateSources = useCallback((sources: Source[]) => {
    setState(prev => ({ ...prev, sources }))
  }, [])

  const updateActiveKb = useCallback((activeKb: string) => {
    setState(prev => ({ ...prev, activeKb }))
  }, [])

  const updateActiveSourceId = useCallback((activeSourceId: string | null) => {
    setState(prev => ({ ...prev, activeSourceId }))
  }, [])

  const updateChunkCounts = useCallback((chunkCounts: Record<string, number>) => {
    setState(prev => ({ ...prev, chunkCounts }))
  }, [])

  const updateLastFetched = useCallback((lastFetched: number) => {
    setState(prev => ({ ...prev, lastFetched }))
  }, [])

  return (
    <AppStateContext.Provider
      value={{
        state,
        updateSessions,
        updateSources,
        updateActiveKb,
        updateActiveSourceId,
        updateChunkCounts,
        updateLastFetched,
      }}
    >
      {children}
    </AppStateContext.Provider>
  )
}

export function useAppState() {
  const context = useContext(AppStateContext)
  if (!context) {
    throw new Error("useAppState must be used within AppStateProvider")
  }
  return context
}
