import { useMessage } from 'naive-ui'

export function useBookmarkDnd(state: any, actions: any, bookmarkApi: any) {
  const message = useMessage()

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

  const onDragEnd = async () => {
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

  return { onDragStart, onDragEnter, onDragEnd, handleTreeDrop }
}
