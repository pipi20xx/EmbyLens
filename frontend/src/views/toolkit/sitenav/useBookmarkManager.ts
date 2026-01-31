import { ref, computed, reactive, onMounted, h } from 'vue'
import { NIcon, useDialog, useMessage } from 'naive-ui'
import { FolderOutlined as FolderIcon } from '@vicons/material'
import { useBookmark, type Bookmark } from './useBookmark'

export function useBookmarkManager() {
  const dialog = useDialog()
  const message = useMessage()
  const { 
    bookmarks, fetchBookmarks, createBookmark: apiCreate, 
    updateBookmark: apiUpdate, deleteBookmark: apiDelete, 
    clearAllBookmarks, exportBookmarks,
    reorderBookmarks: apiReorder, importBookmarksHtml, fetchIcon 
  } = useBookmark()

  // --- UI 状态 ---
  const currentFolder = ref<Bookmark | null>(null)
  const selectedKeys = ref<string[]>([])
  const dragId = ref<string | null>(null)
  const showAddBookmark = ref(false)
  const showAddFolder = ref(false)
  const editingItem = ref<Bookmark | null>(null)
  const fetchingIcon = ref(false)
  
  const folderName = ref('')
  const form = reactive({ title: '', url: '', icon: '' })

  // --- 计算属性 ---
  const currentItems = computed(() => {
    if (!currentFolder.value) return bookmarks.value
    return currentFolder.value.children || []
  })

  const folderTree = computed(() => {
    const mapFolder = (items: Bookmark[]): any[] => {
      return items
        .filter(i => i.type === 'folder')
        .map(i => ({
          label: i.title,
          key: i.id,
          children: (i.children && i.children.some(c => c.type === 'folder')) ? mapFolder(i.children) : undefined,
          prefix: () => h(NIcon, null, { default: () => h(FolderIcon) })
        }))
    }
    return mapFolder(bookmarks.value)
  })

  const showAddBookmarkModal = computed({
    get: () => showAddBookmark.value || !!editingItem.value,
    set: (val) => {
      if (!val) {
        showAddBookmark.value = false
        editingItem.value = null
      }
    }
  })

  // --- 内部辅助 ---
  const refreshCurrentFolder = async () => {
    const oldId = currentFolder.value?.id
    await fetchBookmarks()
    if (oldId) {
      const find = (list: Bookmark[]): Bookmark | null => {
        for (const i of list) {
          if (i.id === oldId) return i
          if (i.children) {
            const r = find(i.children)
            if (r) return r
          }
        }
        return null
      }
      currentFolder.value = find(bookmarks.value)
    }
  }

  // --- 方法 ---
  const selectRoot = () => {
    currentFolder.value = null
    selectedKeys.value = []
  }

  const handleTreeSelect = (keys: string[]) => {
    selectedKeys.value = keys
    if (keys.length > 0) {
      const findFolder = (list: Bookmark[], id: string): Bookmark | null => {
        for (const i of list) {
          if (i.id === id) return i
          if (i.children) {
            const r = findFolder(i.children, id)
            if (r) return r
          }
        }
        return null
      }
      currentFolder.value = findFolder(bookmarks.value, keys[0])
    } else {
      currentFolder.value = null
    }
  }

  const handleItemClick = (item: Bookmark) => {
    if (item.type === 'folder') {
      handleTreeSelect([item.id])
    } else if (item.url) {
      window.open(item.url, '_blank')
    }
  }

  const handleEdit = (item: Bookmark) => {
    editingItem.value = item
    form.title = item.title
    form.url = item.url || ''
    form.icon = item.icon || ''
  }

  const confirmDelete = (item: Bookmark) => {
    dialog.warning({
      title: '删除',
      content: `确定移除 "${item.title}"?`,
      positiveText: '确认',
      negativeText: '取消',
      onPositiveClick: async () => {
        await apiDelete(item.id)
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
        await clearAllBookmarks()
        message.success('已全部清空')
        selectRoot()
      }
    })
  }

  const handleExport = () => { exportBookmarks() }

  const saveBookmark = async () => {
    const data = { ...form, type: 'file' as const, parent_id: currentFolder.value?.id }
    if (editingItem.value) await apiUpdate(editingItem.value.id, data)
    else await apiCreate(data)
    showAddBookmark.value = false
    editingItem.value = null
    form.title = ''; form.url = ''; form.icon = ''
    await refreshCurrentFolder()
  }

  const saveFolder = async () => {
    if (!folderName.value) return
    await apiCreate({ title: folderName.value, type: 'folder', parent_id: currentFolder.value?.id })
    showAddFolder.value = false
    folderName.value = ''
    await refreshCurrentFolder()
  }

  const autoFetchTitle = async () => {
    if (form.url && !form.title) {
      try { form.title = new URL(form.url).hostname } catch (e) {}
    }
  }

  const autoFetchIcon = async () => {
    if (!form.url) return
    fetchingIcon.value = true
    const icon = await fetchIcon(form.url)
    if (icon) form.icon = icon
    fetchingIcon.value = false
  }

  const handleImportHtml = async (e: Event) => {
    const target = e.target as HTMLInputElement
    const file = target.files?.[0]
    if (!file) return
    
    const loadingMsg = message.loading('正在导入...', { duration: 0 })
    try {
      const result = await importBookmarksHtml(file)
      loadingMsg.destroy()
      if (result.count > 0) {
        message.success(`成功导入 ${result.count} 个项目`)
        await refreshCurrentFolder()
      } else {
        message.warning('未发现新书签')
      }
    } catch (err: any) {
      loadingMsg.destroy()
      message.error(`导入失败: ${err.message || '格式错误'}`)
    } finally {
      target.value = ''
    }
  }

  const onDragStart = (id: string) => { dragId.value = id }
  const onDragEnter = (targetId: string) => {
    if (!dragId.value || dragId.value === targetId) return
    const list = currentFolder.value ? currentFolder.value.children : bookmarks.value
    if (!list) return
    const fromIndex = list.findIndex(i => i.id === dragId.value)
    const toIndex = list.findIndex(i => i.id === targetId)
    if (fromIndex !== -1 && toIndex !== -1) {
      const [movedItem] = list.splice(fromIndex, 1)
      list.splice(toIndex, 0, movedItem)
    }
  }
  const onDragEnd = async () => {
    if (!dragId.value) return
    const list = currentFolder.value ? currentFolder.value.children : bookmarks.value
    if (list) await apiReorder(list.map(i => i.id), currentFolder.value?.id)
    dragId.value = null
  }

  onMounted(fetchBookmarks)

  return {
    currentFolder, selectedKeys, dragId, showAddBookmark, showAddFolder, editingItem,
    fetchingIcon, folderName, form, currentItems, folderTree, showAddBookmarkModal,
    selectRoot, handleTreeSelect, handleItemClick, handleEdit, confirmDelete,
    handleClearAll, handleExport, saveBookmark, saveFolder, autoFetchTitle, 
    autoFetchIcon, handleImportHtml, onDragStart, onDragEnter, onDragEnd
  }
}