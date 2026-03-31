<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-md-5">
        <div class="card">
          <div class="card-body p-4">
            <h4 class="text-center mb-4">
              <i class="bi bi-person-circle text-primary me-2"></i>手机号登录
            </h4>

            <!-- Phone Input -->
            <div class="mb-3">
              <label class="form-label">手机号</label>
              <input
                v-model="phone"
                type="tel"
                class="form-control"
                placeholder="请输入手机号"
                maxlength="11"
                @input="phone = phone.replace(/\D/g, '')"
              >
            </div>

            <!-- Verification Code -->
            <div class="mb-3">
              <label class="form-label">验证码</label>
              <div class="input-group">
                <input
                  v-model="code"
                  type="text"
                  class="form-control"
                  placeholder="请输入验证码"
                  maxlength="6"
                >
                <button
                  class="btn btn-outline-primary"
                  :disabled="countdown > 0 || !phone"
                  @click="sendCode"
                >
                  {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
                </button>
              </div>
            </div>

            <!-- Error -->
            <div v-if="errorMsg" class="alert alert-danger py-2" style="font-size:0.85rem">
              {{ errorMsg }}
            </div>

            <!-- Submit -->
            <button class="btn btn-primary w-100" :disabled="!phone || !code || isLoading" @click="login">
              <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
              登录
            </button>

            <p class="text-center text-muted mt-3 mb-0" style="font-size:0.8rem">
              未注册手机号将自动创建账号
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const phone = ref('')
const code = ref('')
const countdown = ref(0)
const isLoading = ref(false)
const errorMsg = ref('')
const auth = useAuthStore()

let countdownTimer: ReturnType<typeof setInterval> | null = null

async function sendCode() {
  if (countdown.value > 0 || !phone.value) return
  errorMsg.value = ''
  try {
    await auth.sendCode(phone.value)
    countdown.value = 60
    countdownTimer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0 && countdownTimer) {
        clearInterval(countdownTimer)
        countdownTimer = null
      }
    }, 1000)
  } catch (e: any) {
    errorMsg.value = e.message || '发送失败'
  }
}

async function login() {
  if (!phone.value || !code.value) return
  isLoading.value = true
  errorMsg.value = ''
  try {
    await auth.login(phone.value, code.value)
    navigateTo('/')
  } catch (e: any) {
    errorMsg.value = e.message || '登录失败'
  } finally {
    isLoading.value = false
  }
}

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>
