import { ref, computed } from 'vue'
import { menuLayout, MenuGroup } from '../../store/navigationStore'
import { allMenuItems } from '../../config/menu'

export function useMenuEditor() {
  const editingGroupIndex = ref<number | null>(null)

  // 计算已分配的项，用于从功能池中排除
  const allocatedItemKeys = computed(() => {
    const keys = new Set<string>()
    menuLayout.value.forEach(g => {
      if (g.type === 'item') {
        keys.add(g.key)
      } else if (g.items) {
        g.items.forEach(k => keys.add(k))
      }
    })
    return keys
  })

  const unallocatedItems = ref([...allMenuItems.filter(m => !allocatedItemKeys.value.has(m.key as string))])

  // 动态更新功能池（当 menuLayout 变化时）
  const refreshUnallocated = () => {
    unallocatedItems.value = allMenuItems.filter(m => !allocatedItemKeys.value.has(m.key as string))
  }

  const addNewGroup = () => {
    menuLayout.value.push({
      key: `group-${Date.now()}`,
      label: '新分组',
      visible: true,
      type: 'group',
      items: []
    })
  }

  const removeGroup = (index: number) => {
    menuLayout.value.splice(index, 1)
  }

  const removeItemFromGroup = (groupIndex: number, itemIndex: number) => {
    menuLayout.value[groupIndex].items.splice(itemIndex, 1)
  }

  const addItemAsPrimary = (item: any) => {
    menuLayout.value.push({
      key: item.key,
      label: item.label,
      visible: true,
      type: 'item',
      items: []
    })
  }

  // 处理从功能池拖入一级菜单的行为（Draggable 会自动处理数组，但我们需要确保类型正确）
  const onPoolToPrimary = (evt: any) => {
    if (evt.added) {
      const item = evt.added.element
      // 将普通菜单项包装成 MenuGroup 结构
      const idx = evt.added.newIndex
      menuLayout.value[idx] = {
        key: item.key,
        label: item.label,
        visible: true,
        type: 'item',
        items: []
      }
    }
  }

  return {
    menuLayout,
    unallocatedItems,
    editingGroupIndex,
    addNewGroup,
    removeGroup,
    removeItemFromGroup,
    refreshUnallocated,
    onPoolToPrimary,
    addItemAsPrimary
  }
}
