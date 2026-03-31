<template>
  <div>
    <AppNavbar />
    <main style="min-height: calc(100vh - 56px - 48px); padding-bottom: 70px;">
      <slot />
    </main>
    <footer class="py-3 text-center" style="font-size:0.8rem; color: var(--gray-500)">
      <p class="mb-0">&copy; {{ new Date().getFullYear() }} 酒店搜索比价 · 仅供参考，请以平台实时价格为准</p>
    </footer>
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
const auth = useAuthStore()
auth.init()

onMounted(() => {
  auth.checkAuth()
})
</script>
