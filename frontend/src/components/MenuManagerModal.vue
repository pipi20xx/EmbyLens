<script setup lang="ts">
import { ref } from 'vue'
import { 
  NModal, 
  NCard, 
  NSpace, 
  NSwitch, 
  NText, 
  NIcon,
  NButton
} from 'naive-ui'
import { DragHandleOutlined as DragIcon } from '@vicons/material'
import { menuSettings } from '../store/navigationStore'
import { menuOptions } from '../config/menu'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits(['update:show'])

// 获取原始菜单名称的映射
const getLabel = (key: string) => {
  const option = menuOptions.find(opt => opt.key === key)
  return option ? (option.label as string) : key
}

const draggedIndex = ref<number | null>(null)

const onDragStart = (index: number) => {
  draggedIndex.value = index
}

const onDragOver = (e: DragEvent) => {
  e.preventDefault()
}

const onDrop = (index: number) => {
  if (draggedIndex.value === null) return
  
  const item = menuSettings.value.splice(draggedIndex.value, 1)[0]
  menuSettings.value.splice(index, 0, item)
  draggedIndex.value = null
}

const handleClose = () => {
  emit('update:show', false)
}
</script>

<template>
  <n-modal :show="show" @update:show="handleClose" transform-origin="center">
    <n-card
      style="width: 400px"
      title="菜单排序与可见性"
      bordered
      size="medium"
      role="dialog"
      aria-modal="true"
    >
      <div class="menu-list">
        <div 
          v-for="(item, index) in menuSettings" 
          :key="item.key"
          class="menu-item"
          draggable="true"
          @dragstart="onDragStart(index)"
          @dragover="onDragOver"
          @drop="onDrop(index)"
          :class="{ 'is-dragging': draggedIndex === index }"
        >
          <n-space align="center" justify="space-between" style="width: 100%">
            <n-space align="center" :size="12">
              <n-icon class="drag-handle" size="20">
                <DragIcon />
              </n-icon>
              <n-text>{{ getLabel(item.key) }}</n-text>
            </n-space>
            <n-switch v-model:value="item.visible" size="small" />
          </n-space>
        </div>
      </div>
      <template #footer>
        <n-space justify="end">
          <n-button type="primary" @click="handleClose">完成</n-button>
        </n-space>
      </template>
    </n-card>
  </n-modal>
</template>

<style scoped>
.menu-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.menu-item {
  padding: 10px 12px;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  cursor: default;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.menu-item:hover {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: var(--primary-color);
}
.drag-handle {
  cursor: grab;
  color: rgba(255, 255, 255, 0.3);
}
.drag-handle:active {
  cursor: grabbing;
}
.is-dragging {
  opacity: 0.5;
  background-color: var(--primary-color);
}
</style>
