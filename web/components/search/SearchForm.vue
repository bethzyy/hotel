<template>
  <div>
    <div class="text-center py-3 mb-1">
      <h1 class="hero-title display-4 mb-2">发现理想酒店</h1>
      <p class="hero-subtitle">搜索全球酒店，对比多平台价格，找到最低价</p>
    </div>

    <div class="search-container">
      <form class="search-form" @submit.prevent="handleSearch">
        <!-- Unified Destination Input -->
        <div class="row g-2 mb-2">
          <div class="col-md-6">
            <label class="form-label small text-muted">目的地</label>
            <div class="position-relative">
              <input
                ref="destinationInput"
                v-model="destination"
                type="text"
                class="form-control"
                placeholder="城市、景点、地标，如：上海陆家嘴、东京、巴黎"
                required
                @focus="showSuggestions = true"
                @blur="hideSuggestions"
              >
              <div v-if="showSuggestions && filteredCities.length" class="city-suggestions dropdown-menu show position-absolute w-100" style="z-index:10">
                <a v-for="city in filteredCities" :key="city" class="dropdown-item" href="#"
                  @mousedown.prevent="destination = city; showSuggestions = false">{{ city }}</a>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <label class="form-label small text-muted">入住日期</label>
            <input v-model="store.checkIn" type="date" class="form-control" required>
          </div>
          <div class="col-md-3">
            <label class="form-label small text-muted">退房日期</label>
            <input v-model="store.checkOut" type="date" class="form-control" required>
          </div>
        </div>

        <div class="row g-2 mb-2">
          <div class="col-md-3">
            <label class="form-label small text-muted">成人数</label>
            <div class="input-group">
              <button type="button" class="btn btn-outline-secondary" @click="adjustCount('adultCount', -1)">-</button>
              <input v-model.number="store.adultCount" type="number" class="form-control text-center" min="1" max="10">
              <button type="button" class="btn btn-outline-secondary" @click="adjustCount('adultCount', 1)">+</button>
            </div>
          </div>
          <div class="col-md-3">
            <label class="form-label small text-muted">儿童数</label>
            <div class="input-group">
              <button type="button" class="btn btn-outline-secondary" @click="adjustCount('childCount', -1)">-</button>
              <input v-model.number="store.childCount" type="number" class="form-control text-center" min="0" max="10">
              <button type="button" class="btn btn-outline-secondary" @click="adjustCount('childCount', 1)">+</button>
            </div>
          </div>
          <div class="col-md-6">
            <label class="form-label small text-muted">关键词（可选）</label>
            <input v-model="store.keyword" type="text" class="form-control" placeholder="酒店名/品牌">
          </div>
        </div>

        <!-- Mode hint -->
        <div class="mb-2">
          <small class="text-muted">
            <i class="bi bi-lightbulb me-1"></i>
            国内城市自动搜索途牛+全球双源，海外城市使用全球搜索
          </small>
        </div>

        <button type="submit" class="btn btn-primary btn-lg w-100 rounded-pill mt-2" :disabled="isSearching">
          <span v-if="isSearching" class="spinner-border spinner-border-sm me-2"></span>
          <i v-else class="bi bi-search me-2"></i>
          {{ isSearching ? '搜索中...' : '搜索酒店' }}
        </button>
      </form>
    </div>

    <!-- Search History -->
    <SearchHistory v-if="history.length" :items="history" @select="fillFromHistory" />
  </div>
</template>

<script setup lang="ts">
const POPULAR_CITIES = [
  '北京', '上海', '广州', '深圳', '杭州', '成都', '重庆', '武汉',
  '南京', '西安', '长沙', '苏州', '厦门', '青岛', '大连', '三亚',
  '丽江', '桂林', '昆明', '哈尔滨', '天津', '郑州', '济南', '福州',
  '东京', '大阪', '首尔', '曼谷', '新加坡', '巴黎', '伦敦', '纽约',
]

const store = useSearchFormStore()

const destination = ref(store.cityName || store.place || '')
const isSearching = ref(false)
const history = ref<{ query: string; place: string; provider: string }[]>([])
const showSuggestions = ref(false)
const destinationInput = ref<HTMLInputElement | null>(null)

// Sync destination back to store
watch(destination, (val) => {
  store.cityName = val
  store.place = val
})

// Validate persisted dates on mount
onMounted(() => {
  store.validateDates()
  // Restore destination from store if available
  if (store.cityName) destination.value = store.cityName
  else if (store.place) destination.value = store.place
  loadHistory()
})

const filteredCities = computed(() => {
  const q = destination.value.trim()
  if (!q) return POPULAR_CITIES.slice(0, 10)
  return POPULAR_CITIES.filter(c => c.includes(q)).slice(0, 10)
})

function hideSuggestions() {
  setTimeout(() => { showSuggestions.value = false }, 150)
}

function adjustCount(field: 'adultCount' | 'childCount', delta: number) {
  const val = store[field] as number
  const min = field === 'adultCount' ? 1 : 0
  const max = 10
  store[field] = Math.min(max, Math.max(min, val + delta))
}

async function loadHistory() {
  if (!import.meta.client) return
  const { get } = useApi()
  try {
    const data = await get<{ history: { query: string; place: string; provider: string }[] }>('/history', { limit: '5' })
    history.value = data.history
  } catch { /* ignore */ }
}

function fillFromHistory(item: { query: string; place: string; provider: string }) {
  destination.value = item.place || item.query
}

async function handleSearch() {
  if (!destination.value.trim()) return
  isSearching.value = true
  try {
    const dest = destination.value.trim()

    // Save to search history
    const { post } = useApi()
    post('/history', {
      query: dest,
      place: dest,
      place_type: '城市',
      provider: 'auto',
    }).catch(() => {})

    // Calculate stay_nights from check_in and check_out
    const nights = Math.max(1, Math.round(
      (new Date(store.checkOut).getTime() - new Date(store.checkIn).getTime()) / (1000 * 60 * 60 * 24)
    ))

    // Unified search: send destination + dates to backend
    await navigateTo({
      path: '/results',
      query: {
        destination: dest,
        check_in: store.checkIn,
        check_out: store.checkOut,
        stay_nights: String(nights),
        adult_count: String(store.adultCount),
        child_count: String(store.childCount),
        keyword: store.keyword || undefined,
      },
    })
  } finally {
    isSearching.value = false
  }
}
</script>
