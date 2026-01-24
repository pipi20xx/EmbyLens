<script setup lang="ts">
import { 
  NModal, NSpace, NIcon, NTabs, NTabPane
} from 'naive-ui'
import { 
  PaletteOutlined as PaletteIcon,
  CategoryOutlined as CategoryIcon,
  StorageOutlined as StorageIcon
} from '@vicons/material'
import { Category } from '../useSiteNav'

// 导入物理隔离的积木组件
import AppearancePanel from './settings/AppearancePanel.vue'
import CategoryPanel from './settings/CategoryPanel.vue'
import DataPanel from './settings/DataPanel.vue'

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

const emit = defineEmits([
  'update:show', 'add', 'delete', 'reorder', 
  'export', 'import', 'update', 'uploadBg', 'updateSettings'
])

// 中转子组件事件
const handleImport = (file: File) => emit('import', file)
const handleUploadBg = (file: File) => emit('uploadBg', file)
</script>

<template>
  <n-modal 
    :show="show" 
    @update:show="val => emit('update:show', val)" 
    preset="card" 
    title="高级设置 - 站点导航" 
    style="width: 550px"
    class="category-manager-modal"
  >
    <n-tabs type="line" animated>
      <!-- 外观设置积木 -->
      <n-tab-pane name="appearance">
        <template #tab>
          <n-space :size="4" align="center">
            <n-icon><PaletteIcon /></n-icon> 外观设置
          </n-space>
        </template>
        <AppearancePanel 
          :settings="settings" 
          @uploadBg="handleUploadBg"
          @updateSettings="s => emit('updateSettings', s)"
        />
      </n-tab-pane>

      <!-- 分类管理积木 -->
      <n-tab-pane name="categories">
        <template #tab>
          <n-space :size="4" align="center">
            <n-icon><CategoryIcon /></n-icon> 分类管理
          </n-space>
        </template>
        <CategoryPanel 
          :categories="categories"
          @add="name => emit('add', name)"
          @delete="id => emit('delete', id)"
          @reorder="ids => emit('reorder', ids)"
          @update="(id, name) => emit('update', id, name)"
        />
      </n-tab-pane>

      <!-- 数据管理积木 -->
      <n-tab-pane name="storage">
        <template #tab>
          <n-space :size="4" align="center">
            <n-icon><StorageIcon /></n-icon> 数据管理
          </n-space>
        </template>
        <DataPanel 
          @export="emit('export')"
          @import="handleImport"
        />
      </n-tab-pane>
    </n-tabs>
  </n-modal>
</template>

<style scoped>
/* 主容器样式，保持简洁 */
.category-manager-modal {
  border-radius: 12px;
}
</style>