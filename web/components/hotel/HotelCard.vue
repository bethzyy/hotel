<template>
  <div class="hotel-card" :style="{ '--index': index }">
    <div class="row g-0">
      <!-- Image -->
      <div class="col-md-4 position-relative">
        <HotelImage :src="hotel.image_url" :alt="hotel.name" />
        <FavoriteButton
          :hotel-id="hotel.hotel_id"
          :hotel-name="hotel.name"
          :provider="hotel.provider"
          :is-favorite="hotel.is_favorite"
        />
        <!-- Star name badge on image -->
        <span v-if="hotel.star_name" class="position-absolute top-0 start-0 badge bg-dark bg-opacity-75 m-2" style="font-size:0.7rem">
          {{ hotel.star_name }}
        </span>
      </div>
      <!-- Info -->
      <div class="col-md-8 p-3">
        <div class="d-flex justify-content-between align-items-start mb-1">
          <div class="flex-grow-1">
            <h5 class="hotel-name mb-1">
              <NuxtLink
                :to="`/detail/${hotel.hotel_id}?provider=${hotel.provider}&check_in=${checkIn}&check_out=${checkOut}`"
                class="text-decoration-none text-dark"
              >
                {{ hotel.name }}
              </NuxtLink>
            </h5>
            <div class="d-flex gap-1 align-items-center flex-wrap mb-1">
              <div v-if="hotel.star_rating" class="star-rating">
                <i v-for="s in Math.min(hotel.star_rating, 5)" :key="s" class="bi bi-star-fill"></i>
              </div>
              <span v-if="hotel.brand_name" class="badge bg-primary bg-opacity-10 text-primary" style="font-size:0.7rem">
                {{ hotel.brand_name }}
              </span>
              <!-- Source badge (unified search) -->
              <SourceBadge :sources="hotel._sources" :provider="hotel.provider" />
            </div>
          </div>
          <PriceBadge :price="hotel.price_per_night" :currency="hotel.currency" per-night />
        </div>

        <!-- Address + Business -->
        <p v-if="hotel.address || hotel.business" class="text-muted mb-1" style="font-size:0.85rem">
          <i class="bi bi-geo-alt me-1"></i>
          <span v-if="hotel.address">{{ hotel.address }}</span>
          <span v-if="hotel.business" class="ms-1 text-primary" style="font-size:0.8rem">
            <i class="bi bi-pin-map me-1"></i>{{ hotel.business }}
          </span>
          <span v-if="hotel.distance != null" class="badge bg-light text-primary ms-2" style="font-size:0.75rem">
            <i class="bi bi-signpost-split me-1"></i>{{ formatDistance(hotel.distance) }}
          </span>
        </p>

        <!-- Room info line (Tuniu) -->
        <div v-if="hotel.room_name || hotel.meal || hotel.refund" class="mb-1" style="font-size:0.78rem">
          <span v-if="hotel.room_name" class="text-muted me-2"><i class="bi bi-house me-1"></i>{{ hotel.room_name }}</span>
          <span v-if="hotel.meal" class="badge bg-light text-secondary me-1" style="font-size:0.7rem">{{ hotel.meal }}</span>
          <span v-if="hotel.refund" class="badge bg-light text-secondary me-1" style="font-size:0.7rem">{{ hotel.refund }}</span>
        </div>

        <!-- Comment digest (Tuniu) -->
        <p v-if="hotel.comment_digest" class="text-muted mb-1 fst-italic" style="font-size:0.78rem">
          "{{ hotel.comment_digest }}"
        </p>

        <!-- Tags -->
        <div v-if="hotel.tags?.length" class="hotel-tags mb-1">
          <span v-for="tag in hotel.tags.slice(0, 4)" :key="tag" class="tag">{{ tag }}</span>
        </div>

        <!-- Amenities preview -->
        <div v-if="hotel.amenities?.length" class="amenities-preview">
          <span v-for="amenity in hotel.amenities.slice(0, 3)" :key="amenity" class="amenity-tag">
            <i class="bi bi-check-lg me-1"></i>{{ amenity }}
          </span>
        </div>

        <!-- Rating badge -->
        <div v-if="hotel.rating" class="mt-1">
          <span class="rating-badge">
            <i class="bi bi-star-fill"></i>
            {{ hotel.rating }}
            <span v-if="hotel.review_count" style="font-weight:400; font-size:0.75rem">({{ hotel.review_count }})</span>
          </span>
        </div>

        <!-- Country/Area badge -->
        <div v-if="hotel.country" class="mt-1">
          <span class="badge bg-info bg-opacity-10 text-info">{{ hotel.country }}</span>
        </div>

        <!-- Actions -->
        <div class="d-flex gap-2 mt-2">
          <NuxtLink
            :to="`/detail/${hotel.hotel_id}?provider=${hotel.provider}&check_in=${checkIn}&check_out=${checkOut}`"
            class="btn btn-sm btn-outline-primary rounded-pill"
          >
            <i class="bi bi-eye me-1"></i>详情
          </NuxtLink>
          <button
            v-if="hotel.provider === 'tuniu'"
            class="btn btn-sm btn-primary rounded-pill"
            @click="$event.preventDefault(); navigateToBooking()"
          >
            <i class="bi bi-calendar-check me-1"></i>在线预订
          </button>
          <button
            v-else-if="hotel.booking_url"
            class="btn btn-sm btn-outline-secondary rounded-pill"
            @click="trackAndBook(hotel)"
          >
            <i class="bi bi-calendar-check me-1"></i>预订
          </button>
          <button
            class="btn btn-sm btn-outline-secondary rounded-pill"
            @click="toggleComparison"
          >
            <i class="bi bi-arrow-left-right me-1"></i>比价
          </button>
        </div>

        <!-- Comparison Section (inline) -->
        <ComparisonSection
          v-if="showComparison"
          :hotel-id="hotel.hotel_id"
          :provider="hotel.provider"
          :hotel-name="hotel.name"
          :check-in="checkIn"
          :check-out="checkOut"
          :source-price="hotel.price_per_night"
          :source-currency="hotel.currency"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Hotel } from '~/types/api'

const props = defineProps<{
  hotel: Hotel
  index?: number
  checkIn?: string
  checkOut?: string
}>()

const showComparison = ref(false)

function toggleComparison() {
  showComparison.value = !showComparison.value
}

function navigateToBooking() {
  navigateTo(`/detail/${props.hotel.hotel_id}?provider=tuniu&check_in=${props.checkIn}&check_out=${props.checkOut}`)
}

function trackAndBook(hotel: Hotel) {
  const url = `/api/click/track?url=${encodeURIComponent(hotel.booking_url || '')}&hotel_id=${hotel.hotel_id}&provider=${hotel.provider}&hotel_name=${encodeURIComponent(hotel.name)}&source=card`
  window.open(url, '_blank')
}

function formatDistance(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)}米`
  return `${(meters / 1000).toFixed(1)}公里`
}
</script>
