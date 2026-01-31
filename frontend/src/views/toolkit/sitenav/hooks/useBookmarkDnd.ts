import { useMessage } from 'naive-ui'
import { useBookmark, type Bookmark } from '../useBookmark'

export function useBookmarkDnd(state: any, actions: any) {
  const message = useMessage()
  const bookmarkApi = useBookmark()

  // --- 1. 右侧列表内排序 ---
  const onDragStart = (e: DragEvent, id: string) => {
    state.dragId.value = id
    if (e.dataTransfer) {
      e.dataTransfer.setData('text/plain', id)
      e.dataTransfer.effectAllowed = 'move'
    }
  }

  const onDragEnter = (targetId: string) => {
    if (!state.dragId.value || state.dragId.value === targetId) return
    const list = state.currentItems.value
    const fromIndex = list.findIndex((i: any) => i.id === state.dragId.value)
    const toIndex = list.findIndex((i: any) => i.id === targetId)
    if (fromIndex !== -1 && toIndex !== -1) {
      const [movedItem] = list.splice(fromIndex, 1)
      list.splice(toIndex, 0, movedItem)
    }
  }

  const onDragEnd = () => {
    if (state.dragId.value) {
      const list = state.currentItems.value
      bookmarkApi.reorderBookmarks(
        list.map((i: any) => i.id),
        state.selectedKeys.value[0] === 'root' ? null : state.selectedKeys.value[0]
      )
    }
    state.dragId.value = null
  }

  // --- 2. 左侧树内部层级拖拽 ---
  const handleTreeDrop = async ({ node, dragNode, dropPosition }: any) => {
    if (!dragNode) return
    const dragKey = dragNode.key
    const targetKey = node.key
    
    // 根节点不可移动
    if (dragKey === 'root' || dragKey === targetKey) return

    let newParentId: string | null = null
    let targetSiblings: string[] = []

    if (dropPosition === 'inside') {
      // 情况 A: 移动到目标文件夹内部
      newParentId = targetKey === 'root' ? null : targetKey
      
      const { item } = actions.findItemById(state.bookmarks.value, targetKey) || { item: null }
      const currentChildren = (targetKey === 'root' ? state.bookmarks.value : item?.children) || []
      
      targetSiblings = currentChildren.map((i: any) => i.id).filter((id: string) => id !== dragKey)
      targetSiblings.push(dragKey)
    } else {
      // 情况 B: 移动到目标节点之前或之后
      if (targetKey === 'root') return // 不允许拖到根节点同级

      const { item: targetItem } = actions.findItemById(state.bookmarks.value, targetKey) || { item: null }
      newParentId = targetItem?.parent_id || null
      
      const currentLevel = newParentId === null 
        ? state.bookmarks.value 
        : actions.findItemById(state.bookmarks.value, newParentId).item?.children || []
      
      targetSiblings = currentLevel.map((i: any) => i.id).filter((id: string) => id !== dragKey)
      const targetIndex = targetSiblings.indexOf(targetKey)
      
      if (dropPosition === 'before') {
        targetSiblings.splice(targetIndex, 0, dragKey)
      } else {
        targetSiblings.splice(targetIndex + 1, 0, dragKey)
      }
    }

    await bookmarkApi.reorderBookmarks(targetSiblings, newParentId)
    await bookmarkApi.fetchBookmarks(true)
    message.success('已调整文件夹层级')
  }

  return {
    onDragStart,
    onDragEnter,
    onDragEnd,
    handleTreeDrop
  }
}