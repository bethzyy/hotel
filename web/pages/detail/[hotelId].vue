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
              <span v-if="hotel.business" class="ms-2 text-primary"><i class="bi bi-pin-map me-1"></i>{{ hotel.business }}</span>
            </p>
            <div class="d-flex gap-2 align-items-center flex-wrap">
              <div v-if="hotel.star_rating" class="star-rating">
                <i v-for="s in Math.min(hotel.star_rating, 5)" :key="s" class="bi bi-star-fill"></i>
              </div>
              <span v-if="hotel.star_name" class="badge bg-primary bg-opacity-10 text-primary">{{ hotel.star_name }}</span>
              <span v-if="hotel.rating" class="rating-badge">
                <i class="bi bi-star-fill"></i>{{ hotel.rating }}
              </span>
              <span v-if="hotel.brand_name || hotel.brand" class="badge bg-light text-dark">{{ hotel.brand_name || hotel.brand }}</span>
              <SourceBadge :sources="hotel._sources" :provider="hotel.provider" />
            </div>
            <!-- Policies -->
            <div v-if="hotel.policies" class="mt-2 d-flex gap-3 flex-wrap" style="font-size:0.85rem">
              <span v-if="hotel.policies.check_in_time" class="text-muted">
                <i class="bi bi-box-arrow-in-right me-1"></i>入住 {{ hotel.policies.check_in_time }}
              </span>
              <span v-if="hotel.policies.check_out_time" class="text-muted">
                <i class="bi bi-box-arrow-right me-1"></i>退房 {{ hotel.policies.check_out_time }}
              </span>
              <span v-if="hotel.policies.cancel_policy" class="text-success">
                <i class="bi bi-shield-check me-1"></i>{{ hotel.policies.cancel_policy }}
              </span>
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
              <!-- Tuniu booking (for tuniu or merged hotels) -->
              <button
                v-if="hotel.provider === 'tuniu' || hotel._sources?.includes('tuniu')"
                class="btn btn-primary"
                @click="showBookingModal = true"
              >
                <i class="bi bi-calendar-check me-1"></i>在线预订
              </button>
              <!-- RollingGo booking URL -->
              <a
                v-if="hotel.booking_url"
                :href="`/api/click/track?url=${encodeURIComponent(hotel.booking_url)}&hotel_id=${hotel.hotel_id}&provider=${hotel.provider}&hotel_name=${encodeURIComponent(hotel.name)}&source=detail`"
                target="_blank"
                class="btn btn-outline-primary"
              >
                <i class="bi bi-globe2 me-1"></i>全球预订
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- Image Gallery -->
      <div v-if="hotel.images?.length" class="mb-4">
        <div class="hotel-main-image" :style="{ backgroundImage: `url(${hotel.images[mainImage]})` }"></div>
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
      <!-- Fallback: single image from search snippet -->
      <div v-else-if="hotel.image_url" class="mb-4">
        <div class="hotel-main-image" :style="{ backgroundImage: `url(${hotel.image_url})` }"></div>
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

      <!-- Room Plans - Grouped by room type -->
      <div v-if="groupedRooms.size" class="card mb-4">
        <div class="card-header d-flex align-items-center">
          <span><i class="bi bi-house-door"></i>房型与价格</span>
          <span class="badge bg-primary ms-auto">{{ groupedRooms.size }} 种房型</span>
        </div>
        <div class="card-body p-0">
          <div v-for="[typeId, rooms] of groupedRooms" :key="typeId" class="border-bottom">
            <!-- Room type header -->
            <div class="p-3 bg-light bg-opacity-50">
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <h6 class="mb-1 fw-bold">{{ rooms[0].room_name }}</h6>
                  <div class="d-flex flex-wrap gap-2">
                    <span v-if="rooms[0].bed_type && rooms[0].bed_type !== '未知床型'" class="badge bg-white text-dark border">
                      <i class="bi bi-bed me-1"></i>{{ rooms[0].bed_type }}
                    </span>
                    <span v-if="rooms[0].room_size" class="badge bg-white text-dark border">
                      <i class="bi bi-arrows-angle-expand me-1"></i>{{ rooms[0].room_size }}
                    </span>
                    <span v-if="rooms[0].max_occupancy" class="badge bg-white text-dark border">
                      <i class="bi bi-person me-1"></i>{{ rooms[0].max_occupancy }}人
                    </span>
                    <span v-if="rooms[0].floor" class="badge bg-white text-dark border">
                      <i class="bi bi-building me-1"></i>{{ rooms[0].floor }}
                    </span>
                  </div>
                </div>
                <div v-if="rooms[0].room_images?.length" class="d-none d-md-block" style="width:80px;height:60px">
                  <img :src="rooms[0].room_images[0]" class="rounded w-100 h-100" style="object-fit:cover" />
                </div>
              </div>
            </div>
            <!-- Rate plans -->
            <div
              v-for="room in rooms"
              :key="room.rate_plan_id || room.room_id + room.rate_plan_name"
              class="rate-plan-item px-3 py-2 border-bottom d-flex justify-content-between align-items-center"
              :class="{ 'opacity-50': !room.available }"
            >
              <div class="flex-grow-1">
                <div class="fw-medium" style="font-size:0.9rem">{{ room.rate_plan_name }}</div>
                <div class="d-flex gap-2 mt-1" style="font-size:0.78rem">
                  <span v-if="room.breakfast" class="text-muted"><i class="bi bi-cup-hot me-1"></i>{{ room.breakfast }}</span>
                  <span v-if="room.cancel_policy" class="text-muted" :title="room.cancel_policy">
                    <i class="bi bi-shield me-1"></i>{{ truncatePolicy(room.cancel_policy) }}
                  </span>
                </div>
              </div>
              <div class="d-flex align-items-center gap-3">
                <div class="text-end">
                  <div v-if="room.price" class="price-badge" style="font-size:1.1rem">
                    ¥{{ Math.round(room.price) }}
                    <small>/晚</small>
                  </div>
                  <div v-else-if="getReferencePrice(room)" class="price-badge text-muted" style="font-size:1rem">
                    ~¥{{ getReferencePrice(room) }}
                    <small>/晚参考</small>
                  </div>
                  <span v-if="!room.available" class="badge bg-secondary">已满</span>
                </div>
                <button
                  v-if="room.available && hotel.provider === 'tuniu'"
                  class="btn btn-sm btn-primary rounded-pill"
                  @click="openBooking(room)"
                >
                  预订
                </button>
                <span v-else-if="room.available" class="badge bg-success">可订</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Booking Modal -->
      <div v-if="showBookingModal" class="modal-overlay" @click.self="showBookingModal = false">
        <div class="modal-content card" style="max-width:480px; width:90%">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span><i class="bi bi-calendar-check me-1"></i>预订 {{ selectedRoom?.room_name }}</span>
            <button class="btn-close" @click="showBookingModal = false"></button>
          </div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label small text-muted">方案</label>
              <div class="fw-medium">{{ selectedRoom?.rate_plan_name }} · ¥{{ Math.round(selectedRoom?.price || 0) }}/晚</div>
              <div class="text-muted" style="font-size:0.8rem">{{ selectedRoom?.breakfast }} · {{ truncatePolicy(selectedRoom?.cancel_policy || '') }}</div>
            </div>
            <div class="mb-3">
              <label class="form-label small text-muted">房间数</label>
              <select v-model="bookingForm.roomCount" class="form-select">
                <option v-for="n in 5" :key="n" :value="n">{{ n }}间</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label small text-muted">联系人姓名</label>
              <input v-model="bookingForm.contactName" type="text" class="form-control" placeholder="入住人姓名" />
            </div>
            <div class="mb-3">
              <label class="form-label small text-muted">手机号</label>
              <input v-model="bookingForm.contactPhone" type="tel" class="form-control" placeholder="接收订单信息" />
            </div>
            <div v-if="bookingError" class="alert alert-danger py-2" style="font-size:0.85rem">{{ bookingError }}</div>
            <button class="btn btn-primary w-100" :disabled="bookingLoading" @click="submitBooking">
              <span v-if="bookingLoading" class="spinner-border spinner-border-sm me-1"></span>
              确认预订
            </button>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup lang="ts">
