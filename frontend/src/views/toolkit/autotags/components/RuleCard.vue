<template>
  <n-card 
    size="small" 
    class="rule-card" 
    :class="{ 'is-dragging': isDragging }"
    :title="rule.name" 
    hoverable
    draggable="true"
    @dragstart="onDragStart"
    @dragend="onDragEnd"
    @dragover.prevent
    @click="$emit('edit')"
  >
    <template #header-extra>
      <n-space :size="4" align="center">
        <!-- 拖拽手柄图标 -->
        <n-icon size="18" class="drag-handle" @mousedown.stop>
          <DragIcon />
        </n-icon>
        
        <n-popconfirm @positive-click.stop="$emit('delete')">
          <template #trigger>
            <n-button quaternary circle size="tiny" type="error" @click.stop>
              <template #icon><n-icon><DeleteIcon /></n-icon></template>
            </n-button>
          </template>
          确认删除？
        </n-popconfirm>
      </n-space>
    </template>
    
    <n-space vertical :size="4">
      <n-space align="center">
        <n-tag size="small" :bordered="false" type="primary" round>{{ rule.tag }}</n-tag>
        <n-text depth="3" style="font-size: 12px">[{{ typeLabel }}]</n-text>
      </n-space>
      <div class="rule-summary">
        <n-text depth="3" style="font-size: 11px">
          {{ summaryText }}
        </n-text>
      </div>
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { NCard, NSpace, NButton, NIcon, NTag, NText, NPopconfirm } from 'naive-ui'
import { 
  DragIndicatorOutlined as DragIcon,
  DeleteOutlineOutlined as DeleteIcon
} from '@vicons/material'

const props = defineProps<{ 
  rule: any,
  index: number
}>()

const emit = defineEmits(['edit', 'delete', 'drag-start', 'drag-end'])

const isDragging = ref(false)

const typeLabel = computed(() => {
  const map: any = { 'all': '全部', 'movie': '仅电影', 'series': '仅剧集' }
  return map[props.rule.item_type] || '全部'
})

const summaryText = computed(() => {
  const c = props.rule.conditions
  const parts = []
  if (c.countries?.length) parts.push(`地区: ${c.countries.join('/')}`)
  if (c.genres?.length) parts.push(`流派: ${c.genres.join('/')}`)
  if (c.years_text) parts.push(`年份: ${c.years_text}`)
  return parts.join(' | ') || '无限制条件'
})

const onDragStart = (e: DragEvent) => {
  isDragging.value = true
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', props.index.toString())
  }
  emit('drag-start', props.index)
}

const onDragEnd = () => {
  isDragging.value = false
  emit('drag-end')
}
</script>

<style scoped>
.rule-card { cursor: grab; transition: all 0.2s ease; border: 1px solid transparent; }
.rule-card:active { cursor: grabbing; }
.rule-card:hover { border-color: var(--n-primary-color); transform: translateY(-2px); }
.rule-card.is-dragging { opacity: 0.5; border: 1px dashed var(--n-primary-color); }

.drag-handle { color: #666; cursor: grab; margin-right: 8px; }
.drag-handle:hover { color: var(--n-primary-color); }

.rule-summary { height: 32px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; line-height: 1.4; }
</style>