<template>
  <div v-if="visible" class="modal d-block" tabindex="-1" style="background:rgba(0,0,0,0.5)">
    <div class="modal-dialog modal-dialog-centered modal-sm">
      <div class="modal-content">
        <div class="modal-body text-center p-4">
          <i class="bi bi-gem text-warning" style="font-size:2.5rem"></i>
          <h5 class="mt-3 mb-2">升级会员</h5>
          <p class="text-muted mb-3">{{ message }}</p>
          <div class="d-grid gap-2">
            <NuxtLink to="/membership" class="btn btn-warning" @click="visible = false">
              查看会员方案
            </NuxtLink>
            <button class="btn btn-outline-secondary btn-sm" @click="visible = false">
              稍后再说
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const visible = ref(false)

defineProps<{
  message?: string
}>()

function show() {
  visible.value = true
}

defineExpose({ show })
</script>
