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
  
  // 核心：提供完整的初始化结构，防止 null 报错
  const dedupeConfig = ref<any>({ 
    rules: {
      priority_order: [],
      values_weight: {
        display_title: [],
        video_codec: [],
        video_range: []
      },
      tie_breaker: 'small_id'
    }, 
    exclude_paths: [] 
  })

  const loadConfig = async () => {
    try {
      const res = await axios.get('/api/dedupe/config')
      if (res.data && res.data.rules) {
        dedupeConfig.value = res.data
      }
    } catch (e) {
      console.error('加载配置失败', e)
    }
  }

  const saveDedupeConfig = async () => {
    try {
      await axios.post('/api/dedupe/config', dedupeConfig.value)
      message.success('规则已保存并应用')
      return true
    } catch (e) {
      message.error('保存配置失败')
      return false
    }
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
      const res = await axios.get('/api/dedupe/items', { 
        params: { query_text: searchName.value } 
      })
      items.value = processItems(res.data)
    } catch (e) {
      message.error('加载列表失败')
    } finally {
      loading.value = false
    }
  }

  const onLoadChildren = async (row: any) => {
    try {
      const res = await axios.get('/api/dedupe/items', { 
        params: { parent_id: row.id } 
      })
      row.children = processItems(res.data)
    } catch (e) {
      message.error('加载子项失败')
    }
  }

  const toggleDuplicateMode = async (val: boolean) => {
    if (val) {
      loading.value = true
      selectedIds.value = []
      try {
        const res = await axios.get('/api/dedupe/duplicates')
        const flattened: any[] = []
        res.data.forEach((group: any) => {
          group.items.forEach((item: any) => {
            flattened.push({ ...item, is_duplicate: true, isLeaf: true })
          })
        })
        items.value = flattened
      } catch (e) {
        message.error('加载重复项失败')
      } finally {
        loading.value = false
      }
    } else {
      loadItems()
    }
  }

  const syncMedia = async () => {
    syncing.value = true
    try {
      await axios.post('/api/dedupe/sync')
      message.success('全量同步完成')
      showOnlyDuplicates.value ? toggleDuplicateMode(true) : loadItems()
    } catch (e) {
      message.error('同步请求失败')
    } finally {
      syncing.value = false
    }
  }

  const autoSelect = async () => {
    if (!showOnlyDuplicates.value) {
      message.warning('请先开启“仅显示重复项”模式')
      return
    }
    try {
      const res = await axios.post('/api/dedupe/smart-select', { items: items.value })
      selectedIds.value = res.data.to_delete
      message.success(`智能选中了 ${selectedIds.value.length} 个建议删除项`)
    } catch (e) {
      message.error('智能选中算法执行失败')
    }
  }

  const confirmDelete = () => {
    dialog.error({
      title: '永久删除确认',
      content: `确定要删除选中的 ${selectedIds.value.length} 个项目吗？文件将从磁盘永久移除。`,
      positiveText: '确认删除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          const res = await axios.delete('/api/dedupe/items', { 
            data: { item_ids: selectedIds.value } 
          })
          message.success(`已删除 ${res.data.success} 个项目`)
          selectedIds.value = []
          showOnlyDuplicates.value ? toggleDuplicateMode(true) : loadItems()
        } catch (e) {
          message.error('删除操作失败')
        }
      }
    })
  }

  return {
    loading, syncing, searchName, showOnlyDuplicates, items, selectedIds, dedupeConfig,
    loadItems, onLoadChildren, toggleDuplicateMode, syncMedia, autoSelect, confirmDelete, loadConfig, saveDedupeConfig
  }
}