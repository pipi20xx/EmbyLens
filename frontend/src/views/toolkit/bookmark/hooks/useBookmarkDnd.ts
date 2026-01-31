import { ref } from 'vue'
import { useMessage } from 'naive-ui'

export function useBookmarkDnd(state: any, actions: any, bookmarkApi: any) {
  const message = useMessage()
  const dragOverKey = ref<string | null>(null)
  const isDropped = ref(false)

  const onDragStart = (e: DragEvent, id: string) => {
    isDropped.value = false
    
    // If dragging an item not in selection, select it exclusively
    if (!state.selectedItemIds.value.has(id)) {
      state.selectedItemIds.value.clear()
      state.selectedItemIds.value.add(id)
      state.lastSelectedId.value = id
    }
    
    state.dragId.value = id
    if (e.dataTransfer) {
      e.dataTransfer.setData('text/plain', id)
      e.dataTransfer.effectAllowed = 'move'
      // Set a custom drag image or text if possible to indicate count?
      // For now, default is fine.
    }
  }

  const onDragEnter = (targetId: string) => {
    if (!state.dragId.value || state.dragId.value === targetId) return
    // If multi-selecting, maybe disable list reordering visual? 
    // Or just let it handle the primary dragged item.
    if (state.selectedItemIds.value.size > 1) return

    const list = state.currentItems.value
    const fromIndex = list.findIndex((i: any) => i.id === state.dragId.value)
    const toIndex = list.findIndex((i: any) => i.id === targetId)
    if (fromIndex !== -1 && toIndex !== -1) {
      const [movedItem] = list.splice(fromIndex, 1)
      list.splice(toIndex, 0, movedItem)
    }
  }

  const onDragEnd = async () => {
    dragOverKey.value = null
    if (isDropped.value) {
      state.dragId.value = null
      isDropped.value = false
      return
    }

    if (state.dragId.value) {
      const list = state.currentItems.value
      const pId = state.selectedKeys.value[0] === 'root' ? null : state.selectedKeys.value[0]
      await bookmarkApi.reorderBookmarks(list.map((i: any) => i.id), pId)
    }
    state.dragId.value = null
  }

  const handleTreeDrop = async ({ node, dragNode, dropPosition }: any) => {
    if (!dragNode) return
    const dragKey = dragNode.key
    const targetKey = node.key
    if (dragKey === 'root' || dragKey === targetKey) return

    let newParentId: string | null = null
    let targetSiblings: string[] = []

    if (dropPosition === 'inside') {
      newParentId = targetKey === 'root' ? null : targetKey
      const targetItem = actions.findItemById(state.bookmarks.value, targetKey)
      const currentChildren = (targetKey === 'root' ? state.bookmarks.value : targetItem?.children) || []
      targetSiblings = currentChildren.map((i: any) => i.id).filter((id: string) => id !== dragKey)
      targetSiblings.push(dragKey)
    } else {
      if (targetKey === 'root') return
      const targetItem = actions.findItemById(state.bookmarks.value, targetKey)
      newParentId = targetItem?.parent_id || null
      const currentLevel = newParentId === null 
        ? state.bookmarks.value 
        : actions.findItemById(state.bookmarks.value, newParentId)?.children || []
      targetSiblings = currentLevel.map((i: any) => i.id).filter((id: string) => id !== dragKey)
      const targetIndex = targetSiblings.indexOf(targetKey)
      if (dropPosition === 'before') targetSiblings.splice(targetIndex, 0, dragKey)
      else targetSiblings.splice(targetIndex + 1, 0, dragKey)
    }

    await bookmarkApi.reorderBookmarks(targetSiblings, newParentId)
    await actions.refreshCurrentFolder()
    message.success('已更新文件夹层级')
  }

  const nodeProps = ({ option }: { option: any }) => {
    return {
      style: option.key === dragOverKey.value 
        ? 'background-color: rgba(32, 128, 240, 0.15); color: #2080f0; transition: all 0.2s ease;' 
        : undefined,
      ondragover: (e: DragEvent) => {
        if (state.dragId.value) {
          e.preventDefault()
          if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
          if (dragOverKey.value !== option.key) {
             dragOverKey.value = option.key
          }
        }
      },
      ondrop: async (e: DragEvent) => {
        dragOverKey.value = null
        const draggedId = state.dragId.value
        if (!draggedId) return

        e.preventDefault()
        e.stopPropagation()
        
        isDropped.value = true

        const targetKey = option.key
        // Allow dropping onto self only if moving others? No, generally dropping onto self is no-op.
        // But with multi-select, if I drag A (and B selected) onto A's parent, it's a no-op?
        // Dragging list item to tree folder.
        
        const idsToMove = Array.from(state.selectedItemIds.value as Set<string>)
        // Fallback if empty (shouldn't happen)
        if (idsToMove.length === 0) idsToMove.push(draggedId)
        
        // Validation: Don't move if target is one of the moving items (folder)
        if (idsToMove.includes(targetKey)) return

        const targetParentId = targetKey === 'root' ? null : targetKey

        try {
          await bookmarkApi.reorderBookmarks(idsToMove, targetParentId)
          message.success(`成功移动 ${idsToMove.length} 个项目`)
          await actions.refreshCurrentFolder()
          // Clear selection after move? Maybe user wants to move them again?
          // Usually after move they disappear from view (if view is source folder), so selection is implicitly cleared or invalid.
          state.selectedItemIds.value.clear()
        } catch (error) {
          message.error('移动失败')
        }
        state.dragId.value = null
      }
    }
  }

  return { onDragStart, onDragEnter, onDragEnd, handleTreeDrop, nodeProps }
}
