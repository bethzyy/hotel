<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <!-- Success -->
        <div v-if="orderData" class="text-center">
          <div class="order-success-icon">
            <i class="bi bi-check-lg"></i>
          </div>
          <h4>预订成功</h4>
          <p class="text-muted mb-4">订单已提交，请注意查收确认信息</p>
          <div class="card p-3 text-start mb-4">
            <div class="d-flex justify-content-between py-1">
              <span class="text-muted">订单号</span>
              <span class="fw-bold">{{ orderData.order_id }}</span>
            </div>
            <div class="d-flex justify-content-between py-1">
              <span class="text-muted">酒店</span>
              <span>{{ orderData.hotel_name }}</span>
            </div>
          </div>
          <NuxtLink to="/" class="btn btn-primary">返回首页</NuxtLink>
        </div>

        <!-- No data -->
        <div v-else class="text-center">
          <div class="empty-state-icon"><i class="bi bi-inbox"></i></div>
          <h4>暂无订单信息</h4>
          <NuxtLink to="/" class="btn btn-primary">去搜索</NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const orderData = ref<any>(null)

onMounted(() => {
  if (import.meta.client) {
    const data = sessionStorage.getItem('orderData')
    if (data) {
      try { orderData.value = JSON.parse(data) } catch { /* ignore */ }
    }
  }
})
</script>
