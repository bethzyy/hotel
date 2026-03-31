<template>
  <div class="container py-4">
    <h4 class="mb-4"><i class="bi bi-heart text-danger me-2"></i>我的收藏</h4>

    <div v-if="pending" class="text-center py-5">
      <div class="spinner-border" role="status"></div>
    </div>

    <div v-else-if="items.length === 0" class="empty-state">
      <div class="empty-state-icon"><i class="bi bi-heart"></i></div>
      <h4>暂无收藏</h4>
      <p>搜索酒店时点击心形按钮即可收藏</p>
      <NuxtLink to="/" class="btn btn-primary">去搜索</NuxtLink>
    </div>

    <div v-else class="d-flex flex-column gap-3">
      <div
        v-for="item in items"
        :key="item.id"
        class="card p-3"
      >
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <h6 class="mb-1">{{ item.hotel_name || item.hotel_id }}</h6>
            <small class="text-muted">
              {{ item.provider }} · {{ formatDate(item.created_at) }}
            </small>
          </div>
          <div class="d-flex gap-2">
            <NuxtLink
              :to="`/detail/${item.hotel_id}?provider=${item.provider}`"
              class="btn btn-sm btn-outline-primary"
            >
              查看
            </NuxtLink>
            <button class="btn btn-sm btn-outline-danger" @click="remove(item.hotel_id)">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Favorite } from '~/types/api'

const favorites = useFavoritesStore()
const pending = ref(true)
const items = ref<Favorite[]>([])

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

async function loadFavorites() {
  pending.value = true
  try {
    await favorites.loadAll()
    items.value = favorites.items
  } finally {
    pending.value = false
  }
}

async function remove(hotelId: string) {
  await favorites.remove(hotelId)
  items.value = favorites.items
}

onMounted(loadFavorites)
</script>
