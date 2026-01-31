import { ref, reactive, computed, h, type Ref } from 'vue'
import { NIcon } from 'naive-ui'
import { 
  FolderOutlined as FolderIcon,
  HomeOutlined as HomeIcon
} from '@vicons/material'
import { type Bookmark } from '../../sitenav/useBookmark'

export function useBookmarkState(bookmarks: Ref<Bookmark[]>) {
  const currentFolder = ref<Bookmark | null>(null)
  const selectedKeys = ref<string[]>(['root'])
  const selectedItemIds = ref<Set<string>>(new Set())
  const lastSelectedId = ref<string | null>(null)
  const dragId = ref<string | null>(null)
  const isDraggingExternal = ref(false)
  const dropTargetId = ref<string | null>(null)
  const showAddBookmark = ref(false)
  const showAddFolder = ref(false)
  const editingItem = ref<Bookmark | null>(null)
  const fetchingIcon = ref(false)
  const folderName = ref('')
  const searchQuery = ref('')
  const form = reactive({ title: '', url: '', icon: '' })

  const searchBookmarks = (items: Bookmark[], query: string): Bookmark[] => {
    let result: Bookmark[] = []
    const q = query.toLowerCase()
    for (const item of items) {
      if (item.title.toLowerCase().includes(q) || (item.url && item.url.toLowerCase().includes(q))) {
        result.push(item)
      }
      if (item.children) {
        result = result.concat(searchBookmarks(item.children, query))
      }
    }
    return result
  }

  const currentItems = computed(() => {
    const rawData = Array.isArray(bookmarks.value) ? bookmarks.value : []

    if (searchQuery.value.trim()) {
      return searchBookmarks(rawData, searchQuery.value.trim())
    }

    if (!currentFolder.value || selectedKeys.value[0] === 'root') {
      return rawData
    }
    return currentFolder.value.children || []
  })

  const folderTree = computed(() => {
    const rawData = Array.isArray(bookmarks.value) ? bookmarks.value : []
    const transform = (items: Bookmark[]): any[] => {
      return items
        .filter(i => i.type === 'folder')
        .map(i => ({
          label: i.title,
          key: i.id,
          isLeaf: false,
          children: i.children ? transform(i.children) : [],
          prefix: () => h(NIcon, null, { default: () => h(FolderIcon) })
        }))
    }
    return [
      {
        label: '我的书签',
        key: 'root',
        isLeaf: false,
        prefix: () => h(NIcon, null, { default: () => h(HomeIcon) }),
        children: transform(rawData)
      }
    ]
  })

  const showAddBookmarkModal = computed({
    get: () => showAddBookmark.value || !!editingItem.value,
    set: (val) => { if (!val) { showAddBookmark.value = false; editingItem.value = null; } }
  })

  return {
    bookmarks, currentFolder, selectedKeys, selectedItemIds, lastSelectedId, dragId, isDraggingExternal, dropTargetId,
    showAddBookmark, showAddFolder, editingItem, fetchingIcon, folderName, searchQuery, form,
    showAddBookmarkModal, currentItems, folderTree
  }
}