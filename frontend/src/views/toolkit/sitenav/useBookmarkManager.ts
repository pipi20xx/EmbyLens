import { onMounted, h, computed } from 'vue'
import { NIcon } from 'naive-ui'
import { 
  FolderOutlined as FolderIcon,
  HomeOutlined as HomeIcon
} from '@vicons/material'
import { useBookmarkState } from './hooks/useBookmarkState'
import { useBookmarkActions } from './hooks/useBookmarkActions'
import { useBookmarkDnd } from './hooks/useBookmarkDnd'
import { type Bookmark } from './useBookmark'

export function useBookmarkManager() {
  const state = useBookmarkState()
  const actions = useBookmarkActions(state)
  const dnd = useBookmarkDnd(state, actions)

  // 文件夹树：保持文件夹始终为非叶子节点，支持拖入
  const folderTree = computed(() => {
    const rawData = Array.isArray(state.bookmarks.value) ? state.bookmarks.value : []
    
    const transform = (items: Bookmark[]): any[] => {
      return items
        .filter(i => i.type === 'folder')
        .map(i => ({
          label: i.title,
          key: i.id,
          isLeaf: false, // 允许任何文件夹接收拖拽
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

  const autoFetchTitle = async () => {
    if (state.form.url && !state.form.title) {
      try {
        state.form.title = new URL(state.form.url).hostname
      } catch (e) {}
    }
  }

  const autoFetchIcon = async () => {
    if (!state.form.url) return
    state.fetchingIcon.value = true
    const icon = await actions.fetchIcon(state.form.url)
    if (icon) state.form.icon = icon
    state.fetchingIcon.value = false
  }

  onMounted(() => state.fetchBookmarks(true))

  return {
    ...state,
    ...actions,
    ...dnd,
    folderTree,
    autoFetchTitle,
    autoFetchIcon
  }
}