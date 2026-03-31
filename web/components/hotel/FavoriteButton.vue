<template>
  <button
    class="btn favorite-btn position-absolute top-0 end-0 m-2 z-1"
    :class="isFavorite ? 'btn-danger active' : 'btn-outline-danger'"
    @click.stop="toggle"
    :title="isFavorite ? '取消收藏' : '收藏'"
  >
    <i :class="isFavorite ? 'bi bi-heart-fill' : 'bi bi-heart'"></i>
  </button>
</template>

<script setup lang="ts">
const props = defineProps<{
  hotelId: string
  hotelName?: string
  provider?: string
  isFavorite?: boolean
}>()

const isFavorite = ref(props.isFavorite || false)

async function toggle() {
  const store = useFavoritesStore()
  try {
    const result = await store.toggle(props.hotelId, {
      name: props.hotelName,
      provider: props.provider,
    })
    isFavorite.value = result.is_favorite
  } catch { /* ignore */ }
}
</script>
