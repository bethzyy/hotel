<template>
  <nav class="navbar navbar-expand-lg">
    <div class="container">
      <NuxtLink to="/" class="navbar-brand">
        <i class="bi bi-building me-2"></i>
        {{ config.public.siteName }}
      </NuxtLink>
      <div class="d-flex align-items-center gap-3">
        <NuxtLink to="/favorites" class="nav-link text-white position-relative">
          <i class="bi bi-heart"></i>
          <span v-if="favorites.count > 0" class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger" style="font-size:0.6rem">
            {{ favorites.count }}
          </span>
        </NuxtLink>
        <NuxtLink v-if="!auth.isAuthenticated" to="/login" class="btn btn-outline-light btn-sm">
          <i class="bi bi-person me-1"></i>登录
        </NuxtLink>
        <button v-else class="btn btn-outline-light btn-sm" @click="auth.logout()">
          <i class="bi bi-box-arrow-right me-1"></i>退出
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const auth = useAuthStore()
const favorites = useFavoritesStore()

onMounted(() => {
  favorites.loadCount()
})
</script>
