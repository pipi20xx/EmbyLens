import { useDialog, useMessage } from 'naive-ui'
import { useBookmark, type Bookmark } from '../useBookmark'

export function useBookmarkActions(state: any) {
  const dialog = useDialog()
  const message = useMessage()
  const bookmarkApi = useBookmark()

  // 递归查找工具
  const findItemById = (list: Bookmark[], id: string): Bookmark | null => {
    for (const i of list) {
      if (i.id === id) return i
      if (i.children) {
        const res = findItemById(i.children, id)
        if (res) return res
      }
    }
    return null
  }

  const handleTreeSelect = (keys: string[]) => {
    state.selectedKeys.value = keys
    const targetKey = keys[0]
    if (!targetKey || targetKey === 'root') {
      state.currentFolder.value = null
      return
    }
    state.currentFolder.value = findItemById(state.bookmarks.value, targetKey)
  }

  const handleEdit = (item: Bookmark) => {
    state.editingItem.value = item
    state.form.title = item.title
    state.form.url = item.url || ''
    state.form.icon = item.icon || ''
  }

  const confirmDelete = (item: Bookmark) => {
    dialog.warning({
      title: '删除',
      content: `确定移除 "${item.title}"?`,
      positiveText: '确认',
      negativeText: '取消',
      onPositiveClick: async () => {
        await bookmarkApi.deleteBookmark(item.id)
        message.success('已删除')
        await bookmarkApi.fetchBookmarks(true)
      }
    })
  }

  const handleClearAll = () => {
    dialog.error({
      title: '危险',
      content: '确定清空所有内容？',
      positiveText: '清空',
      negativeText: '取消',
      onPositiveClick: async () => {
        await bookmarkApi.clearAllBookmarks()
        message.success('已清空')
        state.selectedKeys.value = ['root']
        state.currentFolder.value = null
      }
    })
  }

  const saveBookmark = async () => {
    const pId = state.selectedKeys.value[0] === 'root' ? null : state.selectedKeys.value[0]
    const data = { ...state.form, type: 'file' as const, parent_id: pId }
    if (state.editingItem.value) {
      await bookmarkApi.updateBookmark(state.editingItem.value.id, data)
    } else {
      await bookmarkApi.createBookmark(data)
    }
    state.showAddBookmarkModal.value = false
    await bookmarkApi.fetchBookmarks(true)
  }

  const saveFolder = async () => {
    if (!state.folderName.value) return
    const pId = state.selectedKeys.value[0] === 'root' ? null : state.selectedKeys.value[0]
    await bookmarkApi.createBookmark({
      title: state.folderName.value,
      type: 'folder',
      parent_id: pId
    })
    state.showAddFolder.value = false
    state.folderName.value = ''
    await bookmarkApi.fetchBookmarks(true)
  }

  const handleImportHtml = async (e: Event) => {
    const target = e.target as HTMLInputElement
    const file = target.files?.[0]
    if (!file) return
    const loadingMsg = message.loading('导入中...')
    try {
      const result = await bookmarkApi.importBookmarksHtml(file)
      loadingMsg.destroy()
      message.success(`成功导入 ${result.count} 个书签`)
      await bookmarkApi.fetchBookmarks(true)
    } catch (err: any) {
      loadingMsg.destroy()
      message.error('导入失败')
    } finally {
      target.value = ''
    }
  }

  return {
    handleTreeSelect,
    handleEdit,
    confirmDelete,
    handleClearAll,
    saveBookmark,
    saveFolder,
    handleImportHtml,
    findItemById,
    exportBookmarks: bookmarkApi.exportBookmarks,
    fetchIcon: bookmarkApi.fetchIcon
  }
}
