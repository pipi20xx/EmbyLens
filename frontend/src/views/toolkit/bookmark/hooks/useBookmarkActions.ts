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
        await bookmarkApi.clearBookmarks()
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

  const handleSelect = (item: Bookmark, e: MouseEvent) => {
    // If it's a folder click for navigation (double click or icon click), handled elsewhere usually.
    // This is for selection in the list.
    
    if (e.shiftKey && state.lastSelectedId.value) {
      // Range select
      const list = state.currentItems.value
      const lastIdx = list.findIndex((i: any) => i.id === state.lastSelectedId.value)
      const currIdx = list.findIndex((i: any) => i.id === item.id)
      if (lastIdx !== -1 && currIdx !== -1) {
        const start = Math.min(lastIdx, currIdx)
        const end = Math.max(lastIdx, currIdx)
        // If ctrl is not pressed, clear previous unless we are adding to range?
        // Standard behavior: shift+click extends selection from anchor.
        // Usually clears others outside range unless ctrl is also held.
        // For simplicity: Clear others, select range.
        if (!e.ctrlKey && !e.metaKey) {
            state.selectedItemIds.value.clear()
        }
        for (let i = start; i <= end; i++) {
          state.selectedItemIds.value.add(list[i].id)
        }
      }
    } else if (e.ctrlKey || e.metaKey) {
      // Toggle
      if (state.selectedItemIds.value.has(item.id)) {
        state.selectedItemIds.value.delete(item.id)
      } else {
        state.selectedItemIds.value.add(item.id)
        state.lastSelectedId.value = item.id
      }
    } else {
      // Single Select
      state.selectedItemIds.value.clear()
      state.selectedItemIds.value.add(item.id)
      state.lastSelectedId.value = item.id
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
      const result = await bookmarkApi.importHtml(file)
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

      saveBookmark, saveFolder, handleImportHtml, findItemById, refreshCurrentFolder, handleSelect

    }

  }

  