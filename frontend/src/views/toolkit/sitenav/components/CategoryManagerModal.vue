<script setup lang="ts">
import { ref } from 'vue'
import { 
  NModal, NSpace, NInput, NInputGroup, NButton, 
  NDivider, NIcon, NText, NPopconfirm, NScrollbar,
  NUpload, NSlider, NSelect
} from 'naive-ui'
import { 
  DragIndicatorOutlined as DragIcon,
  DeleteOutlined as DeleteIcon,
  AddOutlined as AddIcon,
  CloudDownloadOutlined as ExportIcon,
  CloudUploadOutlined as ImportIcon,
  EditOutlined as EditIcon,
  CheckOutlined as SaveIcon,
  ImageOutlined as ImageIcon
} from '@vicons/material'
import { Category } from '../useSiteNav'

const props = defineProps<{
  show: boolean
  categories: Category[]
  settings: {
    background_url: string
    background_opacity: number
    background_blur: number
    background_size: string
  }
}>()

const emit = defineEmits(['update:show', 'add', 'delete', 'reorder', 'export', 'import', 'update', 'uploadBg', 'updateSettings'])

const newCatName = ref('')
const editingId = ref<number | null>(null)
const editingName = ref('')
const dragItem = ref<number | null>(null)
const dragOverItem = ref<number | null>(null)

const sizeOptions = [
  { label: '全部填充 (有裁剪)', value: 'cover' },
  { label: '完整显示 (无裁剪)', value: 'contain' },
  { label: '强制拉伸 (无黑边)', value: '100% 100%' }
]

const handleAdd = () => {
  if (!newCatName.value) return
  emit('add', newCatName.value)
  newCatName.value = ''
}

const startEdit = (cat: Category) => {
  editingId.value = cat.id
  editingName.value = cat.name
}

const saveEdit = () => {
  if (editingId.value && editingName.value) {
    emit('update', editingId.value, editingName.value)
    editingId.value = null
  }
}

const handleImport = (options: { file: { file: File } }) => {
  emit('import', options.file.file)
}

