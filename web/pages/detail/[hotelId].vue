<template>
  <div class="container py-4">
    <div v-if="pending" class="text-center py-5">
      <div class="spinner-border" role="status"></div>
      <p class="mt-2 text-muted">加载中...</p>
    </div>

    <div v-else-if="error" class="text-center py-5">
      <div class="empty-state-icon"><i class="bi bi-exclamation-triangle"></i></div>
      <h4>加载失败</h4>
      <p class="text-muted">{{ error }}</p>
      <NuxtLink to="/" class="btn btn-primary">返回搜索</NuxtLink>
    </div>

    <template v-else-if="hotel">
      <!-- Header -->
      <div class="hotel-header">
        <div class="row align-items-center">
          <div class="col-lg-8">
            <h3 class="fw-bold mb-2">{{ hotel.name }}</h3>
            <p v-if="hotel.address" class="text-muted mb-2">
              <i class="bi bi-geo-alt me-1"></i>{{ hotel.address }}
            </p>
            <div class="d-flex gap-2 align-items-center flex-wrap">
              <div v-if="hotel.star_rating" class="star-rating">
                <i v-for="s in Math.min(hotel.star_rating, 5)" :key="s" class="bi bi-star-fill"></i>
              </div>
              <span v-if="hotel.rating" class="rating-badge">
                <i class="bi bi-star-fill"></i>{{ hotel.rating }}
              </span>
              <span v-if="hotel.brand" class="badge bg-light text-dark">{{ hotel.brand }}</span>
            </div>
          </div>
          <div class="col-lg-4 text-lg-end mt-3 mt-lg-0">
            <div v-if="hotel.price_per_night" class="price-section p-3 d-inline-block">
              <small class="text-muted">每晚最低</small>
              <PriceBadge :price="hotel.price_per_night" :currency="hotel.currency" per-night />
            </div>
            <div class="mt-2 d-flex gap-2 justify-content-lg-end">
              <FavoriteButton
                :hotel-id="hotel.hotel_id"
                :hotel-name="hotel.name"
                :provider="hotel.provider"
                :is-favorite="hotel.is_favorite"
              />
              <a
                v-if="hotel.booking_url"
                :href="`/api/click/track?url=${encodeURIComponent(hotel.booking_url)}&hotel_id=${hotel.hotel_id}&provider=${hotel.provider}&hotel_name=${encodeURIComponent(hotel.name)}&source=detail`"
                target="_blank"
                class="btn btn-primary"
              >
                <i class="bi bi-calendar-check me-1"></i>立即预订
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- Image Gallery -->
      <div v-if="hotel.images?.length" class="mb-4">
        <div class="hotel-main-image" :style="{ backgroundImage: `url(${hotel.images[0]})` }"></div>
        <div class="image-gallery">
          <div
            v-for="(img, idx) in hotel.images.slice(0, 10)"
            :key="idx"
            class="gallery-thumb"
            :class="{ active: mainImage === idx }"
            :style="{ backgroundImage: `url(${img})` }"
            @click="mainImage = idx"
          ></div>
        </div>
      </div>

      <!-- Description -->
      <div v-if="hotel.description" class="card mb-4">
        <div class="card-header">
          <i class="bi bi-info-circle"></i>酒店介绍
        </div>
        <div class="card-body">
          <p class="mb-0" style="white-space:pre-wrap">{{ hotel.description }}</p>
        </div>
      </div>

      <!-- Map -->
      <div v-if="hotel.latitude && hotel.longitude" class="card mb-4">
        <div class="card-header">
          <i class="bi bi-map"></i>位置
        </div>
        <div class="card-body p-0">
          <ClientOnly>
            <div style="height:300px; border-radius:0 0 var(--radius-xl) var(--radius-xl)">
              <div class="d-flex align-items-center justify-content-center h-100 text-muted">
                <i class="bi bi-geo-alt me-2"></i>{{ hotel.address }}
              </div>
            </div>
          </ClientOnly>
        </div>
      </div>

      <!-- Amenities -->
      <div v-if="hotel.amenities?.length" class="card mb-4">
        <div class="card-header">
          <i class="bi bi-grid"></i>酒店设施
        </div>
        <div class="card-body">
          <div class="row g-2">
            <div v-for="amenity in hotel.amenities" :key="amenity" class="col-6 col-md-4 col-lg-3">
              <div class="amenity-item">
                <i class="bi bi-check-circle"></i>{{ amenity }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Room Plans -->
      <div v-if="hotel.room_plans?.length" class="card mb-4">
        <div class="card-header">
          <i class="bi bi-house-door"></i>房型与价格
          <span class="badge bg-primary ms-auto">{{ hotel.room_plans.length }} 种房型</span>
        </div>
        <div class="card-body p-0">
          <div
            v-for="room in hotel.room_plans"
            :key="room.room_id"
            class="room-plan-card p-3 border-bottom"
          >
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h6 class="mb-1">{{ room.room_name }}</h6>
                <div class="d-flex flex-wrap gap-2 mb-2">
                  <span v-if="room.bed_type" class="badge bg-light"><i class="bi bi-bed me-1"></i>{{ room.bed_type }}</span>
                  <span v-if="room.room_size" class="badge bg-light">{{ room.room_size }}</span>
                  <span v-if="room.max_occupancy" class="badge bg-light"><i class="bi bi-person me-1"></i>{{ room.max_occupancy }}人</span>
                  <span v-if="room.breakfast" class="badge bg-light"><i class="bi bi-cup-hot me-1"></i>{{ room.breakfast }}</span>
                </div>
              </div>
              <div class="text-end">
                <div v-if="room.price" class="price-badge" style="font-size:1.2rem">
                  ¥{{ room.price }}
                  <small>/晚</small>
                </div>
                <span v-if="!room.available" class="badge bg-danger">已满</span>
                <span v-else class="badge bg-success">可订</span>
              </div>
            </div>
            <a
              v-if="room.available && hotel.booking_url"
              :href="`/api/click/track?url=${encodeURIComponent(hotel.booking_url)}&hotel_id=${hotel.hotel_id}&provider=${hotel.provider}&source=room`"
              target="_blank"
              class="btn btn-sm btn-primary mt-2"
            >
              预订此房型
            </a>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { HotelDetail } from '~/types/api'

const route = useRoute()
const pending = ref(true)
const error = ref('')
const hotel = ref<HotelDetail | null>(null)
const mainImage = ref(0)

async function loadHotel() {
  pending.value = true
  error.value = ''
  const { get } = useApi()
  const hotelId = route.params.hotelId as string
  const provider = route.query.provider as string
  const params: Record<string, string> = {
    provider: provider || 'tuniu',
    adult_count: (route.query.adult_count as string) || '2',
    child_count: (route.query.child_count as string) || '0',
  }
  if (route.query.check_in) params.check_in = route.query.check_in as string
  if (route.query.check_out) params.check_out = route.query.check_out as string
  if (route.query.check_in_date) params.check_in_date = route.query.check_in_date as string
  if (route.query.check_out_date) params.check_out_date = route.query.check_out_date as string

  try {
    const data = await get<{ hotel: HotelDetail; is_favorite: boolean }>(`/hotel/${hotelId}`, params)
    hotel.value = { ...data.hotel, is_favorite: data.is_favorite }

    if (hotel.value) {
      useSeoMeta({
        title: `${hotel.value.name} - 酒店详情`,
        ogTitle: hotel.value.name,
        ogDescription: hotel.value.description?.substring(0, 160),
        ogImage: hotel.value.image_url,
      })

      // Track view hotel event
      const tracking = useTracking()
      tracking.trackViewHotel({
        hotelId: hotel.value.hotel_id,
        hotelName: hotel.value.name,
        provider: hotel.value.provider,
        price: hotel.value.price_per_night,
      })
    }
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    pending.value = false
  }
}

watch(() => route.params.hotelId, loadHotel, { immediate: true })
</script>
