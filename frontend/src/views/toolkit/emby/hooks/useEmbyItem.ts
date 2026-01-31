import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { embyApi } from '@/api/emby'

export function useEmbyItem() {
  const message = useMessage()
  const itemId = ref('')
  const itemData = ref<any>(null)
  const loading = ref(false)

  const fetchInfo = async () => {
    if (!itemId.value) {
      message.warning('请输入项目 ID')
      return
    }
    loading.value = true
    itemData.value = null
    try {
      const res = await embyApi.getItemInfo(itemId.value)
      itemData.value = res.data
      message.success('元数据抓取成功')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '抓取失败，请确认 ID 是否正确')
    } finally {
      loading.value = false
    }
  }

  return {
    itemId, itemData, loading, fetchInfo
  }
}
