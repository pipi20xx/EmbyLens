import { ref, computed } from 'vue'
import { menuLayout, MenuGroup } from '../../store/navigationStore'
import { allMenuItems } from '../../config/menu'

export interface MenuGroup {
  key: string
  label: string
  visible: boolean
  type: 'group' | 'item' // 区分是容器还是独立项
  items: string[]
}

export function useMenuEditor() {
  const draggingGroupIndex = ref<number | null>(null)
  const draggingItem = ref<{ groupIndex: number | null, itemIndex: number | null, key: string } | null>(null)
  const editingGroupIndex = ref<number | null>(null)

  const allocatedItemKeys = computed(() => {
    const keys = new Set<string>()
    menuLayout.value.forEach(g => {
      if (g.type === 'item') {
        keys.add(g.key)
      } else {
        g.items.forEach(k => keys.add(k))
      }
    })
    return keys
  })

  const unallocatedItems = computed(() => {
    return allMenuItems.filter(m => !allocatedItemKeys.value.has(m.key as string))
  })

  const addNewGroup = () => {
    menuLayout.value.push({
      key: `group-${Date.now()}`,
      label: '新分组',
      visible: true,
      type: 'group',
      items: []
    })
  }

  // 将功能池的项直接添加为一级菜单
  const addItemAsPrimary = (itemKey: string, targetIndex?: number) => {
    const item = allMenuItems.find(m => m.key === itemKey)
    if (!item) return

    const newPrimary: MenuGroup = {
      key: item.key as string,
      label: item.label as string,
      visible: true,
      type: 'item',
      items: []
    }

    if (typeof targetIndex === 'number') {
      menuLayout.value.splice(targetIndex, 0, newPrimary)
    } else {
      menuLayout.value.push(newPrimary)
    }
  }

  const removeGroup = (index: number) => {
    menuLayout.value.splice(index, 1)
  }

  const removeItemFromGroup = (groupIndex: number, itemIndex: number) => {
    menuLayout.value[groupIndex].items.splice(itemIndex, 1)
  }

  const onGroupDragStart = (index: number) => {
    draggingGroupIndex.value = index
  }

  // 处理一级菜单之间的排序（包括 Group 和 Item）
  const onPrimaryDrop = (targetIndex: number) => {
    // 情况 A：移动已有的一级菜单
    if (draggingGroupIndex.value !== null) {
      const moved = menuLayout.value.splice(draggingGroupIndex.value, 1)[0]
      menuLayout.value.splice(targetIndex, 0, moved)
      draggingGroupIndex.value = null
    } 
    // 情况 B：从功能池拖入成为一级菜单
    else if (draggingItem.value && draggingItem.value.groupIndex === null) {
      addItemAsPrimary(draggingItem.value.key, targetIndex)
      draggingItem.value = null
    }
  }

  const onItemDragStart = (groupIndex: number | null, itemIndex: number | null, key: string) => {
    draggingItem.value = { groupIndex, itemIndex, key }
  }

  const onGroupTargetDrop = (targetGroupIndex: number, targetItemIndex?: number) => {
    if (!draggingItem.value) return
    const { groupIndex, itemIndex, key } = draggingItem.value
    
    // 如果目标是 'item' 类型的一级菜单，则不允许存入子项（或者将其转为 group）
    if (menuLayout.value[targetGroupIndex].type === 'item') {
      // 这里的逻辑可以根据习惯定，目前我们只允许往 type='group' 的里扔
      return
    }

    if (groupIndex !== null && itemIndex !== null) {
      menuLayout.value[groupIndex].items.splice(itemIndex, 1)
    }

    const targetItems = menuLayout.value[targetGroupIndex].items
    if (!targetItems.includes(key)) {
      if (typeof targetItemIndex === 'number') {
        targetItems.splice(targetItemIndex, 0, key)
      } else {
        targetItems.push(key)
      }
    }
    draggingItem.value = null
  }

  return {
    menuLayout,
    unallocatedItems,
    draggingGroupIndex,
    draggingItem,
    editingGroupIndex,
    addNewGroup,
    removeGroup,
    removeItemFromGroup,
    onGroupDragStart,
    onPrimaryDrop,
    onItemDragStart,
    onGroupTargetDrop
  }
}
