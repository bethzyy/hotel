<template>
  <div class="container py-4">
    <!-- Search Limit Banner -->
    <SearchLimit />

    <!-- Search Info Header -->
    <div v-if="searchInfo" class="search-info mb-4">
      <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
        <div>
          <h5 class="mb-1">
            <i class="bi bi-geo-alt text-primary me-2"></i>
            {{ searchInfo.place }}
            <small class="text-muted ms-2">{{ searchInfo.dateRange }}</small>
          </h5>
          <span class="badge bg-light text-dark">
            {{ hotels.length }} 个结果
            <span v-if="searchInfo.sourceLabel" class="ms-1">· {{ searchInfo.sourceLabel }}</span>
          </span>
        </div>
        <div class="btn-group">
          <button class="btn btn-sm" :class="{ active: sortBy === 'default' }" @click="sortBy = 'default'">默认</button>
          <button class="btn btn-sm" :class="{ active: sortBy === 'price' }" @click="sortBy = 'price'">价格</button>
          <button class="btn btn-sm" :class="{ active: sortBy === 'rating' }" @click="sortBy = 'rating'">评分</button>
        </div>
      </div>
    </div>

    <!-- Source breakdown for merged results -->
    <div v-if="sourceBreakdown" class="alert alert-light d-flex align-items-center mb-3 py-2" role="status">
      <i class="bi bi-diagram-3 me-2 text-primary"></i>
      <small>
        搜索结果来源：
        <span v-if="sourceBreakdown.tuniu" class="badge bg-primary me-1">途牛 {{ sourceBreakdown.tuniu }}家</span>
        <span v-if="sourceBreakdown.rollinggo" class="badge bg-success me-1">全球搜索 {{ sourceBreakdown.rollinggo }}家</span>
        <span v-if="sourceBreakdown.merged_pairs" class="badge bg-info">融合匹配 {{ sourceBreakdown.merged_pairs }}对</span>
      </small>
    </div>

    <!-- Loading -->
    <div v-if="pending" class="d-flex flex-column gap-3">
      <SkeletonCard v-for="i in 5" :key="i" />
    </div>

    <!-- Fallback notice (independent, always shows when applicable) -->
    <div v-if="fallbackFrom && hotels.length > 0" class="alert alert-info d-flex align-items-center mb-3" role="alert">
      <i class="bi bi-info-circle me-2"></i>
      已按距"<strong>{{ fallbackFrom }}</strong>"的实际距离排序（通过坐标计算）
    </div>

    <!-- Empty -->
    <EmptyState v-if="!pending && hotels.length === 0" />

    <!-- Hotel Cards -->
    <div v-if="hotels.length > 0" class="d-flex flex-column gap-3">
      <HotelCard
        v-for="(hotel, idx) in sortedHotels"
        :key="hotel.hotel_id || hotel.rollinggo_hotel_id || idx"
        :hotel="hotel"
        :index="idx"
        :check-in="resolvedCheckIn"
        :check-out="resolvedCheckOut"
      />
    </div>

    <!-- Load More (only for non-merged results with pagination) -->
    <div v-if="hasMore && !pending && !isMerged" class="text-center mt-4">
      <button class="btn btn-outline-primary" @click="loadMore" :disabled="loadingMore">
        <span v-if="loadingMore" class="spinner-border spinner-border-sm me-2"></span>
        加载更多
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Hotel, SearchResult } from '~/types/api'

const route = useRoute()
const sortBy = ref('default')
const loadingMore = ref(false)
const hasMore = ref(false)
const pending = ref(true)
const isMerged = ref(false)
const sourceBreakdown = ref<{ tuniu?: number; rollinggo?: number; merged_pairs?: number } | null>(null)

// Resolve check-in/check-out dates
const resolvedCheckIn = computed(() => {
  return (route.query.check_in || route.query.check_in_date || '') as string
})
const resolvedCheckOut = computed(() => {
  const checkOut = route.query.check_out as string
  if (checkOut) return checkOut
  // Calculate from check_in + stay_nights
  const checkIn = (route.query.check_in_date || route.query.check_in) as string
  const nights = Number(route.query.stay_nights) || 1
  if (checkIn) {
    const d = new Date(checkIn)
    d.setDate(d.getDate() + nights)
    return d.toISOString().split('T')[0]
  }
  return ''
})

const hotels = ref<Hotel[]>([])
const searchInfo = ref<{ place: string; dateRange: string; sourceLabel: string } | null>(null)
const fallbackFrom = ref('')

const sortedHotels = computed(() => {
  const list = [...hotels.value]
  if (sortBy.value === 'price') {
    list.sort((a, b) => (a.price_per_night || Infinity) - (b.price_per_night || Infinity))
  } else if (sortBy.value === 'rating') {
    list.sort((a, b) => (b.rating || 0) - (a.rating || 0))
  }
  return list
})

function getSourceLabel(data: SearchResult): string {
  if (data.merged) return '双源融合'
  if (data.provider === 'tuniu') return '国内酒店'
  if (data.provider === 'rollinggo') return '全球搜索'
  if (data.provider === 'auto') return '智能搜索'
  return ''
}

async function search() {
  pending.value = true
  const { post } = useApi()
  try {
    const q = { ...route.query }
    const data = await post<SearchResult>('/search', q)
    hotels.value = data.hotels || []
    hasMore.value = !!data.has_more
    isMerged.value = !!data.merged
    fallbackFrom.value = (data as any).fallback_from || ''

    // Source breakdown for merged results
    if (data.merged && data.sources) {
      sourceBreakdown.value = data.sources
    } else {
      sourceBreakdown.value = null
    }

    const checkIn = (route.query.check_in || route.query.check_in_date) as string
    const checkOut = (route.query.check_out || '') as string
    const place = (route.query.destination || route.query.city_name || route.query.place) as string
    searchInfo.value = {
      place: place || '',
      dateRange: checkIn && checkOut ? `${checkIn} ~ ${checkOut}` : '',
      sourceLabel: getSourceLabel(data),
    }

    useSeoMeta({
      title: `${place}酒店搜索结果 - ${hotels.value.length}家酒店`,
      description: `搜索${place}酒店，共找到${hotels.value.length}家酒店，对比价格找到最优惠的。`,
    })

    // Track search event
    const tracking = useTracking()
    tracking.trackSearch({
      provider: (data.provider as string) || undefined,
      place: place || undefined,
      checkIn: checkIn || undefined,
      checkOut: checkOut || undefined,
      resultCount: hotels.value.length,
    })
  } catch (e: any) {
    hotels.value = []
  } finally {
    pending.value = false
  }
}

async function loadMore() {
  loadingMore.value = true
  const { post } = useApi()
  try {
    const q = { ...route.query, page_num: String(hotels.value.length / 20 + 1) }
    const data = await post<SearchResult>('/search', q)
    hotels.value.push(...(data.hotels || []))
    hasMore.value = !!data.has_more
  } catch { /* ignore */ } finally {
    loadingMore.value = false
  }
}

watch(() => route.query, search, { immediate: true })
</script>
