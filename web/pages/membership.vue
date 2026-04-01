<template>
  <div class="container py-4">
    <h4 class="mb-4">
      <i class="bi bi-gem me-2"></i>会员中心
    </h4>

    <!-- Current Status -->
    <div class="card mb-4">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <h5 class="mb-1">
              {{ membership.isMember ? '👑 ' : '' }}{{ membership.tierLabel }}
            </h5>
            <p v-if="membership.isMember" class="text-muted mb-0">
              有效期至 {{ formatDate(membership.expiresAt) }}
            </p>
            <p v-else class="text-muted mb-0">
              今日剩余搜索 <strong>{{ membership.searchRemaining }}</strong> 次
            </p>
          </div>
          <div v-if="membership.isMember" class="badge bg-warning text-dark" style="font-size:1rem; padding:0.5em 1em">
            VIP
          </div>
        </div>
      </div>
    </div>

    <!-- Plans -->
    <h5 class="mb-3">升级会员</h5>
    <div class="row g-3 mb-4">
      <div v-for="plan in membership.plans" :key="plan.id" class="col-md-6">
        <PlanCard :plan="plan" @select="handleSubscribe" />
      </div>
    </div>

    <!-- Benefits -->
    <div class="card">
      <div class="card-header">
        <i class="bi bi-list-check"></i>会员权益对比
      </div>
      <div class="card-body">
        <table class="table table-borderless mb-0">
          <thead>
            <tr>
              <th>权益</th>
              <th class="text-center">免费</th>
              <th class="text-center text-warning">会员</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>每日搜索次数</td><td class="text-center">10 次</td><td class="text-center">无限</td></tr>
            <tr><td>跨平台比价</td><td class="text-center"><i class="bi bi-check text-success"></i></td><td class="text-center"><i class="bi bi-check text-success"></i></td></tr>
            <tr><td>价格变动提醒</td><td class="text-center text-muted">-</td><td class="text-center"><i class="bi bi-check text-success"></i></td></tr>
            <tr><td>历史价格分析</td><td class="text-center text-muted">-</td><td class="text-center"><i class="bi bi-check text-success"></i></td></tr>
            <tr><td>优先客服支持</td><td class="text-center text-muted">-</td><td class="text-center"><i class="bi bi-check text-success"></i></td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Upgrade Modal -->
    <div v-if="showPayModal" class="modal d-block" tabindex="-1" style="background:rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">确认支付</h5>
            <button type="button" class="btn-close" @click="showPayModal = false"></button>
          </div>
          <div class="modal-body text-center">
            <p class="mb-2"> {{ selectedPlan?.name }}</p>
            <p class="fs-2 fw-bold text-primary mb-3">¥{{ selectedPlan?.price }}</p>
            <div class="d-grid gap-2">
              <button class="btn btn-success" @click="handlePay('wechat')">
                <i class="bi bi-wechat me-2"></i>微信支付
              </button>
              <button class="btn btn-primary" @click="handlePay('alipay')">
                <i class="bi bi-alipay me-2"></i>支付宝
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PaymentPlan } from '~/types/api'

const membership = useMembershipStore()
const auth = useAuthStore()
const { post } = useApi()

const showPayModal = ref(false)
const selectedPlan = ref<PaymentPlan | null>(null)
const paying = ref(false)

onMounted(async () => {
  await Promise.all([membership.fetchInfo(), membership.fetchPlans()])
})

function formatDate(dateStr: string | null) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function handleSubscribe(plan: PaymentPlan) {
  if (!auth.isAuthenticated) {
    navigateTo('/login')
    return
  }
  selectedPlan.value = plan
  showPayModal.value = true
}

async function handlePay(provider: string) {
  if (!selectedPlan.value || paying.value) return
  paying.value = true
  try {
    const data = await post<{ subscription_id: number; payment_url: string }>(
      '/payment/create',
      { plan: selectedPlan.value.id, payment_provider: provider }
    )
    // In debug mode, use mock payment endpoint
    if (import.meta.client && window.location.hostname === 'localhost') {
      await $fetch(`/api/payment/mock/${provider}/${data.subscription_id}`, {
        headers: { Authorization: `Bearer ${auth.token}` },
      })
      await membership.fetchInfo()
      showPayModal.value = false
    } else {
      // Redirect to payment page
      window.location.href = data.payment_url
    }
  } catch (e: any) {
    alert(e.message || '创建支付订单失败')
  } finally {
    paying.value = false
  }
}
</script>
