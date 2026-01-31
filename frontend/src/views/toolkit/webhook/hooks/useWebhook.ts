import { ref } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { webhookApi } from '@/api/webhook'

export function useWebhook() {
  const message = useMessage()
  const dialog = useDialog()
  const loading = ref(false)
  const logs = ref([])
  const showModal = ref(false)
  const selectedPayload = ref({})

  const fetchLogs = async () => {
    loading.value = true
    try {
      const res = await webhookApi.getLogs()
      logs.value = res.data
    } catch (e) {
      message.error('加载日志失败')
    } finally {
      loading.value = false
    }
  }

  const handleClear = () => {
    dialog.warning({
      title: '确认清空日志',
      content: '确定要物理删除所有的 Webhook 历史记录吗？此操作无法撤销。',
      positiveText: '确定清空',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await webhookApi.clearLogs()
          message.success('日志已全部物理清理')
          fetchLogs()
        } catch (e) {
          message.error('清理失败')
        }
      }
    })
  }

  const showJson = (payload: any) => {
    selectedPayload.value = payload
    showModal.value = true
  }

  return {
    loading, logs, showModal, selectedPayload,
    fetchLogs, handleClear, showJson
  }
}
