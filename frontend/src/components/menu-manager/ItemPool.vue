<script setup lang="ts">
import { NScrollbar, NText, NSpace, NIcon } from 'naive-ui'
import { DragIndicatorOutlined as DragIcon } from '@vicons/material'

defineProps<{
  items: any[]
}>()

const emit = defineEmits(['dragItem'])

const onDragStart = (key: string) => {
  emit('dragItem', key)
}
</script>

<template>
  <div class="item-pool">
    <div class="section-title">功能池 (拖拽分配)</div>
    <n-scrollbar style="max-height: 65vh;">
      <div class="pool-list">
        <div v-if="items.length === 0" class="empty-hint">所有功能已分配</div>
        <div 
          v-for="item in items" 
          :key="item.key"
          class="pool-item"
          draggable="true"
          @dragstart="onDragStart(item.key)"
        >
          <n-space align="center" :size="8">
            <n-icon class="drag-handle-icon"><DragIcon /></n-icon>
            <n-text strong>{{ item.label }}</n-text>
          </n-space>
          <n-text depth="3" class="item-key">{{ item.key }}</n-text>
        </div>
      </div>
    </n-scrollbar>
  </div>
</template>

<style scoped>
.item-pool {
  width: 260px;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  padding: 16px;
}
.section-title {
  font-size: 13px;
  font-weight: 800;
  color: var(--primary-color);
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.pool-list { display: flex; flex-direction: column; gap: 8px; }
.pool-item {
  padding: 12px;
  background-color: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: grab;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
}
.pool-item:hover {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: var(--primary-color);
}
.item-key { font-size: 10px; opacity: 0.4; margin-top: 4px; }
.empty-hint { padding: 20px; text-align: center; color: rgba(255, 255, 255, 0.2); font-style: italic; font-size: 13px; }
</style>
