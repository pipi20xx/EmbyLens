<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)" preset="card" :title="`备份历史: ${taskName || '加载中...'}`" style="width: 850px">
    <n-data-table
      :columns="columns"
      :data="history"
      :loading="loading"
      size="small"
      :pagination="{ pageSize: 10 }"
    />
  </n-modal>
</template>

<script setup lang="ts">
import { ref, h, watch } from 'vue'
import { NModal, NDataTable, NTag, NButton, NSpace, NRadio, NRadioGroup, NText, useMessage, useDialog } from 'naive-ui'
import axios from 'axios'

const props = defineProps<{
  show: boolean
  taskId: string
  taskName: string
}>()

const emit = defineEmits(['update:show'])
const message = useMessage()
const dialog = useDialog()

const history = ref([])
const loading = ref(false)

const columns = [
  { title: '开始时间', key: 'start_time', width: 170 },
  { 
    title: '状态', 
    key: 'status',
    width: 90,
    render: (row) => {
      const type = row.status === 'success' ? 'success' : (row.status === 'running' ? 'info' : 'error')
      return h(NTag, { type, size: 'small', bordered: false }, { default: () => row.status })
    }
  },
  { title: '大小', key: 'size', width: 100, render: (row) => `${row.size.toFixed(2)} MB` },
  { title: '摘要/错误信息', key: 'message', ellipsis: { tooltip: true } },
  { 
    title: '操作', 
    key: 'actions',
    width: 110,
    render: (row) => {
      if (row.status !== 'success') return null
      return h(NButton, { 
        size: 'tiny', 
        type: 'warning', 
        secondary: true,
        onClick: () => handleRestore(row)
      }, { default: () => '还原' })
    }
  }
]

const fetchHistory = async () => {
  if (!props.taskId) return
  loading.value = true
  try {
    const res = await axios.get(`/api/backup/history?task_id=${props.taskId}`)
    history.value = res.data
  } catch (e) {
    message.error('加载历史记录失败')
  } finally {
    loading.value = false
  }
}

const handleRestore = (row) => {
  const restoreMode = ref('overwrite')

  dialog.warning({
    title: '确认还原',
    content: () => h('div', [
      h('p', `警告：还原操作将影响源目录 "${props.taskName}"。`),
      h('p', { style: 'margin-bottom: 12px; color: #d03050; font-weight: bold;' }, '请选择还原模式：'),
      h(NRadioGroup, {
        value: restoreMode.value,
        'onUpdate:value': (val) => { restoreMode.value = val }
      }, {
        default: () => [
          h(NSpace, { vertical: true }, {
            default: () => [
              h(NRadio, { value: 'overwrite' }, { default: () => '覆盖还原 (保留目录中已有但备份中没有的文件)' }),
              h(NRadio, { value: 'clear' }, { default: () => '清空还原 (还原前删除目标目录下所有内容)' })
            ]
          })
        ]
      })
    ]),
    positiveText: '确认执行',
    negativeText: '取消',
    onPositiveClick: () => {
      // 不再使用 async，点击立即关闭弹窗
      axios.post(`/api/backup/history/${row.id}/restore?clear_dst=${restoreMode.value === 'clear'}`)
        .then(() => {
          message.info('还原任务已在后台启动，请关注系统日志或稍后刷新历史')
          // 延迟刷新历史列表以显示可能产生的新记录（如果逻辑里有的话）
          setTimeout(fetchHistory, 1000)
        })
        .catch(e => {
          message.error('启动还原失败: ' + (e.response?.data?.detail || '未知错误'))
        })
    }
  })
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    history.value = [] // 切换任务时先清空
    fetchHistory()
  }
})
</script>