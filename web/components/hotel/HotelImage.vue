<template>
  <div class="hotel-image-wrapper">
    <div class="hotel-image" :style="bgStyle">
      <img
        v-if="src && !imgError"
        :src="src"
        :alt="alt"
        loading="lazy"
        @error="imgError = true"
      >
      <div v-if="!src || imgError" class="d-flex align-items-center justify-content-center h-100">
        <i class="bi bi-image text-muted" style="font-size:2rem"></i>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  src?: string
  alt?: string
}>()

const imgError = ref(false)

const bgStyle = computed(() => {
  if (!props.src || imgError.value) return {}
  return { backgroundImage: `url(${props.src})` }
})
</script>
