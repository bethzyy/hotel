<template>
  <div class="comparison-section">
    <div class="section-title">
      <i class="bi bi-arrow-left-right"></i>
      多平台比价
    </div>

    <div v-if="loading" class="loading-text">
      <div class="spinner-border" role="status"></div>
      正在比价...
    </div>

    <div v-else-if="!comparisonData" class="text-muted" style="font-size:0.8rem">
      {{ errorMsg || '暂无比价数据' }}
    </div>

    <template v-else>
      <!-- Source price -->
      <div class="comparison-item" :class="{ best: isSourceBest }">
        <div>
          <span class="provider-name">{{ providerName(comparisonData.source.provider) }}</span>
        </div>
        <div class="d-flex align-items-center gap-2">
          <span v-if="comparisonData.source.price" class="provider-price">
            ¥{{ comparisonData.source.price }}
          </span>
          <span v-if="isSourceBest" class="best-badge">最低</span>
        </div>
      </div>

      <!-- Comparison prices -->
      <div
        v-for="comp in comparisonData.comparisons"
        :key="comp.provider"
        class="comparison-item"
        :class="{ best: isBestPrice(comp) }"
      >
        <div>
          <span class="provider-name">{{ providerName(comp.provider) }}</span>
        </div>
        <div class="d-flex align-items-center gap-2">
          <span v-if="comp.price" class="provider-price">
            {{ comp.currency === 'CNY' ? '¥' : comp.currency + ' ' }}{{ comp.price }}
          </span>
          <span v-if="isBestPrice(comp)" class="best-badge">最低</span>
          <a
            v-if="comp.url"
            :href="`/api/click/track?url=${encodeURIComponent(comp.url)}&hotel_id=${hotelId}&provider=${comp.provider}`"
            target="_blank"
            class="btn btn-sm btn-outline-primary py-0 px-2"
            style="font-size:0.7rem"
          >
            去看看
          </a>
        </div>
      </div>

      <!-- External platform prices -->
      <div
        v-for="ext in comparisonData.external_prices"
        :key="ext.platform"
        class="comparison-item"
      >
        <div class="d-flex align-items-center gap-1">
          <i v-if="ext.icon" :class="ext.icon" style="font-size:0.85rem"></i>
          <span class="provider-name">{{ ext.platform_name }}</span>
        </div>
        <div class="d-flex align-items-center gap-2">
          <span v-if="ext.price_cny" class="provider-price">
            ¥{{ Math.round(ext.price_cny) }}
          </span>
          <span v-else-if="ext.price" class="provider-price">
            {{ ext.currency === 'CNY' ? '¥' : ext.currency + ' ' }}{{ ext.price }}
          </span>
          <a
            v-if="ext.url"
            :href="`/api/click/track?url=${encodeURIComponent(ext.url)}&hotel_id=${hotelId}&provider=${ext.platform}`"
            target="_blank"
            class="btn btn-sm btn-outline-primary py-0 px-2"
            style="font-size:0.7rem"
          >
            去看看
          </a>
        </div>
      </div>

      <!-- Best price summary -->
      <div v-if="comparisonData.best_price?.save" class="mt-2 text-center" style="font-size:0.8rem">
        <span class="text-success fw-bold">
          最低价 ¥{{ comparisonData.best_price.price }}，比最高价省 ¥{{ comparisonData.best_price.save }}
        </span>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import type { ComparisonData } from '~/types/api'

const props = defineProps<{
  hotelId: string
  provider: string
  hotelName?: string
  checkIn?: string
  checkOut?: string
  sourcePrice?: number
  sourceCurrency?: string
}>()

const loading = ref(false)
const comparisonData = ref<ComparisonData | null>(null)
const errorMsg = ref('')

const providerNames: Record<string, string> = {
  rollinggo: 'RollingGo',
  tuniu: '途牛',
  booking: 'Booking.com',
  agoda: 'Agoda',
}

function providerName(id: string): string {
  return providerNames[id] || id
}

function isBestPrice(comp: { price?: number }): boolean {
  if (!comparisonData.value?.best_price || !comp.price) return false
  return comp.price === comparisonData.value.best_price.price
}

const isSourceBest = computed(() => {
  if (!comparisonData.value?.best_price || !props.sourcePrice) return false
  return props.sourcePrice === comparisonData.value.best_price.price
})

async function loadComparison() {
  loading.value = true
  errorMsg.value = ''
  const { get } = useApi()
  try {
    comparisonData.value = await get<ComparisonData>(`/compare/${props.provider}/${props.hotelId}`, {
      check_in: props.checkIn || '',
      check_out: props.checkOut || '',
      hotel_name: props.hotelName || '',
      adult_count: '2',
    })
  } catch (e: any) {
    comparisonData.value = null
    errorMsg.value = e?.message || '比价请求失败'
  } finally {
    loading.value = false
  }
}

watch(() => props.hotelId, () => loadComparison(), { immediate: true })
</script>
