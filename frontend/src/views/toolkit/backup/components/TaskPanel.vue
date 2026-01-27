<template>
  <n-card size="small" segmented title="备份任务">
    <template #header-extra>
      <n-space>
        <n-button type="primary" size="small" @click="$emit('add')">新增任务</n-button>
        <n-button size="small" @click="fetchTasks">刷新</n-button>
      </n-space>
    </template>
    
    <n-data-table
      :columns="columns"
      :data="tasks"
      :loading="loading"
      size="small"
    />
  </n-card>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { NCard, NSpace, NButton, NDataTable, NTag, useMessage, useDialog } from 'naive-ui'
import axios from 'axios'

const emit = defineEmits(['add', 'edit', 'run', 'view-history'])
const message = useMessage()
const dialog = useDialog()

const tasks = ref([])
const loading = ref(false)

const formatSchedule = (row: any) => {
  if (!row.enabled) return '-'
  
  if (row.schedule_type === 'interval') {
    const min = parseInt(row.schedule_value)
    if (min % 1440 === 0) return `每隔 ${min / 1440} 天`
    if (min % 60 === 0) return `每隔 ${min / 60} 小时`
    return `每隔 ${min} 分钟`
  }
  
  if (row.schedule_type === 'cron') {
    const cron = row.schedule_value || ''
    // 匹配每天: "m h * * *"
    const dailyMatch = cron.match(/^(\d+)\s+(\d+)\s+\*\s+\*\s+\*$/)
    if (dailyMatch) {
      const m = dailyMatch[1].padStart(2, '0')
      const h = dailyMatch[2].padStart(2, '0')
      return `每天 ${h}:${m}`
    }
    return cron // 复杂的 cron 保持原样
  }
  return row.schedule_value
}

const columns = [
  { 
    title: '任务名称', 
    key: 'name',
    render: (row) => h(NSpace, { align: 'center', size: 4 }, {
      default: () => [
        h('span', null, row.name),
        row.host_id && row.host_id !== 'local' ? h(NTag, { type: 'warning', size: 'tiny', bordered: false, quaternary: true }, { default: () => '远程' }) : null
      ]
    })
  },
  { 
    title: '模式', 
    key: 'mode', 
    render: (row) => h(NTag, { type: 'info', size: 'small', bordered: false }, { default: () => row.mode }) 
  },
  { 
    title: '存储介质', 
    key: 'storage_type',
    render: (row) => {
        const labels = { ssd: 'SSD', hdd: 'HDD', cloud: '云盘' }
        return h(NText, { depth: 3, style: 'font-size: 12px' }, { default: () => labels[row.storage_type] || 'SSD' })
    }
  },
  { 
    title: '自动运行', 
    key: 'enabled', 
    width: 150,
    render: (row) => h(NSpace, { vertical: true, size: 2 }, {
      default: () => [
        h(NTag, { 
          type: row.enabled ? 'success' : 'default', 
          size: 'small', 
          bordered: false,
          round: true
        }, { default: () => row.enabled ? '自动计划中' : '仅手动' }),
        h(NText, { depth: 3, style: 'font-size: 11px; padding-left: 4px;' }, { 
          default: () => formatSchedule(row) 
        })
      ]
    })
  },
  { 
    title: '操作', 
    key: 'actions',
    render: (row) => h(NSpace, {}, {
      default: () => [
        h(NButton, { size: 'tiny', secondary: true, type: 'primary', onClick: () => emit('run', row) }, { default: () => '立即执行' }),
        h(NButton, { size: 'tiny', secondary: true, onClick: () => emit('view-history', row) }, { default: () => '历史' }),
        h(NButton, { size: 'tiny', onClick: () => emit('edit', row) }, { default: () => '编辑' }),
        h(NButton, { size: 'tiny', type: 'error', ghost: true, onClick: () => handleDeleteTask(row) }, { default: () => '删除' })
      ]
    })
  }
]

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/backup/tasks')
    tasks.value = res.data
  } finally {
    loading.value = false
  }
}

const handleDeleteTask = (row) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除任务 "${row.name}" 吗？`,
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: async () => {
      await axios.delete(`/api/backup/tasks/${row.id}`)
      message.success('已删除')
      fetchTasks()
    }
  })
}

defineExpose({ fetchTasks })

onMounted(fetchTasks)
</script>

<script lang="ts">
import { NText } from 'naive-ui'
</script>
