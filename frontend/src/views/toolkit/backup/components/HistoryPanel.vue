<template>
  <n-card size="small" segmented title="执行历史">
    <template #header-extra>
      <n-button size="small" @click="fetchHistory">刷新</n-button>
    </template>
    <n-data-table
      :columns="historyColumns"
      :data="history"
      :loading="loading"
      size="small"
      pagination
    />
  </n-card>
</template>

<script setup lang="ts">
import { ref, h, onMounted, onUnmounted } from 'vue'
import { NCard, NDataTable, NTag, NButton } from 'naive-ui'
import axios from 'axios'

const history = ref([])
const loading = ref(false)
let timer: any = null

const historyColumns = [
  { title: '开始时间', key: 'start_time', width: 180, render: (row) => new Date(row.start_time).toLocaleString() },
  { title: '任务', key: 'task_name', minWidth: 120 },
  { 
    title: '状态', 
    key: 'status',
    width: 100,
    render: (row) => {
      const type = row.status === 'success' ? 'success' : (row.status === 'running' ? 'info' : 'error')
      const labels = { success: '成功', running: '进行中...', failed: '失败' }
      return h(NTag, { type, size: 'small', bordered: false, round: true }, { default: () => labels[row.status] || row.status })
    }
  },
  { title: '大小', key: 'size', width: 100, render: (row) => `${row.size.toFixed(2)} MB` },
  { title: '消息', key: 'message', minWidth: 200, ellipsis: { tooltip: true } }
]

const fetchHistory = async (silent = false) => {
  if (!silent) loading.value = true
  try {
    const res = await axios.get('/api/backup/history')
    history.value = res.data
    
    // 如果有任务正在运行，启动/继续轮询
    const hasRunning = res.data.some((item: any) => item.status === 'running')
    if (hasRunning) {
      startPolling()
    } else {
      stopPolling()
    }
  } finally {
    loading.value = false
  }
}

const startPolling = () => {
  if (timer) return
  timer = setInterval(() => {
    fetchHistory(true)
  }, 5000)
}

const stopPolling = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

defineExpose({ fetchHistory })

onMounted(() => {
  fetchHistory()
})

onUnmounted(() => {
  stopPolling()
})
</script>
