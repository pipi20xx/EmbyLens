import { useDialog, useMessage } from 'naive-ui'
import { type Bookmark } from '../../sitenav/useBookmark'

export function useBookmarkActions(state: any, bookmarkApi: any) {
  const dialog = useDialog()
  const message = useMessage()

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

  const handleItemClick = (item: Bookmark) => {
    if (item.type === 'folder') {
      state.selectedKeys.value = [item.id]
      state.currentFolder.value = item
    } else if (item.url) {
      window.open(item.url, '_blank')
    }
  }

  const handleEdit = (item: Bookmark) => {
    state.editingItem.value = item
    state.form.title = item.title; state.form.url = item.url || ''; state.form.icon = item.icon || ''
  }

  const confirmDelete = (item: Bookmark) => {
    dialog.warning({
      title: '确认删除',
      content: `确定移除 "${item.title}"?`,
      positiveText: '确认',
      negativeText: '取消',
      onPositiveClick: async () => {
        await bookmarkApi.deleteBookmark(item.id)
        message.success('已删除')
        await refreshCurrentFolder()
      }
    })
  }

  const handleClearAll = () => {
    dialog.error({
      title: '危险操作',
      content: '确定要清空所有书签吗？此操作无法撤销。',
      positiveText: '全部清空',
      negativeText: '取消',
      onPositiveClick: async () => {
        await bookmarkApi.clearAllBookmarks()
        message.success('已全部清空')
        state.selectedKeys.value = ['root']
        state.currentFolder.value = null
      }
    })
  }

  const refreshCurrentFolder = async () => {
    const oldId = state.currentFolder.value?.id
    await bookmarkApi.fetchBookmarks(true)
    if (oldId) {
      state.currentFolder.value = findItemById(state.bookmarks.value, oldId)
    }
  }

  const saveBookmark = async () => {
    const pId = state.selectedKeys.value[0] === 'root' ? null : state.selectedKeys.value[0]
    const data = { ...state.form, type: 'file' as const, parent_id: pId }
    if (state.editingItem.value) await bookmarkApi.updateBookmark(state.editingItem.value.id, data)
    else await bookmarkApi.createBookmark(data)
    state.showAddBookmarkModal.value = false
    await refreshCurrentFolder()
  }

  const saveFolder = async () => {
    if (!state.folderName.value) return
    const pId = state.selectedKeys.value[0] === 'root' ? null : state.selectedKeys.value[0]
    await bookmarkApi.createBookmark({ title: state.folderName.value, type: 'folder', parent_id: pId })
    state.showAddFolder.value = false; state.folderName.value = ''
    await refreshCurrentFolder()
  }

  const handleExport = () => {
    bookmarkApi.exportBookmarks()
  }

  const handleImportHtml = async (e: Event) => {
    const target = e.target as HTMLInputElement
    const file = target.files?.[0]
    if (!file) return
    const loadingMsg = message.loading('正在导入...', { duration: 0 })
    try {
      const result = await bookmarkApi.importBookmarksHtml(file)
      loadingMsg.destroy()
      message.success(`成功导入 ${result.count} 个项目`)
      await refreshCurrentFolder()
    } catch (err: any) {
      loadingMsg.destroy(); message.error('导入失败')
    } finally {
      target.value = ''
    }
  }

    return {

      handleTreeSelect, handleItemClick, handleEdit, confirmDelete, handleClearAll, handleExport,

      saveBookmark, saveFolder, handleImportHtml, findItemById, refreshCurrentFolder

    }

  }

  