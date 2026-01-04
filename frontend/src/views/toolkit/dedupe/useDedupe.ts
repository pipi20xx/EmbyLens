import { ref } from 'vue'
import axios from 'axios'
import { useMessage, useDialog } from 'naive-ui'

export function useDedupe() {
  const message = useMessage()
  const dialog = useDialog()

  const loading = ref(false)
  const syncing = ref(false)
  const searchName = ref('')
  const showOnlyDuplicates = ref(false)
  const items = ref<any[]>([])
  const selectedIds = ref<string[]>([])
  const suggestedItems = ref<any[]>([]) // 专门存储智能选中的结果对象
  
  const dedupeConfig = ref<any>({ 
    rules: { priority_order: [], values_weight: {}, tie_breaker: 'small_id' }, 
    exclude_paths: [] 
  })

  const loadConfig = async () => {
    try {
      const res = await axios.get('/api/dedupe/config')
      if (res.data && res.data.rules) dedupeConfig.value = res.data
    } catch (e) {}
  }

  const saveDedupeConfig = async () => {
    try {
      await axios.post('/api/dedupe/config', dedupeConfig.value)
      message.success('规则已保存')
      return true
    } catch (e) { return false }
  }

  const processItems = (data: any[]) => {
    return data.map(i => ({
      ...i,
      isLeaf: i.item_type !== 'Series' && i.item_type !== 'Season'
    }))
  }

  const loadItems = async () => {
    loading.value = true
    selectedIds.value = []
    try {
      const res = await axios.get('/api/dedupe/items', { params: { query_text: searchName.value } })
      items.value = processItems(res.data)
    } catch (e) {
      message.error('加载列表失败')
    } finally {
      loading.value = false
    }
  }

  const onLoadChildren = async (row: any) => {
    try {
      const res = await axios.get('/api/dedupe/items', { params: { parent_id: row.id } })
      row.children = processItems(res.data)
    } catch (e) {}
  }

  const toggleDuplicateMode = async (val: boolean) => {
    if (val) {
      loading.value = true
      selectedIds.value = []
      try {
        const res = await axios.get('/api/dedupe/duplicates')
        // 后端现在直接返回平铺的重复项列表
        items.value = processItems(res.data)
      } catch (e) {
        message.error('加载重复项失败')
      } finally {
        loading.value = false
      }
    } else {
      loadItems()
    }
  }

  const syncMedia = () => {
    if (syncing.value) return
    
    syncing.value = true
    message.info('后台同步任务已启动，请通过“实时日志”查看进度', { duration: 5000 })
    
    // 发起请求但不 await 阻塞
    axios.post('/api/dedupe/sync').then(() => {
      message.success('Emby 媒体库同步已在后台完成')
      // 同步完成后自动刷新当前视图的数据
      if (showOnlyDuplicates.value) {
        toggleDuplicateMode(true)
      } else {
        loadItems()
      }
    }).catch((e) => {
      message.error('后台同步任务执行失败，请检查网络或日志')
    }).finally(() => {
      syncing.value = false
    })
  }

  // --- 智能选中重构 ---
  const autoSelect = async () => {
    loading.value = true
    try {
      // 不传任何参数，让后端全库扫描
      const res = await axios.post('/api/dedupe/smart-select')
      suggestedItems.value = res.data
      selectedIds.value = res.data.map((i: any) => i.id)
      
      if (res.data.length === 0) {
        message.info('未发现符合规则的可清理项目')
      }
      return res.data
    } catch (e) {
      message.error('算法执行失败')
      return []
    } finally {
      loading.value = false
    }
  }

  const deleteItems = async (ids: string[]) => {
    try {
      const res = await axios.delete('/api/dedupe/items', { data: { item_ids: ids } })
      message.success(`成功删除 ${res.data.success} 个项目`)
      selectedIds.value = []
      showOnlyDuplicates.value ? toggleDuplicateMode(true) : loadItems()
      return true
    } catch (e) {
      message.error('删除失败')
      return false
    }
  }

  return {
    loading, syncing, searchName, showOnlyDuplicates, items, selectedIds, suggestedItems, dedupeConfig,
    loadItems, onLoadChildren, toggleDuplicateMode, syncMedia, autoSelect, deleteItems, loadConfig, saveDedupeConfig
  }
}