<template>
  <div class="hotel-image-wrapper">
    <div class="hotel-image">
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
import { ref } from 'vue'

const props = defineProps<{
  src?: string
  alt?: string
}>()

const imgError = ref(false)
</script>
