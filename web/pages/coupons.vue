<template>
  <div class="container py-4">
    <h4 class="mb-4">
      <i class="bi bi-ticket-perforated me-2"></i>优惠券
    </h4>

    <!-- Available Coupons -->
    <h5 class="mb-3">可领取</h5>
    <div v-if="availableCoupons.length === 0" class="text-center py-3 text-muted">
      暂无可领取的优惠券
    </div>
    <div v-else class="row g-2 mb-4">
      <div v-for="coupon in availableCoupons" :key="coupon.id" class="col-md-4">
        <div class="card border-success">
          <div class="card-body">
            <h6 class="mb-1">{{ coupon.name }}</h6>
            <div class="text-success fw-bold">
              <span v-if="coupon.discount_type === 'percentage'">{{ coupon.discount_value }}% OFF</span>
              <span v-else>{{ coupon.discount_value }} 天</span>
            </div>
            <div v-if="coupon.valid_until" class="text-muted small">
              有效期至 {{ formatDate(coupon.valid_until) }}
            </div>
            <button class="btn btn-sm btn-outline-success mt-2 w-100" @click="claimCoupon(coupon.id)">
              领取
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- My Coupons -->
    <h5 class="mb-3">我的优惠券</h5>
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <button class="nav-link" :class="{ active: tab === 'unused' }" @click="tab = 'unused'">
          未使用 ({{ myCoupons.filter(c => c.status === 'unused').length }})
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: tab === 'used' }" @click="tab = 'used'">已使用</button>
      </li>
    </ul>

    <div v-if="filteredCoupons.length === 0" class="text-center py-3 text-muted">
      暂无{{ tab === 'unused' ? '可用' : '' }}优惠券
    </div>
    <div v-else class="d-flex flex-column gap-2">
      <div v-for="uc in filteredCoupons" :key="uc.id" class="card">
        <div class="card-body py-2 d-flex justify-content-between align-items-center">
          <div>
            <strong>{{ uc.coupon?.name }}</strong>
            <span class="badge ms-2" :class="uc.status === 'unused' ? 'bg-success' : 'bg-secondary'">
              {{ uc.status === 'unused' ? '未使用' : '已使用' }}
            </span>
          </div>
          <div class="text-muted small">
            {{ formatDate(uc.received_at) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Coupon {
  id: number
  code: string
  name: string
  discount_type: string
  discount_value: number
  valid_until?: string
  is_valid: boolean
}

interface UserCoupon {
  id: number
  coupon: Coupon | null
  status: string
  received_at?: string
  used_at?: string
}

const { get, post } = useApi()

const availableCoupons = ref<Coupon[]>([])
const myCoupons = ref<UserCoupon[]>([])
const tab = ref('unused')

const filteredCoupons = computed(() => myCoupons.value.filter(c => c.status === tab.value))

onMounted(async () => {
  await Promise.all([loadAvailable(), loadMine()])
})

async function loadAvailable() {
  try {
    const data = await get<{ coupons: Coupon[] }>('/coupons/available')
    availableCoupons.value = data.coupons || []
  } catch { /* ignore */ }
}

async function loadMine() {
  try {
    const data = await get<{ coupons: UserCoupon[] }>('/coupons/mine')
    myCoupons.value = data.coupons || []
  } catch { /* ignore */ }
}

async function claimCoupon(id: number) {
  try {
    await post(`/coupons/${id}/claim`)
    await Promise.all([loadAvailable(), loadMine()])
  } catch (e: any) {
    alert(e.message || '领取失败')
  }
}

function formatDate(dateStr: string | undefined) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>