import type { HotelDetail, RoomPlan } from '~/types/api'

const route = useRoute()
const pending = ref(true)
const error = ref('')
const hotel = ref<HotelDetail | null>(null)
const mainImage = ref(0)

// Booking state
const showBookingModal = ref(false)
const selectedRoom = ref<RoomPlan | null>(null)
const bookingLoading = ref(false)
const bookingError = ref('')
const bookingForm = reactive({
  roomCount: 1,
  contactName: '',
  contactPhone: '',
})

const groupedRooms = computed(() => {
  const plans = hotel.value?.room_plans || []
  const map = new Map<string, RoomPlan[]>()
  for (const plan of plans) {
    const key = plan.room_type_id || plan.room_id
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(plan)
  }
  return map
})

function truncatePolicy(policy: string): string {
  if (!policy) return ''
  if (policy.length <= 30) return policy
  // Extract the key info: first sentence before "。"
  const firstSentence = policy.split('。')[0]
  if (firstSentence.length <= 40) return firstSentence
  return policy.substring(0, 30) + '...'
}

function getReferencePrice(room: RoomPlan): string | null {
  const policies = (room as any).cancellation_policies
  if (policies && Array.isArray(policies) && policies.length > 0) {
    const amount = policies[0].amount
    if (amount && typeof amount === 'number') {
      // Check-in/out dates for night calculation
      const ci = hotel.value?.check_in
      const co = hotel.value?.check_out
      let nights = 1
      if (ci && co) {
        const diff = (new Date(co)).getTime() - (new Date(ci)).getTime()
        nights = Math.max(1, Math.round(diff / 86400000))
      }
      return String(Math.round(amount / nights))
    }
  }
  return null
}

