<template>
  <div class="container py-4">
    <h4 class="mb-4">
      <i class="bi bi-bell me-2"></i>价格提醒
    </h4>

    <div v-if="!membership.isMember" class="alert alert-info">
      <i class="bi bi-info-circle me-2"></i>
      价格提醒是会员专属功能，<NuxtLink to="/membership">升级会员</NuxtLink> 即可使用
    </div>

    <!-- Create Alert -->
    <div v-if="membership.isMember" class="card mb-4">
      <div class="card-body">
        <h6 class="mb-3">设置价格提醒</h6>
        <div class="row g-2">
          <div class="col-md-4">
            <select v-model="newAlert.hotel_id" class="form-select">
              <option value="">选择收藏的酒店</option>
              <option v-for="fav in favorites" :key="fav.hotel_id" :value="fav.hotel_id">
                {{ fav.hotel_name || fav.hotel_id }}
              </option>
            </select>
          </div>
          <div class="col-md-3">
            <input v-model.number="newAlert.target_price" type="number" class="form-control"
              placeholder="目标价格（元/晚）">
          </div>
          <div class="col-md-3 d-flex gap-2">
            <input v-model="newAlert.check_in" type="date" class="form-control" placeholder="入住日期">
          </div>
          <div class="col-md-2">
            <button class="btn btn-primary w-100" @click="createAlert" :disabled="!canCreateAlert">
              <i class="bi bi-plus me-1"></i>添加
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Alert List -->
    <div v-if="alerts.length === 0" class="text-center py-5 text-muted">
      <i class="bi bi-bell-slash" style="font-size:2rem"></i>
      <p class="mt-2">暂无价格提醒</p>
    </div>

    <div v-else class="d-flex flex-column gap-2">
      <div v-for="alert in alerts" :key="alert.id" class="card">
        <div class="card-body d-flex justify-content-between align-items-center py-2">
          <div>
            <strong>{{ alert.hotel_name || alert.hotel_id }}</strong>
            <span class="badge bg-light ms-2">{{ alert.provider }}</span>
            <div class="text-muted small">
              目标价格: ¥{{ alert.target_price }}
              <span v-if="alert.current_price"> · 当前: ¥{{ alert.current_price }}</span>
            </div>
          </div>
          <div class="d-flex align-items-center gap-2">
            <span v-if="alert.triggered_at" class="badge bg-success">已触发</span>
            <span v-else-if="alert.is_active" class="badge bg-warning text-dark">监控中</span>
            <button v-if="alert.is_active" class="btn btn-sm btn-outline-danger" @click="deleteAlert(alert.id)">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface PriceAlert {
  id: number
  hotel_id: string
  hotel_name?: string
  provider: string
  target_price: number
  current_price?: number
  is_active: boolean
  triggered_at?: string
  check_in?: string
}

const membership = useMembershipStore()
const { get, post, del } = useApi()

const alerts = ref<PriceAlert[]>([])
const favorites = ref<{ hotel_id: string; hotel_name: string }[]>([])

const newAlert = ref({
  hotel_id: '',
  target_price: 0,
  check_in: '',
})

const canCreateAlert = computed(() => newAlert.value.hotel_id && newAlert.value.target_price > 0)

onMounted(async () => {
  await membership.fetchInfo()
  if (membership.isMember) {
    await loadAlerts()
    loadFavorites()
  }
})

async function loadAlerts() {
  try {
    const data = await get<{ alerts: PriceAlert[] }>('/alerts')
    alerts.value = data.alerts || []
  } catch { /* ignore */ }
}

async function loadFavorites() {
  try {
    const data = await get<{ favorites: any[] }>('/favorites')
    favorites.value = (data.favorites || []).map(f => ({
      hotel_id: f.hotel_id,
      hotel_name: f.hotel_name || f.name,
    }))
  } catch { /* ignore */ }
}

async function createAlert() {
  if (!canCreateAlert.value) return
  try {
    const fav = favorites.value.find(f => f.hotel_id === newAlert.value.hotel_id)
    await post('/alerts', {
      hotel_id: newAlert.value.hotel_id,
      hotel_name: fav?.hotel_name,
      provider: 'tuniu',
      target_price: newAlert.value.target_price * 100, // Convert to cents
      check_in: newAlert.value.check_in,
    })
    newAlert.value = { hotel_id: '', target_price: 0, check_in: '' }
    await loadAlerts()
  } catch (e: any) {
    alert(e.message || '创建提醒失败')
  }
}

async function deleteAlert(id: number) {
  try {
    await del(`/alerts/${id}`)
    await loadAlerts()
  } catch { /* ignore */ }
}
</script>
