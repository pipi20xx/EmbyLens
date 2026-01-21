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
import { ref, h, onMounted } from 'vue'
import { NCard, NDataTable, NTag, NButton } from 'naive-ui'
import axios from 'axios'

const history = ref([])
const loading = ref(false)

const historyColumns = [
  { title: '开始时间', key: 'start_time' },
  { title: '任务', key: 'task_name' },
  { 
    title: '状态', 
    key: 'status',
    render: (row) => {
      const type = row.status === 'success' ? 'success' : (row.status === 'running' ? 'info' : 'error')
      return h(NTag, { type, size: 'small', bordered: false }, { default: () => row.status })
    }
  },
  { title: '大小', key: 'size', render: (row) => `${row.size.toFixed(2)} MB` },
  { title: '消息', key: 'message', ellipsis: { tooltip: true } }
]

const fetchHistory = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/backup/history')
    history.value = res.data
  } finally {
    loading.value = false
  }
}

defineExpose({ fetchHistory })

onMounted(fetchHistory)
</script>
