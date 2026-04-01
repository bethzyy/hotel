<template>
  <div v-if="membership.loaded && !membership.isUnlimited" class="alert d-flex align-items-center py-2 px-3 mb-3"
    :class="membership.canSearch ? 'alert-light' : 'alert-warning'" style="font-size:0.85rem">
    <i :class="membership.canSearch ? 'bi bi-info-circle text-primary' : 'bi bi-exclamation-triangle text-warning'" class="me-2"></i>
    <span v-if="membership.canSearch">
      今日剩余搜索 <strong>{{ membership.searchRemaining }}</strong> 次
      <a href="/membership" class="ms-2 text-decoration-none">升级会员</a>
    </span>
    <span v-else>
      今日搜索次数已用完，<a href="/membership" class="fw-bold text-decoration-none">升级会员</a> 享无限搜索
    </span>
  </div>
</template>

<script setup lang="ts">
const membership = useMembershipStore()

onMounted(() => {
  membership.fetchInfo()
})
</script>
