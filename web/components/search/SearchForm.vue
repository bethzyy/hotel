<template>
  <div>
    <div class="text-center py-4 mb-2">
      <h1 class="gradient-text display-4 fw-bold mb-2">发现理想酒店</h1>
      <p class="text-muted">搜索全球酒店，对比多平台价格，找到最低价</p>
    </div>

    <div class="search-container">
      <form class="search-form" @submit.prevent="handleSearch">
        <!-- Provider Toggle -->
        <div class="d-flex gap-3 mb-4">
          <div
            v-for="p in providers" :key="p.id"
            class="provider-card flex-fill p-3 text-center"
            :class="{ selected: store.provider === p.id }"
            @click="store.setProvider(p.id)"
          >
            <span class="mb-0 fw-medium" style="cursor:pointer">
              {{ p.name }}
            </span>
            <div style="font-size:0.75rem" class="text-muted">{{ p.description }}</div>
          </div>
        </div>

        <!-- Tuniu: City + Date Range -->
        <template v-if="store.provider === 'tuniu'">
          <div class="row g-3 mb-3">
            <div class="col-md-4">
              <label class="form-label small text-muted">城市</label>
              <div class="position-relative">
                <input v-model="store.cityName" type="text" class="form-control" placeholder="输入城市名称" required
                  @focus="showCitySuggestions = true" @blur="hideCitySuggestions">
                <div v-if="showCitySuggestions && filteredCities.length" class="city-suggestions dropdown-menu show position-absolute w-100" style="z-index:10">
                  <a v-for="city in filteredCities" :key="city" class="dropdown-item" href="#"
                    @mousedown.prevent="store.cityName = city; showCitySuggestions = false">{{ city }}</a>
                </div>
              </div>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">入住日期</label>
              <input v-model="store.checkIn" type="date" class="form-control" required>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">退房日期</label>
              <input v-model="store.checkOut" type="date" class="form-control" required>
            </div>
          </div>
          <div class="row g-3 mb-3">
            <div class="col-md-4">
              <label class="form-label small text-muted">成人数</label>
              <div class="input-group">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('adultCount', -1)">-</button>
                <input v-model.number="store.adultCount" type="number" class="form-control text-center" min="1" max="10">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('adultCount', 1)">+</button>
              </div>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">儿童数</label>
              <div class="input-group">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('childCount', -1)">-</button>
                <input v-model.number="store.childCount" type="number" class="form-control text-center" min="0" max="10">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('childCount', 1)">+</button>
              </div>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">关键词（可选）</label>
              <input v-model="store.keyword" type="text" class="form-control" placeholder="酒店名/品牌">
            </div>
          </div>
        </template>

        <!-- RollingGo: Place + Date + Stay -->
        <template v-else>
          <div class="destination-input-wrapper mb-3">
            <div class="input-group input-group-lg">
              <span class="input-group-text bg-primary text-white border-0">
                <i class="bi bi-geo-alt-fill"></i>
              </span>
              <input v-model="store.place" type="text" class="form-control border-start-0" placeholder="输入目的地（景点、城市、机场、酒店...）" required>
            </div>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-md-4">
              <label class="form-label small text-muted">地点类型</label>
              <select v-model="store.placeType" class="form-select" required>
                <option value="">选择类型...</option>
                <option v-for="pt in placeTypes" :key="pt" :value="pt">{{ pt }}</option>
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">入住日期</label>
              <input v-model="store.checkInDate" type="date" class="form-control">
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">住宿晚数</label>
              <div class="input-group">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('stayNights', -1)">-</button>
                <input v-model.number="store.stayNights" type="number" class="form-control text-center" min="1" max="30">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('stayNights', 1)">+</button>
              </div>
            </div>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-md-6">
              <label class="form-label small text-muted">成人数</label>
              <div class="input-group">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('adultCount', -1)">-</button>
                <input v-model.number="store.adultCount" type="number" class="form-control text-center" min="1" max="10">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('adultCount', 1)">+</button>
              </div>
            </div>
            <div class="col-md-6">
              <label class="form-label small text-muted">儿童数</label>
              <div class="input-group">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('childCount', -1)">-</button>
                <input v-model.number="store.childCount" type="number" class="form-control text-center" min="0" max="10">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('childCount', 1)">+</button>
              </div>
            </div>
          </div>

          <!-- Advanced Filters -->
          <div class="mb-3">
            <button type="button" class="btn btn-link text-muted text-decoration-none p-0" @click="showAdvanced = !showAdvanced">
              <i class="bi bi-sliders me-1"></i> 高级筛选
              <i :class="showAdvanced ? 'bi bi-chevron-up' : 'bi bi-chevron-down'" class="ms-1"></i>
            </button>
          </div>
          <div v-if="showAdvanced" class="row g-3 mb-3">
            <div class="col-md-4">
              <label class="form-label small text-muted">最低星级</label>
              <select v-model="store.minStar" class="form-select">
                <option value="">不限</option>
                <option value="3">3星</option>
                <option value="4">4星</option>
                <option value="5">5星</option>
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">最高价格/晚</label>
              <input v-model.number="store.maxPrice" type="number" class="form-control" placeholder="不限">
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">搜索结果数</label>
              <select v-model="store.size" class="form-select">
                <option :value="10">10</option>
                <option :value="20">20</option>
                <option :value="50">50</option>
              </select>
            </div>
          </div>
        </template>

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
]

