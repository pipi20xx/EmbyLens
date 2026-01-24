<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'

const props = defineProps<{
  textColor?: string
  alignment?: string
}>()

const currentTime = ref(new Date())
let timer: any = null

const updateTime = () => {
  currentTime.value = new Date()
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const timeStr = computed(() => {
  const h = String(currentTime.value.getHours()).padStart(2, '0')
  const m = String(currentTime.value.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
})

const secondsStr = computed(() => {
  return String(currentTime.value.getSeconds()).padStart(2, '0')
})

const dateStr = computed(() => {
  const options: Intl.DateTimeFormatOptions = { 
    month: 'long', 
    day: 'numeric', 
    weekday: 'short' 
  }
  return currentTime.value.toLocaleDateString('zh-CN', options)
})
</script>

<template>
  <div class="nav-clock" :style="{ 
    alignItems: alignment === 'center' ? 'center' : (alignment === 'right' ? 'flex-end' : 'flex-start') 
  }">
    <div class="time-wrapper" :style="{ color: textColor || '#fff' }">
      <span class="main-time">{{ timeStr }}</span>
      <span class="seconds">{{ secondsStr }}</span>
    </div>
    <div class="date-wrapper" :style="{ color: textColor || '#fff', opacity: 0.8 }">
      {{ dateStr }}
    </div>
  </div>
</template>

<style scoped>
.nav-clock {
  display: flex;
  flex-direction: column;
  margin-bottom: 8px;
  font-family: var(--font-mono);
  user-select: none;
}

.time-wrapper {
  display: flex;
  align-items: baseline;
  line-height: 1;
}

.main-time {
  font-size: 48px;
  font-weight: 700;
  letter-spacing: -2px;
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.seconds {
  font-size: 20px;
  margin-left: 6px;
  font-weight: 400;
  opacity: 0.8;
}

.date-wrapper {
  font-size: 14px;
  margin-top: 4px;
  font-weight: 500;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}
</style>
