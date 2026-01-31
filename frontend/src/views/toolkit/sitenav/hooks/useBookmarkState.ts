import { ref, reactive, computed } from 'vue'
import { useBookmark, type Bookmark } from '../useBookmark'

export function useBookmarkState() {
  const { bookmarks, fetchBookmarks } = useBookmark()

  // 核心导航状态
  const currentFolder = ref<Bookmark | null>(null)
  const selectedKeys = ref<string[]>(['root'])
  
  // 拖拽相关状态
  const dragId = ref<string | null>(null)
  const isDraggingExternal = ref(false)
  const dropTargetId = ref<string | null>(null)
  
  // UI 交互状态
  const showAddBookmark = ref(false)
  const showAddFolder = ref(false)
  const editingItem = ref<Bookmark | null>(null)
  const fetchingIcon = ref(false)
  const folderName = ref('')
  
  const form = reactive({
    title: '',
    url: '',
    icon: ''
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

  return {
    bookmarks,
    fetchBookmarks,
    currentFolder,
    selectedKeys,
    dragId,
    isDraggingExternal,
    dropTargetId,
    showAddBookmark,
    showAddFolder,
    editingItem,
    fetchingIcon,
    folderName,
    form,
    showAddBookmarkModal
  }
}
