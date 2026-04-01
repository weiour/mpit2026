export type AuthMode = 'login' | 'register'

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: number
  email: string
  name: string
  role: string
  region?: string | null
}

export interface EventItem {
  id: number
  title: string
  event_date: string | null
  budget: number | null
  guests_count: number | null
  format: string | null
  notes: string | null
  city?: string | null
  status?: string | null
  venue_mode?: string | null
  selected_option?: string | null
  selected_option_kind?: string | null
  owner_id: number
  google_calendar_link?: string | null
  google_calendar_error?: string | null
  guest_emails?: string[] | null
  google_invite_link?: string | null
}

export type ChatActionKind = 'send_prompt' | 'open_tab'

export interface ChatAction {
  id: string
  label: string
  kind: ChatActionKind
  prompt?: string | null
  target_tab?: string | null
}

export interface ChatMessage {
  id: number
  event_id: number
  role: 'system' | 'user' | 'assistant'
  content: string
  created_at: string | null
  actions: ChatAction[]
}

export interface ChatResponse {
  user_message: ChatMessage
  assistant_message: ChatMessage
}

export interface VenueRecommendation {
  id: string
  name: string
  address: string | null
  rating: number | null
  review_count: number | null
  price_note: string | null
  source_query: string | null
  reason: string
  source: string
  tags: string[]
  yandex_maps_url: string | null
  two_gis_url: string | null
}

export interface RecommendationMeta {
  city: string | null
  provider: string
  generated_summary: string
  search_queries: string[]
  missing_fields: string[]
  warnings: string[]
}

export interface RecommendationsResponse {
  items: VenueRecommendation[]
  meta: RecommendationMeta
}