const handleUploadBg = (options: { file: { file: File } }) => {
  emit('uploadBg', options.file.file)
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
    title="高级设置 - 站点导航" 
    style="width: 480px"
    class="category-manager-modal"
  >
    <n-space vertical size="large">
      <!-- 背景外观设置 -->
      <div class="settings-section">
        <n-text depth="3" style="font-size: 12px; margin-bottom: 12px; display: block;">外观设置 (自定义背景)</n-text>
        <n-space vertical size="large">
          <n-space align="center">
            <n-upload :show-file-list="false" @change="handleUploadBg" accept=".png,.jpg,.jpeg,.webp,.svg,.gif">
              <n-button secondary size="small">
                <template #icon><n-icon><ImageIcon /></n-icon></template>
                更换背景图
              </n-button>
            </n-upload>
            <n-button secondary size="small" type="error" quaternary @click="emit('updateSettings', { background_url: '' })" v-if="settings.background_url">
              移除背景
            </n-button>
          </n-space>

          <div v-if="settings.background_url">
            <div class="setting-item">
              <span class="label">背景缩放模式</span>
              <n-select 
                :value="settings.background_size" 
                :options="sizeOptions" 
                size="small"
                @update:value="val => emit('updateSettings', { background_size: val })" 
              />
            </div>
            <div class="setting-item">
              <span class="label">背景透明度 ({{ Math.round(settings.background_opacity * 100) }}%)</span>
              <n-slider 
                :value="settings.background_opacity" 
                :min="0" :max="1" :step="0.01" 
                @update:value="val => emit('updateSettings', { background_opacity: val })" 
              />
            </div>
            <div class="setting-item">
              <span class="label">背景模糊度 ({{ settings.background_blur }}px)</span>
              <n-slider 
                :value="settings.background_blur" 
                :min="0" :max="20" :step="1" 
                @update:value="val => emit('updateSettings', { background_blur: val })" 
              />
            </div>
          </div>
        </n-space>
      </div>

      <n-divider style="margin: 8px 0" />

      <!-- 备份与恢复 -->
      <div class="backup-section">
        <n-text depth="3" style="font-size: 12px; margin-bottom: 8px; display: block;">配置备份与恢复</n-text>
        <n-space>
          <n-button secondary size="small" @click="emit('export')">
            <template #icon><n-icon><ExportIcon /></n-icon></template>
            全量备份 (.zip)
          </n-button>
          <n-upload :show-file-list="false" @change="handleImport" accept=".zip">
            <n-button secondary size="small" type="info">
              <template #icon><n-icon><ImportIcon /></n-icon></template>
              恢复备份
            </n-button>
          </n-upload>
        </n-space>
      </div>

      <n-divider style="margin: 8px 0" />

      <!-- 分类添加 -->
      <div class="add-section">
        <n-text depth="3" style="font-size: 12px; margin-bottom: 8px; display: block;">添加新分类</n-text>
        <n-input-group>
          <n-input v-model:value="newCatName" placeholder="新分类名称" @keyup.enter="handleAdd" />
          <n-button type="primary" @click="handleAdd">
            <template #icon><n-icon><AddIcon /></n-icon></template>
            添加
          </n-button>
        </n-input-group>
      </div>

      <n-divider title-placement="left" style="margin: 12px 0">已有分类 (可上下拖拽排序/点图标改名)</n-divider>
      
      <n-scrollbar style="max-height: 250px; padding-right: 12px;">
        <div class="category-list">
          <div 
            v-for="cat in categories" 
            :key="cat.id"
            class="category-item"
            :class="{ 'is-dragging': dragItem === cat.id, 'is-drag-over': dragOverItem === cat.id }"
            draggable="true"
            @dragstart="onDragStart(cat.id)"
            @dragover.prevent
            @dragenter="onDragEnter(cat.id)"
            @dragend="onDragEnd"
          >
            <div class="drag-handle"><n-icon><DragIcon /></n-icon></div>
            
            <div class="cat-content">
              <template v-if="editingId === cat.id">
                <n-input-group>
                  <n-input size="small" v-model:value="editingName" @keyup.enter="saveEdit" />
                  <n-button size="small" type="primary" @click="saveEdit">
                    <template #icon><n-icon><SaveIcon /></n-icon></template>
                  </n-button>
                </n-input-group>
              </template>
              <template v-else>
                <span class="cat-name">{{ cat.name }}</span>
                <n-button quaternary circle size="tiny" @click="startEdit(cat)" class="edit-btn">
                  <template #icon><n-icon><EditIcon /></n-icon></template>
                </n-button>
              </template>
            </div>

            <div class="cat-actions" v-if="editingId !== cat.id">
              <n-popconfirm @positive-click="emit('delete', cat.id)">
                <template #trigger>
                  <n-button quaternary circle size="small" type="error">
                    <template #icon><n-icon><DeleteIcon /></n-icon></template>
                  </n-button>
                </template>
                确定删除该分类吗？
              </n-popconfirm>
            </div>
          </div>
        </div>
      </n-scrollbar>
    </n-space>
  </n-modal>
</template>

<style scoped>
.category-list { display: flex; flex-direction: column; gap: 8px; }
.category-item {
  display: flex; align-items: center; padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px; transition: all 0.2s;
}
.category-item:hover { background: rgba(255, 255, 255, 0.06); border-color: var(--primary-color); }
.drag-handle { cursor: grab; margin-right: 12px; color: #666; }
.cat-content { flex: 1; display: flex; align-items: center; gap: 8px; }
.cat-name { font-weight: 500; }
.edit-btn { opacity: 0; transition: opacity 0.2s; }
.category-item:hover .edit-btn { opacity: 0.5; }
.edit-btn:hover { opacity: 1 !important; }
.is-dragging { opacity: 0.4; border-style: dashed; }
.is-drag-over { border: 2px solid var(--primary-color); transform: scale(1.01); }

.setting-item {
  margin-bottom: 16px;
}
.setting-item .label {
  font-size: 13px;
  display: block;
  margin-bottom: 8px;
  opacity: 0.8;
}
</style>
