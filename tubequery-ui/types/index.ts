export interface Source {
  id: string
  title: string
  url: string
  source_type: string
  kb_id: string
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
  role: "user" | "assistant"
  content: string
  citations?: Citation[]
  isStreaming?: boolean
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
