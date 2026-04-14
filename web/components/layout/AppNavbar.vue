<template>
  <nav class="navbar navbar-expand-lg">
    <div class="container">
      <NuxtLink to="/" class="navbar-brand">
        <i class="bi bi-building me-2"></i>
        {{ config.public.siteName }}
      </NuxtLink>
      <div class="d-flex align-items-center gap-3">
        <NuxtLink v-if="membership.isMember" to="/membership" class="nav-link" title="会员中心">
          <i class="bi bi-gem text-warning"></i>
        </NuxtLink>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const membership = useMembershipStore()

onMounted(() => {
  membership.fetchInfo()
})
</script>
