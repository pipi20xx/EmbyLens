<template>
  <n-modal v-model:show="show" preset="card" :title="`构建历史 - ${projectName}`" style="width: 800px">
    <n-data-table
      :columns="columns"
      :data="tasks"
      :loading="loading"
      :bordered="false"
      size="small"
      max-height="400"
    />
    
    <!-- 内层日志查看器 -->
    <n-modal v-model:show="showLog" preset="card" title="详细日志" style="width: 900px; margin-top: 50px;">
      <div class="log-container">
        <pre>{{ currentLog }}</pre>
      </div>
    </n-modal>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch, h } from 'vue'
import { NModal, NDataTable, NButton, NSpace, NTag, useMessage, useDialog } from 'naive-ui'
import axios from 'axios'

const props = defineProps<{
  show: boolean
  projectId: string
  projectName: string
}>()

const emit = defineEmits(['update:show'])

const show = ref(false)
const tasks = ref([])
const loading = ref(false)
const showLog = ref(false)
const currentLog = ref('')

const message = useMessage()
const dialog = useDialog()

watch(() => props.show, (val) => {
  show.value = val
  if (val) fetchHistory()
})

watch(show, (val) => {
  emit('update:show', val)
})

const columns = [
  { 
    title: '执行时间', 
    key: 'created_at',
    render(row: any) {
      if (!row.created_at) return '-'
      const date = new Date(row.created_at)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    }
  },
  { title: 'Tag', key: 'tag' },
  { 
    title: '状态', 
    key: 'status',
    render(row: any) {
      const statusMap: Record<string, { label: string, type: 'success' | 'error' | 'info' | 'warning' }> = {
        'SUCCESS': { label: '成功', type: 'success' },
        'FAILED': { label: '失败', type: 'error' },
        'PENDING': { label: '处理中', type: 'info' }
      }
      const config = statusMap[row.status] || { label: row.status, type: 'info' }
      return h(NTag, { size: 'small', type: config.type, ghost: true }, { default: () => config.label })
    }
  },
  {
    title: '操作',
    key: 'actions',
    render(row: any) {
      return h(NSpace, null, {
        default: () => [
          h(NButton, { size: 'small', onClick: () => viewLog(row.id) }, { default: () => '查看日志' }),
          h(NButton, { size: 'small', type: 'error', ghost: true, onClick: () => deleteLog(row.id) }, { default: () => '删除' })
        ]
      })
    }
  }
]

const fetchHistory = async () => {
  if (!props.projectId) return
  loading.value = true
  try {
    const res = await axios.get(`/api/image-builder/projects/${props.projectId}/tasks`)
    tasks.value = res.data
  } catch (e) {
    message.error('获取历史失败')
  } finally {
    loading.value = false
  }
}

const viewLog = async (taskId: string) => {
  try {
    const res = await axios.get(`/api/image-builder/tasks/${taskId}/log`)
    currentLog.value = res.data.content
    showLog.value = true
  } catch (e) {
    message.error('读取日志失败')
  }
}

const deleteLog = (taskId: string) => {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这条构建记录吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await axios.delete(`/api/image-builder/tasks/${taskId}`)
        message.success('已删除')
        fetchHistory()
      } catch (e) {
        message.error('删除失败')
      }
    }
  })
}
</script>

<style scoped>
.log-container {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 4px;
  max-height: 600px;
  overflow-y: auto;
  font-family: monospace;
  white-space: pre-wrap;
}
</style>
