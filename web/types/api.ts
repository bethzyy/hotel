export interface Hotel {
  hotel_id: string
  name: string
  address?: string
  city?: string
  country?: string
  star_rating?: number
  rating?: number
  review_count?: number
  price_per_night?: number
  currency?: string
  image_url?: string
  images?: string[]
  tags?: string[]
  amenities?: string[]
  description?: string
  latitude?: number
  longitude?: number
  booking_url?: string
  provider: string
  is_favorite?: boolean
  distance?: number
  distance_meters?: number
}

export interface RoomPlan {
  room_id: string
  room_name: string
  bed_type?: string
  room_size?: string
  max_occupancy?: number
  price?: number
  price_per_night?: number
  currency?: string
  available?: boolean
  breakfast?: string
  cancel_policy?: string
  amenities?: string[]
  pre_book_param?: string
}

export interface HotelDetail extends Hotel {
  room_plans?: RoomPlan[]
  brand?: string
  check_in_time?: string
  check_out_time?: string
  phone?: string
}

export interface ComparisonSource {
  provider: string
  hotel_id: string
  name: string
  address?: string
  price?: number
  currency?: string
  url?: string
  supports_booking?: boolean
}

export interface ComparisonResult {
  provider: string
  hotel_id: string
  name?: string
  address?: string
  price?: number
  currency?: string
  price_cny?: number
  url?: string
  match_confidence?: number
  name_similarity?: number
  location_match?: boolean
  distance_meters?: number
}

export interface ExternalPrice {
  platform_name: string
  platform_key?: string
  price?: number
  currency?: string
  price_cny?: number
  url?: string
}

export interface BestPrice {
  provider: string
  price: number
  currency: string
  url?: string
  save?: number | null
}

export interface ComparisonData {
  source: ComparisonSource
  comparisons: ComparisonResult[]
  external_prices: ExternalPrice[]
  best_price: BestPrice | null
}

export interface SearchResult {
  hotels: Hotel[]
  total: number
  provider: string
  supports_booking: boolean
  supports_pagination?: boolean
  query_id?: string
  page_num?: number
  has_more?: boolean
  query?: string
  place?: string
}

export interface Favorite {
  id: number
  hotel_id: string
  provider: string
  hotel_name: string
  hotel_data?: string
  created_at: string
}

export interface SearchHistoryItem {
  id: number
  query: string
  place: string
  place_type?: string
  provider?: string
  created_at: string
}

export interface User {
  id: number
  phone: string
  nickname?: string
  avatar_url?: string
  created_at: string
}

export interface Provider {
  id: string
  name: string
  supports_booking?: boolean
  description?: string
}

export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: string
  message?: string
  cached?: boolean
}

export interface SearchParams {
  provider?: string
  // RollingGo params
  query?: string
  place?: string
  place_type?: string
  check_in_date?: string
  stay_nights?: number
  size?: number
  // Tuniu params
  city_name?: string
  check_in?: string
  check_out?: string
  // Common
  adult_count?: number
  child_count?: number
  child_ages?: number[]
  keyword?: string
  page_num?: number
  query_id?: string
}
