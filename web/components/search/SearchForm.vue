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
            :class="{ selected: form.provider === p.id }"
            @click="form.provider = p.id"
          >
            <input type="radio" :id="p.id" :value="p.id" v-model="form.provider" class="d-none">
            <label :for="p.id" class="mb-0 fw-medium" style="cursor:pointer">
              {{ p.name }}
            </label>
            <div style="font-size:0.75rem" class="text-muted">{{ p.description }}</div>
          </div>
        </div>

        <!-- Tuniu: City + Date Range -->
        <template v-if="form.provider === 'tuniu'">
          <div class="row g-3 mb-3">
            <div class="col-md-4">
              <label class="form-label small text-muted">城市</label>
              <input v-model="form.cityName" type="text" class="form-control" placeholder="输入城市名称" required>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">入住日期</label>
              <input v-model="form.checkIn" type="date" class="form-control" required>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">退房日期</label>
              <input v-model="form.checkOut" type="date" class="form-control" required>
            </div>
          </div>
          <div class="row g-3 mb-3">
            <div class="col-md-4">
              <label class="form-label small text-muted">成人数</label>
              <div class="input-group">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('adultCount', -1)">-</button>
                <input v-model.number="form.adultCount" type="number" class="form-control text-center" min="1" max="10">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('adultCount', 1)">+</button>
              </div>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">儿童数</label>
              <div class="input-group">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('childCount', -1)">-</button>
                <input v-model.number="form.childCount" type="number" class="form-control text-center" min="0" max="10">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('childCount', 1)">+</button>
              </div>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">关键词（可选）</label>
              <input v-model="form.keyword" type="text" class="form-control" placeholder="酒店名/品牌">
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
              <input v-model="form.place" type="text" class="form-control border-start-0" placeholder="输入目的地（景点、城市、机场、酒店...）" required>
            </div>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-md-4">
              <label class="form-label small text-muted">地点类型</label>
              <select v-model="form.placeType" class="form-select" required>
                <option value="">选择类型...</option>
                <option v-for="pt in placeTypes" :key="pt" :value="pt">{{ pt }}</option>
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">入住日期</label>
              <input v-model="form.checkInDate" type="date" class="form-control">
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">住宿晚数</label>
              <div class="input-group">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('stayNights', -1)">-</button>
                <input v-model.number="form.stayNights" type="number" class="form-control text-center" min="1" max="30">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('stayNights', 1)">+</button>
              </div>
            </div>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-md-6">
              <label class="form-label small text-muted">成人数</label>
              <div class="input-group">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('adultCount', -1)">-</button>
                <input v-model.number="form.adultCount" type="number" class="form-control text-center" min="1" max="10">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('adultCount', 1)">+</button>
              </div>
            </div>
            <div class="col-md-6">
              <label class="form-label small text-muted">儿童数</label>
              <div class="input-group">
                <button type="button" class="btn btn-outline-secondary" @click="adjustCount('childCount', -1)">-</button>
                <input v-model.number="form.childCount" type="number" class="form-control text-center" min="0" max="10">
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
              <select v-model="form.minStar" class="form-select">
                <option value="">不限</option>
                <option value="3">3星</option>
                <option value="4">4星</option>
                <option value="5">5星</option>
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">最高价格/晚</label>
              <input v-model.number="form.maxPrice" type="number" class="form-control" placeholder="不限">
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted">搜索结果数</label>
              <select v-model="form.size" class="form-select">
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
const providers = [
  { id: 'rollinggo', name: '全球酒店', description: 'RollingGo · 全球搜索' },
  { id: 'tuniu', name: '国内酒店', description: '途牛 · 国内预订' },
]

const placeTypes = ['景点', '城市', '机场', '火车站', '地铁站', '酒店', '区/县', '详细地址']

const form = reactive({
  provider: 'tuniu',
  // Tuniu
  cityName: '',
  checkIn: '',
  checkOut: '',
  keyword: '',
  // RollingGo
  place: '',
  placeType: '',
  checkInDate: '',
  stayNights: 1,
  // Common
  adultCount: 2,
  childCount: 0,
  // Advanced
  minStar: '',
  maxPrice: undefined as number | undefined,
  size: 20,
})

const showAdvanced = ref(false)
const isSearching = ref(false)
const history = ref<{ query: string; place: string; provider: string }[]>([])

// Set default dates
onMounted(() => {
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  const dayAfter = new Date(today)
  dayAfter.setDate(dayAfter.getDate() + 2)
  form.checkIn = formatDate(tomorrow)
  form.checkOut = formatDate(dayAfter)
  form.checkInDate = formatDate(tomorrow)

  // Load search history
  loadHistory()
})

function formatDate(d: Date): string {
  return d.toISOString().split('T')[0]
}

function adjustCount(field: string, delta: number) {
  const val = (form as any)[field] as number
  const min = field === 'adultCount' ? 1 : field === 'stayNights' ? 1 : 0
  const max = field === 'stayNights' ? 30 : 10
  ;(form as any)[field] = Math.min(max, Math.max(min, val + delta))
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
    form.provider = 'tuniu'
    form.cityName = item.place || item.query
  } else {
    form.provider = 'rollinggo'
    form.place = item.place || item.query
  }
}

async function handleSearch() {
  isSearching.value = true
  try {
    // Save to search history
    const { post } = useApi()
    post('/history', {
      query: form.provider === 'tuniu' ? form.cityName : form.place,
      place: form.provider === 'tuniu' ? form.cityName : form.place,
      place_type: form.provider === 'rollinggo' ? form.placeType : '城市',
      provider: form.provider,
    }).catch(() => {})

    // Navigate to results
    if (form.provider === 'tuniu') {
      await navigateTo({
        path: '/results',
        query: {
          provider: 'tuniu',
          city_name: form.cityName,
          check_in: form.checkIn,
          check_out: form.checkOut,
          adult_count: String(form.adultCount),
          child_count: String(form.childCount),
          keyword: form.keyword || undefined,
        },
      })
    } else {
      await navigateTo({
        path: '/results',
        query: {
          provider: 'rollinggo',
          place: form.place,
          place_type: form.placeType,
          check_in_date: form.checkInDate,
          stay_nights: String(form.stayNights),
          adult_count: String(form.adultCount),
          child_count: String(form.childCount),
          min_star: form.minStar || undefined,
          max_price: form.maxPrice ? String(form.maxPrice) : undefined,
          size: String(form.size),
        },
      })
    }
  } finally {
    isSearching.value = false
  }
}
</script>
