<template>
  <div class="mt-4 text-center">
    <small class="text-muted">最近搜索</small>
    <div class="d-flex flex-wrap justify-content-center gap-2 mt-2">
      <span
        v-for="(item, idx) in items" :key="idx"
        class="badge rounded-pill" style="cursor:pointer; padding:6px 14px; font-size:0.85rem; background:var(--gray-100); color:var(--gray-700)"
        @click="$emit('select', item)"
      >
        <i class="bi bi-clock-history me-1"></i>{{ item.place || item.query }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  items: { query: string; place: string; provider: string }[]
}>()

defineEmits<{
  select: [item: { query: string; place: string; provider: string }]
}>()
</script>
