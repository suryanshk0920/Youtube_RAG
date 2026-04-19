export interface Source {
  id: string
  title: string
  url: string
  source_type: string
  kb_id: string
  kb_name?: string
  status: string
  video_count: number
  chunk_count: number
  created_at: string
}

export interface Citation {
  video_title: string
  video_id: string
  timestamp_label: string
  youtube_url: string
  excerpt: string
}

export interface Message {
  id: string
  role: "user" | "assistant" | "summary"
  content: string
  citations?: Citation[]
  isStreaming?: boolean
  summaryData?: IntroData  // For summary messages
}

export interface IntroData {
  source_id: string
  source_title: string
  intro: string
  topics: string[]
  questions: string[]
}

export interface ChatSession {
  sourceId: string
  sourceTitle: string
  kbId: string
  messages: Message[]
  createdAt: string
  dbId?: string  // Supabase UUID — undefined for local-only sessions
}

export interface IngestResponse {
  source_id: string
  title: string
  kb_id: string
  video_count: number
  chunk_count: number
  status: string
}

// Subscription types
export interface PlanLimits {
  videos_per_day: number
  questions_per_day: number
  history_retention_days: number
  max_concurrent_videos: number
  advanced_features: boolean
  priority_processing: boolean
  export_enabled: boolean
}

export interface UserSubscription {
  id: string
  user_id: string
  plan_type: "free" | "pro" | "enterprise"
  status: "active" | "cancelled" | "expired" | "past_due"
  stripe_customer_id?: string
  stripe_subscription_id?: string
  current_period_start?: string
  current_period_end?: string
  created_at: string
  updated_at: string
}
