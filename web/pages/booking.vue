<template>
  <div class="container py-4">
    <h4 class="mb-4"><i class="bi bi-calendar-check text-primary me-2"></i>预订酒店</h4>
    <div class="row g-4">
      <div class="col-lg-7">
        <div class="form-section">
          <h6 class="form-section-title"><i class="bi bi-person"></i>联系人信息</h6>
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label">姓名 <span class="text-danger">*</span></label>
              <input v-model="form.contactName" type="text" class="form-control" required>
            </div>
            <div class="col-md-6">
              <label class="form-label">手机号 <span class="text-danger">*</span></label>
              <input v-model="form.contactPhone" type="tel" class="form-control" required>
            </div>
          </div>
        </div>
        <div class="form-section">
          <h6 class="form-section-title"><i class="bi bi-people"></i>入住人信息</h6>
          <p class="text-muted mb-3" style="font-size:0.85rem">每间房需要填写入住人姓名</p>
          <div v-for="(room, idx) in form.rooms" :key="idx" class="room-guest-section mb-3">
            <h6 class="mb-2">房间 {{ idx + 1 }}: {{ room.roomName || `房型${idx + 1}` }}</h6>
            <div class="row g-2">
              <div class="col-md-6">
                <input v-model="room.guestName" type="text" class="form-control" placeholder="入住人姓名">
              </div>
              <div class="col-md-6">
                <input v-model="room.idCard" type="text" class="form-control" placeholder="身份证号">
              </div>
            </div>
          </div>
        </div>
        <button class="btn btn-primary btn-lg w-100 submit-btn" :disabled="submitting" @click="submit">
          <span v-if="submitting" class="spinner-border spinner-border-sm me-2"></span>
          确认预订
        </button>
      </div>
      <div class="col-lg-5">
        <div class="order-summary card">
          <div class="card-body">
            <h6 class="mb-3">订单摘要</h6>
            <p class="text-muted mb-1" style="font-size:0.85rem">酒店信息加载中...</p>
            <div v-if="bookingData" class="mt-3">
              <p class="fw-bold mb-1">{{ bookingData.hotel?.name }}</p>
              <p class="text-muted mb-2" style="font-size:0.85rem">{{ bookingData.hotel?.address }}</p>
              <div class="d-flex justify-content-between py-2 border-top">
                <span class="text-muted">入住</span>
                <span>{{ bookingData.checkIn }}</span>
              </div>
              <div class="d-flex justify-content-between py-2 border-top">
                <span class="text-muted">退房</span>
                <span>{{ bookingData.checkOut }}</span>
              </div>
              <div class="d-flex justify-content-between py-2 border-top">
                <span class="text-muted">晚数</span>
                <span>{{ bookingData.nights }} 晚</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const form = reactive({
  contactName: '',
  contactPhone: '',
  rooms: [] as { roomName: string; guestName: string; idCard: string }[],
})
const bookingData = ref<any>(null)
const submitting = ref(false)

onMounted(() => {
  if (import.meta.client) {
    const data = sessionStorage.getItem('bookingData')
    if (data) {
      try {
        bookingData.value = JSON.parse(data)
        const rooms = bookingData.value?.available_rooms || []
        form.rooms = rooms.map((r: any) => ({
          roomName: r.room_name || '',
          guestName: '',
          idCard: '',
        }))
      } catch { /* ignore */ }
    }
  }
})

async function submit() {
  submitting.value = true
  // Booking submission logic
  submitting.value = false
}
</script>
