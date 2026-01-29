<script setup lang="ts">
import { NSpace, NSwitch, NInput, NText, NIcon, NButton, NPopconfirm } from 'naive-ui'
import { 
  DragIndicatorOutlined as DragIcon,
  DeleteOutlineOutlined as DeleteIcon,
  EditOutlined as EditIcon
} from '@vicons/material'
import draggable from 'vuedraggable'
import { allMenuItems } from '../../config/menu'

const props = defineProps<{
  group: any
  gIdx: number
  isEditing: boolean
}>()

const emit = defineEmits([
  'removeGroup', 'removeItem', 'startEdit', 'stopEdit'
])

const getItemLabel = (key: string) => {
  const item = allMenuItems.find(m => m.key === key)
  return item ? (item.label as string) : key
}
</script>

<template>
  <div class="group-card">
    <!-- 分类头部 -->
    <div class="group-header">
      <n-space align="center" :size="12">
        <n-icon class="primary-drag-handle group-drag-handle"><DragIcon /></n-icon>
        <n-switch v-model:value="group.visible" size="small" />
        <n-input 
          v-if="isEditing"
          v-model:value="group.label" 
          size="small" 
          style="width: 140px"
          @blur="emit('stopEdit')"
          @keyup.enter="emit('stopEdit')"
          @click.stop
          autofocus
        />
        <n-text v-else strong class="group-label" @click.stop="emit('startEdit', gIdx)">
          {{ group.label }}
          <n-icon size="14" style="margin-left: 4px; opacity: 0.5;"><EditIcon /></n-icon>
        </n-text>
      </n-space>

      <n-popconfirm @positive-click="emit('removeGroup', gIdx)">
        <template #trigger>
          <n-button quaternary circle size="tiny" type="error">
            <template #icon><n-icon><DeleteIcon /></n-icon></template>
          </n-button>
        </template>
        删除分类？
      </n-popconfirm>
    </div>

    <!-- 子项区域：允许从池中拖入项 -->
    <draggable
      v-model="group.items"
      group="menu-items"
      item-key="self"
      class="group-content"
      ghost-class="sub-ghost"
      animation="150"
    >
      <template #item="{ element, index }">
        <div class="sub-item">
          <n-icon size="14" class="sub-drag-icon"><DragIcon /></n-icon>
          <n-text class="sub-item-text">{{ getItemLabel(element) }}</n-text>
          <n-button 
            quaternary 
            circle 
            size="tiny" 
            type="warning" 
            class="item-del-btn" 
            @click.stop="emit('removeItem', gIdx, index)"
          >
            <template #icon><n-icon><DeleteIcon /></n-icon></template>
          </n-button>
        </div>
      </template>
      <template #footer>
        <div v-if="group.items.length === 0" class="empty-hint">将功能拖拽至此</div>
      </template>
    </draggable>
  </div>
</template>

<style scoped>
.group-card {
  background-color: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s;
}

.group-header { 
  padding: 10px 16px; 
  background-color: rgba(255, 255, 255, 0.04); 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
}
.group-drag-handle { color: rgba(255,255,255,0.2); cursor: grab; }
.group-label { cursor: pointer; padding: 2px 6px; border-radius: 4px; }
.group-label:hover { background-color: rgba(255, 255, 255, 0.1); }

.group-content { 
  padding: 12px; 
  display: flex; 
  flex-wrap: wrap; 
  gap: 8px; 
  min-height: 50px; 
}

.sub-item { 
  display: flex; 
  align-items: center; 
  gap: 6px; 
  background-color: rgba(255, 255, 255, 0.06); 
  padding: 6px 10px; 
  border-radius: 6px; 
  border: 1px solid rgba(255, 255, 255, 0.1); 
  cursor: grab; 
}
.sub-item:hover { background-color: rgba(var(--primary-color-rgb), 0.1); border-color: var(--primary-color); }
.sub-drag-icon { opacity: 0.3; }
.sub-item-text { font-size: 0.85rem; }
.sub-ghost { opacity: 0.3; background: var(--primary-color-suppl) !important; }

.item-del-btn { opacity: 0; transition: opacity 0.2s; }
.sub-item:hover .item-del-btn { opacity: 1; }
.empty-hint { width: 100%; text-align: center; color: rgba(255,255,255,0.1); font-size: 12px; padding: 10px; font-style: italic; }
</style>
