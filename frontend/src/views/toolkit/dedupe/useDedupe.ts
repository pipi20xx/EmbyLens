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
  
  const dedupeConfig = ref<any>({ 
    rules: {
      priority_order: [],
      values_weight: { display_title: [], video_codec: [], video_range: [] },
      tie_breaker: 'small_id'
    }, 
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
        // 关键改进：按组显示重复项，不再混在一起
        const flattened: any[] = []
        res.data.forEach((group: any) => {
          group.items.forEach((item: any, index: number) => {
            flattened.push({ 
              ...item, 
              is_duplicate: true, 
              isLeaf: true,
              group_id: group.tmdb_id,
              is_first_in_group: index === 0 // 用于前端做视觉分割
            })
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
      message.error('同步失败')
    } finally {
      syncing.value = false
    }
  }

  const autoSelect = async () => {
    if (!showOnlyDuplicates.value) return message.warning('请先开启“仅显示重复项”模式')
    try {
      const res = await axios.post('/api/dedupe/smart-select', { items: items.value })
      selectedIds.value = res.data.to_delete
      message.success(`已智能选中 ${selectedIds.value.length} 个冗余副本`)
    } catch (e) {
      message.error('算法执行失败')
    }
  }

  const confirmDelete = () => {
    dialog.error({
      title: '永久删除确认',
      content: `确定要删除选中的 ${selectedIds.value.length} 个项目吗？`,
      positiveText: '确认删除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          const res = await axios.delete('/api/dedupe/items', { data: { item_ids: selectedIds.value } })
          message.success(`已清理 ${res.data.success} 个项目`)
          selectedIds.value = []
          showOnlyDuplicates.value ? toggleDuplicateMode(true) : loadItems()
        } catch (e) {}
      }
    })
  }

  return {
    loading, syncing, searchName, showOnlyDuplicates, items, selectedIds, dedupeConfig,
    loadItems, onLoadChildren, toggleDuplicateMode, syncMedia, autoSelect, confirmDelete, loadConfig, saveDedupeConfig
  }
}