const providers = [
  { id: 'rollinggo', name: '全球酒店', description: 'RollingGo · 全球搜索' },
  { id: 'tuniu', name: '国内酒店', description: '途牛 · 国内预订' },
]

const placeTypes = ['景点', '城市', '机场', '火车站', '地铁站', '酒店', '区/县', '详细地址']

const store = useSearchFormStore()

const showAdvanced = ref(false)
const isSearching = ref(false)
const history = ref<{ query: string; place: string; provider: string }[]>([])
const showCitySuggestions = ref(false)

// Validate persisted dates on mount
onMounted(() => {
  store.validateDates()
  loadHistory()
})

const filteredCities = computed(() => {
  const q = store.cityName.trim()
  if (!q) return POPULAR_CITIES.slice(0, 8)
  return POPULAR_CITIES.filter(c => c.includes(q)).slice(0, 8)
})

function hideCitySuggestions() {
  setTimeout(() => { showCitySuggestions.value = false }, 150)
}

function adjustCount(field: 'adultCount' | 'childCount' | 'stayNights', delta: number) {
  const val = store[field] as number
  const min = field === 'adultCount' ? 1 : field === 'stayNights' ? 1 : 0
  const max = field === 'stayNights' ? 30 : 10
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
  if (item.provider === 'tuniu') {
    store.setProvider('tuniu')
    store.cityName = item.place || item.query
  } else {
    store.setProvider('rollinggo')
    store.place = item.place || item.query
  }
}

async function handleSearch() {
  isSearching.value = true
  try {
    // Save to search history
    const { post } = useApi()
    post('/history', {
      query: store.provider === 'tuniu' ? store.cityName : store.place,
      place: store.provider === 'tuniu' ? store.cityName : store.place,
      place_type: store.provider === 'rollinggo' ? store.placeType : '城市',
      provider: store.provider,
    }).catch(() => {})

    // Navigate to results
    if (store.provider === 'tuniu') {
      await navigateTo({
        path: '/results',
        query: {
          provider: 'tuniu',
          city_name: store.cityName,
          check_in: store.checkIn,
          check_out: store.checkOut,
          adult_count: String(store.adultCount),
          child_count: String(store.childCount),
          keyword: store.keyword || undefined,
        },
      })
    } else {
      await navigateTo({
        path: '/results',
        query: {
          provider: 'rollinggo',
          place: store.place,
          place_type: store.placeType,
          check_in_date: store.checkInDate,
          stay_nights: String(store.stayNights),
          adult_count: String(store.adultCount),
          child_count: String(store.childCount),
          min_star: store.minStar || undefined,
          max_price: store.maxPrice ? String(store.maxPrice) : undefined,
          size: String(store.size),
        },
      })
    }
  } finally {
    isSearching.value = false
  }
}
</script>
