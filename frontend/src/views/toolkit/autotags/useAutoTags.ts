import { ref } from 'vue'
import axios from 'axios'
import { useMessage } from 'naive-ui'

export function useAutoTags() {
  const message = useMessage()
  const rules = ref<any[]>([])
  const loading = ref(false)

  const fetchRules = async () => {
    loading.value = true
    try {
      const res = await axios.get('/api/autotags/rules')
      rules.value = Array.isArray(res.data) ? res.data : []
    } catch (e) {
      rules.value = []
    } finally {
      loading.value = false
    }
  }

  const saveRules = async (newRules: any[]) => {
    try {
      await axios.post('/api/autotags/rules', newRules)
      message.success('规则已持久化')
      rules.value = newRules
      return true
    } catch (e) { return false }
  }

  const startTask = async (options: any) => {
    try {
      await axios.post('/api/autotags/execute', options)
    } catch (e) { message.error('启动失败') }
  }

  const testWrite = async (itemId: string, tag: string) => {
    try {
      const res = await axios.post('/api/autotags/test-write', { item_id: itemId, tag })
      return res.data.success
    } catch (e) { return false }
  }

  const clearAll = async () => {
    try {
      await axios.post('/api/autotags/clear-all')
    } catch (e) { message.error('启动失败') }
  }

  const clearSpecific = async (tags: string[]) => {
    try {
      await axios.post('/api/autotags/clear-specific', { tags })
    } catch (e) { message.error('启动失败') }
  }

  return {
    rules, loading, fetchRules, saveRules, startTask, testWrite, clearAll, clearSpecific
  }
}