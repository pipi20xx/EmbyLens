import { ref, watch } from 'vue'

const SAVE_KEY = 'embylens_current_view'

// 从本地存储恢复上次停留的页面，默认显示仪表盘
export const currentViewKey = ref(localStorage.getItem(SAVE_KEY) || 'DashboardView')

export const isLogConsoleOpen = ref(false)

// 监听变化并自动持久化
watch(currentViewKey, (val) => {
  localStorage.setItem(SAVE_KEY, val)
})