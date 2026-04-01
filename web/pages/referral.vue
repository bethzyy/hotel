<template>
  <div class="container py-4">
    <h4 class="mb-4">
      <i class="bi bi-people me-2"></i>邀请好友
    </h4>

    <!-- My Referral Code -->
    <div class="card mb-4 text-center">
      <div class="card-body py-4">
        <p class="text-muted mb-2">我的推荐码</p>
        <div class="d-flex justify-content-center align-items-center gap-2 mb-2">
          <span class="fs-2 fw-bold font-monospace">{{ referralCode }}</span>
          <button class="btn btn-outline-primary btn-sm" @click="copyCode">
            <i class="bi bi-clipboard"></i>
          </button>
        </div>
        <p class="text-muted small">
          邀请好友注册，双方各获得 <strong>{{ rewardDays }}</strong> 天会员
        </p>
      </div>
    </div>

    <!-- Share -->
    <div class="card mb-4">
      <div class="card-body">
        <h6 class="mb-3">分享给好友</h6>
        <div class="d-grid gap-2 d-md-flex">
          <input :value="shareLink" class="form-control" readonly @click="($event.target as HTMLInputElement).select()">
          <button class="btn btn-primary" @click="copyLink">复制链接</button>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="row g-3 mb-4">
      <div class="col-6">
        <div class="card text-center p-3">
          <div class="fs-2 fw-bold">{{ totalReferrals }}</div>
          <div class="text-muted small">邀请人数</div>
        </div>
      </div>
      <div class="col-6">
        <div class="card text-center p-3">
          <div class="fs-2 fw-bold text-success">{{ totalReferrals * rewardDays }}</div>
          <div class="text-muted small">获得天数</div>
        </div>
      </div>
    </div>

    <!-- Records -->
    <h5 class="mb-3">邀请记录</h5>
    <div v-if="records.length === 0" class="text-center py-4 text-muted">
      暂无邀请记录
    </div>
    <div v-else class="list-group">
      <div v-for="record in records" :key="record.id" class="list-group-item d-flex justify-content-between">
        <span>用户 {{ record.referred_id }}</span>
        <span class="text-muted small">{{ formatDate(record.created_at) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { get } = useApi()

const referralCode = ref('')
const totalReferrals = ref(0)
const rewardDays = ref(7)
const records = ref<{ id: number; referred_id: number; created_at: string }[]>([])

const shareLink = computed(() => {
  if (!import.meta.client) return ''
  return `${window.location.origin}/login?ref=${referralCode.value}`
})

onMounted(async () => {
  await loadReferralInfo()
})

async function loadReferralInfo() {
  try {
    const data = await get<{ code: string; total_referrals: number; reward_days: number }>('/referral/code')
    referralCode.value = data.code
    totalReferrals.value = data.total_referrals
    rewardDays.value = data.reward_days

    const recordsData = await get<{ records: any[] }>('/referral/records')
    records.value = recordsData.records || []
  } catch { /* ignore */ }
}

function copyCode() {
  navigator.clipboard.writeText(referralCode.value)
}

function copyLink() {
  navigator.clipboard.writeText(shareLink.value)
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>
