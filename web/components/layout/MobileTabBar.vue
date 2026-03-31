<template>
  <div class="d-md-none fixed-bottom bg-white border-top" style="padding-bottom: env(safe-area-inset-bottom)">
    <div class="d-flex justify-content-around py-2">
      <NuxtLink to="/" class="text-center text-decoration-none" :class="{ 'text-primary': route.path === '/' }">
        <i class="bi bi-search d-block fs-5"></i>
        <span class="d-block" style="font-size:0.7rem">搜索</span>
      </NuxtLink>
      <NuxtLink to="/favorites" class="text-center text-decoration-none position-relative" :class="{ 'text-primary': route.path === '/favorites' }">
        <i class="bi bi-heart d-block fs-5"></i>
        <span v-if="favorites.count > 0" class="position-absolute top-0 start-50 badge rounded-pill bg-danger" style="font-size:0.5rem; transform: translateX(50%)">
          {{ favorites.count }}
        </span>
        <span class="d-block" style="font-size:0.7rem">收藏</span>
      </NuxtLink>
      <NuxtLink to="/login" class="text-center text-decoration-none" :class="{ 'text-primary': route.path === '/login' }">
        <i class="bi bi-person d-block fs-5"></i>
        <span class="d-block" style="font-size:0.7rem">我的</span>
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const favorites = useFavoritesStore()
</script>
