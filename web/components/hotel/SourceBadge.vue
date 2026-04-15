<template>
  <span v-if="label" class="badge" :class="badgeClass" style="font-size:0.65rem">
    <i :class="icon" class="me-1"></i>{{ label }}
  </span>
</template>

<script setup lang="ts">
const props = defineProps<{
  sources?: string[]
  provider?: string
}>()

const label = computed(() => {
  if (props.sources?.length === 2) return '双源'
  if (props.provider === 'tuniu') return '途牛'
  if (props.provider === 'rollinggo') return '全球'
  return ''
})

const badgeClass = computed(() => {
  if (props.sources?.length === 2) return 'bg-info bg-opacity-10 text-info'
  if (props.provider === 'tuniu') return 'bg-primary bg-opacity-10 text-primary'
  if (props.provider === 'rollinggo') return 'bg-success bg-opacity-10 text-success'
  return 'bg-secondary bg-opacity-10 text-secondary'
})

const icon = computed(() => {
  if (props.sources?.length === 2) return 'bi bi-link-45deg'
  if (props.provider === 'tuniu') return 'bi bi-house-check'
  if (props.provider === 'rollinggo') return 'bi bi-globe2'
  return 'bi bi-building'
})
</script>
