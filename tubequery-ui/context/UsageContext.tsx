"use client"

import { createContext, useContext, useCallback, useState, useEffect } from "react"
import type { UserLimitsSummary } from "@/lib/api"

interface UsageContextType {
  refreshUsage: () => void
  refreshTrigger: number
  cachedLimits: UserLimitsSummary | null
  setCachedLimits: (limits: UserLimitsSummary | null) => void
}

const UsageContext = createContext<UsageContextType | null>(null)

const STORAGE_KEY = "tubequery_limits_cache"

function loadCachedLimits(): UserLimitsSummary | null {
  if (typeof window === "undefined") return null
  
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY)
    if (stored) {
      const data = JSON.parse(stored)
      // Check if cache is less than 5 minutes old
      if (data.timestamp && Date.now() - data.timestamp < 5 * 60 * 1000) {
        return data.limits
      }
    }
  } catch (e) {
    console.warn("Failed to load cached limits:", e)
  }
  
  return null
}

function saveCachedLimits(limits: UserLimitsSummary | null) {
  if (typeof window === "undefined" || !limits) return
  
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
      limits,
      timestamp: Date.now()
    }))
  } catch (e) {
    console.warn("Failed to save cached limits:", e)
  }
}

export function UsageProvider({ children }: { children: React.ReactNode }) {
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [cachedLimits, setCachedLimitsState] = useState<UserLimitsSummary | null>(null)
  
  // Load cached limits on mount
  useEffect(() => {
    const cached = loadCachedLimits()
    if (cached) {
      setCachedLimitsState(cached)
    }
  }, [])
  
  const refreshUsage = useCallback(() => {
    setRefreshTrigger(prev => prev + 1)
  }, [])
  
  const setCachedLimits = useCallback((limits: UserLimitsSummary | null) => {
    setCachedLimitsState(limits)
    saveCachedLimits(limits)
  }, [])
  
  return (
    <UsageContext.Provider value={{ refreshUsage, refreshTrigger, cachedLimits, setCachedLimits }}>
      {children}
    </UsageContext.Provider>
  )
}

export function useUsage() {
  const context = useContext(UsageContext)
  if (!context) {
    throw new Error('useUsage must be used within a UsageProvider')
  }
  return context
}