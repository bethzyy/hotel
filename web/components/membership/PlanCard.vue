<template>
  <div class="card h-100" :class="{ 'border-warning': plan.id === 'yearly' }">
    <div v-if="plan.id === 'yearly'" class="position-absolute top-0 end-0 m-2">
      <span class="badge bg-warning text-dark">推荐</span>
    </div>
    <div class="card-body d-flex flex-column">
      <h6 class="card-title">{{ plan.name }}</h6>
      <div class="mb-3">
        <span class="fs-3 fw-bold">¥{{ plan.price }}</span>
        <span class="text-muted">/{{ plan.id === 'monthly' ? '月' : '年' }}</span>
        <span v-if="plan.id === 'yearly'" class="badge bg-light text-success ms-2">省 ¥40</span>
      </div>
      <ul class="list-unstyled mb-3 flex-grow-1">
        <li v-for="feature in plan.features" :key="feature" class="mb-1">
          <i class="bi bi-check-circle text-success me-1"></i>{{ feature }}
        </li>
      </ul>
      <button class="btn" :class="plan.id === 'yearly' ? 'btn-warning' : 'btn-outline-primary'" @click="$emit('select', plan)">
        立即开通
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PaymentPlan } from '~/types/api'

defineProps<{
  plan: PaymentPlan
}>()

defineEmits<{
  select: [plan: PaymentPlan]
}>()
</script>