function openBooking(room: RoomPlan) {
  selectedRoom.value = room
  bookingError.value = ''
  bookingForm.roomCount = 1
  bookingForm.contactName = ''
  bookingForm.contactPhone = ''
  showBookingModal.value = true
}

async function submitBooking() {
  if (!selectedRoom.value || !hotel.value) return
  if (!bookingForm.contactName.trim()) { bookingError.value = '请输入联系人姓名'; return }
  if (!bookingForm.contactPhone.trim()) { bookingError.value = '请输入手机号'; return }

  bookingLoading.value = true
  bookingError.value = ''

  try {
    const { post } = useApi()
    const checkIn = (route.query.check_in || route.query.check_in_date) as string
    const checkOut = (route.query.check_out || route.query.check_out_date) as string

    const result = await post<{
      success: boolean
      order_id?: string
      payment_url?: string
      error?: string
    }>('/booking/create-order', {
      provider: 'tuniu',
      hotel_id: hotel.value.hotel_id,
      room_id: selectedRoom.value.rate_plan_id || selectedRoom.value.room_id,
      pre_book_param: selectedRoom.value.pre_book_param,
      check_in_date: checkIn,
      check_out_date: checkOut,
      room_count: bookingForm.roomCount,
      contact_name: bookingForm.contactName,
      contact_phone: bookingForm.contactPhone,
      room_guests: Array.from({ length: bookingForm.roomCount }, () => ({
        guests: [{ firstName: bookingForm.contactName, lastName: '' }]
      })),
    })

    if (result.payment_url) {
      showBookingModal.value = false
      window.open(result.payment_url, '_blank')
    } else if (result.order_id) {
      showBookingModal.value = false
      alert(`预订成功！订单号: ${result.order_id}`)
    }
  } catch (e: any) {
    bookingError.value = e.message || '预订失败，请重试'
  } finally {
    bookingLoading.value = false
  }
}

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
    const data = await get<HotelDetail>(`/hotel/${hotelId}`, params)
    hotel.value = data

    // 从搜索结果 sessionStorage 补全空字段（RollingGo 详情 API 经常返回空壳）
    if (hotel.value) {
      try {
        const raw = sessionStorage.getItem(`hotel_snippet:${hotelId}`)
        if (raw) {
          const snippet = JSON.parse(raw)
          for (const [k, v] of Object.entries(snippet)) {
            if ((hotel.value as any)[k] == null || (hotel.value as any)[k] === '') {
              (hotel.value as any)[k] = v
            }
          }
        }
      } catch {}
    }

    if (hotel.value) {
      useSeoMeta({
        title: `${hotel.value.name} - 酒店详情`,
        ogTitle: hotel.value.name,
        ogDescription: hotel.value.description?.substring(0, 160),
        ogImage: hotel.value.image_url,
      })

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

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}
.modal-content {
  animation: slideUp 0.2s ease-out;
}
@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.rate-plan-item:hover {
  background: var(--bs-gray-100);
}
</style>
