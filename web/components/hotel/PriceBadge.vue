<template>
  <div class="price-badge">
    <small v-if="perNight">每晚</small>
    {{ formattedPrice }}
    <small v-if="currency && currency !== 'CNY'">{{ currency }}</small>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatPrice } from '~/utils/currency'

const props = defineProps<{
  price?: number
  currency?: string
  perNight?: boolean
}>()

const formattedPrice = computed(() => formatPrice(props.price, props.currency))
</script>
