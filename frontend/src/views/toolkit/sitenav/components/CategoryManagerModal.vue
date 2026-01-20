<script setup lang="ts">
import { ref } from 'vue'
import { 
  NModal, NSpace, NInput, NInputGroup, NButton, 
  NDivider, NIcon, NText, NPopconfirm, NScrollbar
} from 'naive-ui'
import { 
  DragIndicatorOutlined as DragIcon,
  DeleteOutlined as DeleteIcon,
  AddOutlined as AddIcon
} from '@vicons/material'
import { Category } from '../useSiteNav'

const props = defineProps<{
  show: boolean
  categories: Category[]
}>()

const emit = defineEmits(['update:show', 'add', 'delete', 'reorder'])
const newCatName = ref('')

// 拖拽逻辑
const dragItem = ref<number | null>(null)
const dragOverItem = ref<number | null>(null)

const handleAdd = () => {
  if (!newCatName.value) return
  emit('add', newCatName.value)
  newCatName.value = ''
}

const onDragStart = (id: number) => { dragItem.value = id }
const onDragEnter = (id: number) => { if (id !== dragItem.value) dragOverItem.value = id }
const onDragEnd = () => {
  if (dragItem.value !== null && dragOverItem.value !== null) {
    const newCats = [...props.categories]
    const fromIndex = newCats.findIndex(c => c.id === dragItem.value)
    const toIndex = newCats.findIndex(c => c.id === dragOverItem.value)
    if (fromIndex !== -1 && toIndex !== -1) {
      const [removed] = newCats.splice(fromIndex, 1)
      newCats.splice(toIndex, 0, removed)
      emit('reorder', newCats.map(c => c.id))
    }
  }
  dragItem.value = dragOverItem.value = null
}
</script>

<template>
  <n-modal 
    :show="show" 
    @update:show="val => emit('update:show', val)" 
    preset="card" 
    title="高级设置 - 分类管理" 
    style="width: 450px"
    class="category-manager-modal"
  >
    <n-space vertical size="large">
      <div class="add-section">
        <n-text depth="3" style="font-size: 12px; margin-bottom: 8px; display: block;">添加新分类</n-text>
        <n-input-group>
          <n-input v-model:value="newCatName" placeholder="例如：下载、监控、办公..." @keyup.enter="handleAdd" />
          <n-button type="primary" @click="handleAdd">
            <template #icon><n-icon><AddIcon /></n-icon></template>
            添加
          </n-button>
        </n-input-group>
      </div>

      <n-divider title-placement="left" style="margin: 12px 0">已有分类 (可上下拖拽排序)</n-divider>
      
      <n-scrollbar style="max-height: 400px; padding-right: 12px;">
        <div class="category-list">
          <div 
            v-for="cat in categories" 
            :key="cat.id"
            class="category-item"
            :class="{ 
              'is-dragging': dragItem === cat.id,
              'is-drag-over': dragOverItem === cat.id 
            }"
            draggable="true"
            @dragstart="onDragStart(cat.id)"
            @dragover.prevent
            @dragenter="onDragEnter(cat.id)"
            @dragend="onDragEnd"
          >
            <div class="drag-handle">
              <n-icon><DragIcon /></n-icon>
            </div>
            <div class="cat-name">{{ cat.name }}</div>
            <div class="cat-actions">
              <n-popconfirm @positive-click="emit('delete', cat.id)">
                <template #trigger>
                  <n-button quaternary circle size="small" type="error">
                    <template #icon><n-icon><DeleteIcon /></n-icon></template>
                  </n-button>
                </template>
                删除分类将导致该分类下的站点变为“未分类”，确定吗？
              </n-popconfirm>
            </div>
          </div>
          
          <div v-if="categories.length === 0" class="empty-cats">
            暂无分类，请从上方添加
          </div>
        </div>
      </n-scrollbar>
    </n-space>

    <template #footer>
      <div style="text-align: right; font-size: 12px; opacity: 0.5;">
        拖拽左侧图标可调整展示顺序
      </div>
    </template>
  </n-modal>
</template>

<style scoped>
.category-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  transition: all 0.2s;
  cursor: default;
}

.category-item:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--primary-color);
}

.drag-handle {
  cursor: grab;
  margin-right: 12px;
  display: flex;
  align-items: center;
  color: #666;
  transition: color 0.2s;
}

.category-item:hover .drag-handle {
  color: var(--primary-color);
}

.cat-name {
  flex: 1;
  font-weight: 500;
}

.is-dragging {
  opacity: 0.4;
  border-style: dashed;
}

.is-drag-over {
  border: 2px solid var(--primary-color);
  transform: scale(1.01);
}

.empty-cats {
  text-align: center;
  padding: 40px 0;
  color: #666;
}
</style>