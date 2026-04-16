export interface Hotel {
  hotel_id: string
  name: string
  address?: string
  city?: string
  country?: string
  star_rating?: number
  star_name?: string
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
  // Unified search fields (v3.0)
  _sources?: string[]  // ['tuniu', 'rollinggo'] for merged, ['tuniu'] or ['rollinggo'] for single
  _match_confidence?: number  // Match confidence for merged hotels
  rollinggo_hotel_id?: string  // RollingGo hotel ID for merged hotels
  sort_rating?: number  // Effective rating for sorting (real or star-based estimate)
  sort_rating_source?: 'real' | 'estimated' | 'none'
  // Tuniu search fields
  hotel_id: string
  name: string
  address?: string
  city?: string
  country?: string
  star_rating?: number
  star_name?: string
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
  // Tuniu search fields
  business?: string
  brand_name?: string
  comment_digest?: string
  meal?: string
  refund?: string
  room_name?: string
  room_area?: string
  room_window?: string
  city_name?: string
}

export interface RoomPlan {
  room_id: string
  room_type_id?: string
  room_name: string
  bed_type?: string
  room_size?: string
  max_occupancy?: number
  floor?: string
  has_window?: string | boolean
  room_images?: string[]
  // Rate plan
  rate_plan_name?: string
  rate_plan_id?: string
  price?: number
  price_per_night?: number
  currency?: string
  breakfast?: string
  cancel_policy?: string
  available?: boolean
  amenities?: string[]
  pre_book_param?: string
  room_count?: number
}

export interface HotelDetail extends Hotel {
  room_plans?: RoomPlan[]
  brand?: string
  check_in_time?: string
  check_out_time?: string
  phone?: string
  hotel_name_en?: string
  policies?: {
    check_in_time?: string
    check_out_time?: string
    cancel_policy?: string
  }
  reviews?: {
    score?: number
    count?: number
  }
  supports_booking?: boolean
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
  // Unified search fields (v3.0)
  merged?: boolean
  sources?: {
    tuniu?: number
    rollinggo?: number
    merged_pairs?: number
  }
  warnings?: string[]
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

export interface Membership {
  tier: 'free' | 'basic' | 'premium'
  expires_at: string | null
  is_member: boolean
  search_remaining: number
  search_limit: number
}

export interface PaymentPlan {
  id: string
  name: string
  price: number
  currency: string
  days: number
  features: string[]
}

export interface SearchParams {
  provider?: string
  // Unified search (v3.0)
  destination?: string
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
