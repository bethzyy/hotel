<template>
  <div class="hotel-card" :style="{ '--index': index }">
    <div class="row g-0">
      <!-- Image -->
      <div class="col-md-4">
        <HotelImage :src="hotel.image_url" :alt="hotel.name" />
        <FavoriteButton
          :hotel-id="hotel.hotel_id"
          :hotel-name="hotel.name"
          :provider="hotel.provider"
          :is-favorite="hotel.is_favorite"
        />
      </div>
      <!-- Info -->
      <div class="col-md-8 p-3">
        <div class="d-flex justify-content-between align-items-start mb-2">
          <div class="flex-grow-1">
            <h5 class="hotel-name mb-1">
              <NuxtLink
                :to="`/detail/${hotel.hotel_id}?provider=${hotel.provider}&check_in=${checkIn}&check_out=${checkOut}`"
                class="text-decoration-none text-dark"
              >
                {{ hotel.name }}
              </NuxtLink>
            </h5>
            <div v-if="hotel.star_rating" class="star-rating mb-1">
              <i v-for="s in Math.min(hotel.star_rating, 5)" :key="s" class="bi bi-star-fill"></i>
            </div>
          </div>
          <PriceBadge :price="hotel.price_per_night" :currency="hotel.currency" per-night />
        </div>

        <p v-if="hotel.address" class="text-muted mb-2" style="font-size:0.85rem">
          <i class="bi bi-geo-alt me-1"></i>{{ hotel.address }}
        </p>

        <!-- Tags -->
        <div v-if="hotel.tags?.length" class="hotel-tags mb-2">
          <span v-for="tag in hotel.tags.slice(0, 4)" :key="tag" class="tag">{{ tag }}</span>
        </div>

        <!-- Amenities preview -->
        <div v-if="hotel.amenities?.length" class="amenities-preview">
          <span v-for="amenity in hotel.amenities.slice(0, 3)" :key="amenity" class="amenity-tag">
            <i class="bi bi-check-lg me-1"></i>{{ amenity }}
          </span>
        </div>

        <!-- Rating badge -->
        <div v-if="hotel.rating" class="mt-2">
          <span class="rating-badge">
            <i class="bi bi-star-fill"></i>
            {{ hotel.rating }}
            <span v-if="hotel.review_count" style="font-weight:400; font-size:0.75rem">({{ hotel.review_count }})</span>
          </span>
        </div>

        <!-- Country/Area badge -->
        <div v-if="hotel.country" class="mt-2">
          <span class="badge bg-info bg-opacity-10 text-info">{{ hotel.country }}</span>
        </div>

        <!-- Actions -->
        <div class="d-flex gap-2 mt-3">
          <NuxtLink
            :to="`/detail/${hotel.hotel_id}?provider=${hotel.provider}&check_in=${checkIn}&check_out=${checkOut}`"
            class="btn btn-sm btn-outline-primary rounded-pill"
          >
            <i class="bi bi-eye me-1"></i>详情
          </NuxtLink>
          <button
            v-if="hotel.booking_url"
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

function trackAndBook(hotel: Hotel) {
  const url = `/api/click/track?url=${encodeURIComponent(hotel.booking_url || '')}&hotel_id=${hotel.hotel_id}&provider=${hotel.provider}&hotel_name=${encodeURIComponent(hotel.name)}&source=card`
  window.open(url, '_blank')
}
</script>
