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

const getItemLabel = (element: any) => {
  if (typeof element === 'string') {
    const item = allMenuItems.find(m => m.key === element)
    return item ? (item.label as string) : element
  }
  return element?.label || element?.key || JSON.stringify(element)
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
          style="width: 180px"
          @blur="emit('stopEdit')"
          @keyup.enter="emit('stopEdit')"
          @click.stop
          autofocus
        />
        <n-text v-else strong class="group-label" @click.stop="emit('startEdit', gIdx)">
          {{ group.label }}
          <n-icon size="14" class="edit-icon"><EditIcon /></n-icon>
        </n-text>
      </n-space>

      <n-popconfirm 
        @positive-click="emit('removeGroup', gIdx)"
        positive-text="确认删除"
        negative-text="取消"
      >
        <template #trigger>
          <n-button quaternary circle size="small" type="error">
            <template #icon><n-icon><DeleteIcon /></n-icon></template>
          </n-button>
        </template>
        确定要删除此分类及其包含的所有配置吗？此操作不可撤销。
      </n-popconfirm>
    </div>

    <!-- 子项区域 -->
    <draggable
      v-model="group.items"
      group="menu-items"
      :item-key="(item: any) => item"
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
        <div v-if="group.items.length === 0" class="empty-hint">将功能拖拽至此进行归类</div>
      </template>
    </draggable>
  </div>
</template>

<style scoped>
.group-card {
  background-color: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.group-card:hover {
  border-color: rgba(var(--primary-color-rgb), 0.3);
  background-color: rgba(255, 255, 255, 0.04);
}

.group-header { 
  padding: 14px 20px; 
  background-color: rgba(255, 255, 255, 0.05); 
  display: flex; 
  justify-content: space-between; 
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.group-drag-handle { color: rgba(255,255,255,0.2); cursor: grab; }
.group-label { cursor: pointer; padding: 4px 8px; border-radius: 6px; font-size: 15px; color: var(--primary-color); }
.group-label:hover { background-color: rgba(255, 255, 255, 0.08); }
.edit-icon { margin-left: 6px; opacity: 0.3; transition: opacity 0.2s; }
.group-label:hover .edit-icon { opacity: 0.8; }

.group-content { 
  padding: 16px; 
  display: flex; 
  flex-wrap: wrap; 
  gap: 10px; 
  min-height: 70px;
  background-image: radial-gradient(rgba(255,255,255,0.02) 1px, transparent 0);
  background-size: 20px 20px;
}

.sub-item { 
  display: flex; 
  align-items: center; 
  gap: 8px; 
  background-color: rgba(255, 255, 255, 0.08); 
  padding: 8px 14px; 
  border-radius: 8px; 
  border: 1px solid rgba(255, 255, 255, 0.1); 
  cursor: grab;
  transition: all 0.2s;
}
.sub-item:hover { 
  background-color: rgba(var(--primary-color-rgb), 0.15); 
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
.sub-drag-icon { opacity: 0.3; }
.sub-item-text { font-size: 0.9rem; font-weight: 500; }
.sub-ghost { opacity: 0.3; background: var(--primary-color-suppl) !important; transform: scale(0.95); }

.item-del-btn { opacity: 0; transition: opacity 0.2s; margin-left: 4px; }
.sub-item:hover .item-del-btn { opacity: 1; }
.empty-hint { width: 100%; text-align: center; color: rgba(255,255,255,0.1); font-size: 13px; padding: 20px; font-style: italic; }
</style>
