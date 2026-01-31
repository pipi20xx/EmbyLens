import { ref, computed } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { type Bookmark } from '../../sitenav/useBookmark'

export function useBookmarkHealth(bookmarkApi: any, actions: any) {
  const message = useMessage()
  const dialog = useDialog()

  const showHealthModal = ref(false)
  const activeTab = ref('duplicate') // duplicate | health

  // Duplicate Logic
  const duplicates = ref<any[]>([])
  const loadingDuplicates = ref(false)

  const scanDuplicates = async () => {
    loadingDuplicates.value = true
    try {
      duplicates.value = await bookmarkApi.findDuplicates()
    } finally {
      loadingDuplicates.value = false
    }
  }

  const deleteBookmarkAndRefresh = async (id: string) => {
    await bookmarkApi.deleteBookmark(id)
  }

  const handleMergeDuplicate = async (group: any, keepId: string) => {
    // Delete all except keepId
    for (const item of group.items) {
      if (item.id !== keepId) {
        await deleteBookmarkAndRefresh(item.id)
      }
    }
    // Remove group from list locally
    duplicates.value = duplicates.value.filter(g => g.url !== group.url)
    message.success('合并成功')
    await actions.refreshCurrentFolder()
  }

  const handleMergeAllDuplicates = async () => {
    if (duplicates.value.length === 0) return

    const totalToKeep = duplicates.value.length
    const totalToDelete = duplicates.value.reduce((acc, g) => acc + (g.count - 1), 0)

    dialog.warning({
      title: '批量合并书签',
      content: `确定要合并所有重复组吗？操作后将保留每组的第一个书签，共计清理 ${totalToDelete} 个重复项。`,
      positiveText: '开始合并',
      negativeText: '取消',
      onPositiveClick: async () => {
        let count = 0
        for (const group of duplicates.value) {
          const keepId = group.items[0].id
          for (const item of group.items) {
            if (item.id !== keepId) {
              try {
                await bookmarkApi.deleteBookmark(item.id)
                count++
              } catch (e) {}
            }
          }
        }
        duplicates.value = []
        message.success(`成功合并所有书签，共清理 ${count} 个重复项`)
        await actions.refreshCurrentFolder()
      }
    })
  }
  
  const handleDeleteAllInGroup = async (group: any) => {
      dialog.warning({
          title: '确认删除',
          content: `确定删除该链接的所有 ${group.items.length} 个书签吗？`,
          positiveText: '删除',
          negativeText: '取消',
          onPositiveClick: async () => {
             for (const item of group.items) {
                 await deleteBookmarkAndRefresh(item.id)
             }
             duplicates.value = duplicates.value.filter(g => g.url !== group.url)
             message.success('已全部删除')
             await actions.refreshCurrentFolder()
          }
      })
  }

  // Health Check Logic
  const healthResults = ref<any[]>([])
  const healthProgress = ref(0)
  const isScanningHealth = ref(false)
  
  const scanHealth = async (bookmarks: Bookmark[]) => {
      if (isScanningHealth.value) return
      isScanningHealth.value = true
      healthProgress.value = 0
      healthResults.value = []
      
      // Flatten all bookmarks
      const allFiles: any[] = []
      const traverse = (items: Bookmark[]) => {
          for (const item of items) {
              if (item.type === 'file' && item.url) allFiles.push(item)
              if (item.children) traverse(item.children)
          }
      }
      traverse(bookmarks)
      
      const total = allFiles.length
      if (total === 0) {
          isScanningHealth.value = false
          return
      }

      const BATCH_SIZE = 10
      for (let i = 0; i < total; i += BATCH_SIZE) {
          if (!isScanningHealth.value) break // Allow stop
          
          const batch = allFiles.slice(i, i + BATCH_SIZE)
          const urls = batch.map(b => b.url)
          
          const res = await bookmarkApi.checkHealth(urls)
          
          // Process results
          for (const item of batch) {
              const status = res[item.url]
              if (status !== 200) { // 200 is OK. 0 is fail. 404 is fail.
                  healthResults.value.push({
                      ...item,
                      statusCode: status
                  })
              }
          }
          
          healthProgress.value = Math.min(100, Math.round(((i + BATCH_SIZE) / total) * 100))
      }
      
      healthProgress.value = 100
      isScanningHealth.value = false
  }

  const stopScanHealth = () => {
      isScanningHealth.value = false
  }
  
  const handleDeleteDead = async (id: string) => {
      await bookmarkApi.deleteBookmark(id)
      healthResults.value = healthResults.value.filter(h => h.id !== id)
      message.success('已删除')
      await actions.refreshCurrentFolder()
  }

  const handleDeleteBatchDead = async (statusCodes: number[]) => {
      const targets = healthResults.value.filter(h => statusCodes.includes(h.statusCode))
      if (targets.length === 0) {
          message.info('没有符合条件的书签')
          return
      }

      dialog.warning({
          title: '批量清理',
          content: `确定要清理这 ${targets.length} 个状态码为 [${statusCodes.join(', ')}] 的无效书签吗？`,
          positiveText: '确认清理',
          negativeText: '取消',
          onPositiveClick: async () => {
              const ids = targets.map(t => t.id)
              let count = 0
              for (const id of ids) {
                  try {
                      await bookmarkApi.deleteBookmark(id)
                      count++
                  } catch (e) {}
              }
              healthResults.value = healthResults.value.filter(h => !ids.includes(h.id))
              message.success(`成功清理 ${count} 个无效书签`)
              await actions.refreshCurrentFolder()
          }
      })
  }

  return {
    showHealthModal,
    activeTab,
    duplicates,
    loadingDuplicates,
    scanDuplicates,
    handleMergeDuplicate,
    handleMergeAllDuplicates,
    handleDeleteAllInGroup,
    
    healthResults,
    healthProgress,
    isScanningHealth,
    scanHealth,
    stopScanHealth,
    handleDeleteDead,
    handleDeleteBatchDead
  }
}
