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
            <span v-if="searchInfo.provider" class="ms-1">· {{ searchInfo.provider }}</span>
          </span>
        </div>
        <div class="btn-group">
          <button class="btn btn-sm" :class="{ active: sortBy === 'default' }" @click="sortBy = 'default'">默认</button>
          <button class="btn btn-sm" :class="{ active: sortBy === 'price' }" @click="sortBy = 'price'">价格</button>
          <button class="btn btn-sm" :class="{ active: sortBy === 'rating' }" @click="sortBy = 'rating'">评分</button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="pending" class="d-flex flex-column gap-3">
      <SkeletonCard v-for="i in 5" :key="i" />
    </div>

    <!-- Empty -->
    <EmptyState v-else-if="hotels.length === 0" />

    <!-- Hotel Cards -->
    <div v-else class="d-flex flex-column gap-3">
      <HotelCard
        v-for="(hotel, idx) in sortedHotels"
        :key="hotel.hotel_id"
        :hotel="hotel"
        :index="idx"
        :check-in="route.query.check_in as string"
        :check-out="route.query.check_out as string"
      />
    </div>

    <!-- Load More -->
    <div v-if="hasMore && !pending" class="text-center mt-4">
      <button class="btn btn-outline-primary" @click="loadMore" :disabled="loadingMore">
        <span v-if="loadingMore" class="spinner-border spinner-border-sm me-2"></span>
        加载更多
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Hotel } from '~/types/api'

const route = useRoute()
const sortBy = ref('default')
const loadingMore = ref(false)
const hasMore = ref(false)
const pending = ref(true)

const hotels = ref<Hotel[]>([])
const searchInfo = ref<{ place: string; dateRange: string; provider: string } | null>(null)

const sortedHotels = computed(() => {
  const list = [...hotels.value]
  if (sortBy.value === 'price') {
    list.sort((a, b) => (a.price_per_night || Infinity) - (b.price_per_night || Infinity))
  } else if (sortBy.value === 'rating') {
    list.sort((a, b) => (b.rating || 0) - (a.rating || 0))
  }
  return list
})

async function search() {
  pending.value = true
  const { post } = useApi()
  try {
    const q = { ...route.query }
    const data = await post<Hotel[]>('/search', q)
    hotels.value = data.hotels || []
    hasMore.value = !!data.has_more

    const checkIn = (route.query.check_in || route.query.check_in_date) as string
    const checkOut = (route.query.check_out || '') as string
    const place = (route.query.city_name || route.query.place) as string
    const provider = (route.query.provider) as string
    searchInfo.value = {
      place: place || '',
      dateRange: checkIn && checkOut ? `${checkIn} ~ ${checkOut}` : '',
      provider: provider === 'rollinggo' ? '全球酒店' : provider === 'tuniu' ? '国内酒店' : '',
    }

    useSeoMeta({
      title: `${place}酒店搜索结果 - ${hotels.value.length}家酒店`,
      description: `搜索${place}酒店，共找到${hotels.value.length}家酒店，对比价格找到最优惠的。`,
    })

    // Track search event
    const tracking = useTracking()
    tracking.trackSearch({
      provider: provider || undefined,
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
    const data = await post<Hotel[]>('/search', q)
    hotels.value.push(...(data.hotels || []))
    hasMore.value = !!data.has_more
  } catch { /* ignore */ } finally {
    loadingMore.value = false
  }
}

watch(() => route.query, search, { immediate: true })
</script>
