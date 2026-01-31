<template>
  <div class="bookmark-manager-layout" :class="{ 'is-modal': isModal }">
    <!-- 页面标题区 - 仅在非弹窗模式下显示 -->
    <div v-if="!isModal" class="page-header">
      <n-h2 prefix="bar" align-text><n-text type="primary">书签同步管理</n-text></n-h2>
      <n-text depth="3">跨平台书签统一管理，支持智能体检、分类组织及高效导入导出。</n-text>
    </div>

    <n-card 
      :bordered="false" 
      size="small" 
      class="manager-card" 
      :embedded="!isModal"
      content-style="padding: 0; display: flex; flex-direction: column; height: 100%;"
    >
      <!-- 头部工具栏 -->
      <div class="header-toolbar">
        <div class="header-left-section" v-if="isModal">
          <div class="header-icon-box">
            <n-icon size="18" color="var(--primary-color)"><BookmarkIcon /></n-icon>
          </div>
          <span class="header-title">书签同步管理</span>
        </div>

        <div class="search-box">
          <n-input v-model:value="searchQuery" placeholder="搜索书签..." size="small" round clearable>
            <template #prefix>
              <n-icon :component="SearchIcon" />
            </template>
          </n-input>
        </div>

        <n-space :size="8" class="toolbar-actions">
          <n-button secondary type="primary" size="small" @click="handleAIAnalyze" class="toolbar-btn ai-btn">
            <template #icon><n-icon><LabIcon /></n-icon></template>
            AI 智能整理
          </n-button>

          <n-button secondary size="small" @click="showHealthModal = true" class="toolbar-btn">
            <template #icon><n-icon><HealthIcon /></n-icon></template>
            体检中心
          </n-button>

          <n-button secondary size="small" @click="showAddFolder = true" class="toolbar-btn">
            <template #icon><n-icon><FolderAddIcon /></n-icon></template>
            新建文件夹
          </n-button>
          
          <n-button secondary size="small" @click="triggerFileInput" class="toolbar-btn">
            <template #icon><n-icon><ImportIcon /></n-icon></template>
            导入
            <input 
              type="file" 
              ref="fileInputRef" 
              style="display: none" 
              accept=".html,.htm" 
              @change="onFileChange"
            />
          </n-button>

          <n-button secondary size="small" @click="handleExport" class="toolbar-btn">
            <template #icon><n-icon><ExportIcon /></n-icon></template>
            导出
          </n-button>

          <n-button secondary type="error" size="small" @click="handleClearAll" class="toolbar-btn">
            <template #icon><n-icon><ClearIcon /></n-icon></template>
            清空
          </n-button>

          <n-button type="primary" size="small" @click="showAddBookmark = true" class="toolbar-btn">
            <template #icon><n-icon><AddIcon /></n-icon></template>
            添加书签
          </n-button>
          
          <n-button v-if="isModal" circle quaternary size="small" @click="$emit('close')">
            <template #icon><n-icon size="18"><CloseIcon /></n-icon></template>
          </n-button>
        </n-space>
      </div>

      <div class="manager-body">
        <n-layout has-sider position="static" class="layout-container">
          <!-- 左侧：侧边栏 -->
          <n-layout-sider
            bordered
            :width="siderWidth"
            class="sider-component"
          >
            <div class="resize-handle" @mousedown.prevent="startResize"></div>
            <div class="sider-inner">
              <div class="sider-section-label">收藏夹目录</div>
              <n-tree
                block-line
                expand-on-click
                draggable
                default-expand-all
                :data="folderTree"
                :selected-keys="selectedKeys"
                :node-props="nodeProps"
                @update:selected-keys="handleTreeSelect"
                @drop="handleTreeDrop"
                class="sidebar-tree"
              />
              <n-dropdown
                placement="bottom-start"
                trigger="manual"
                :x="contextMenuX"
                :y="contextMenuY"
                :options="contextMenuOptions"
                :show="showContextMenu"
                :on-clickoutside="() => showContextMenu = false"
                @select="handleContextSelect"
              />
            </div>
          </n-layout-sider>

          <!-- 右侧：内容区 -->
          <n-layout-content class="main-content">
            <n-scrollbar class="main-scrollbar">
              <div class="list-wrapper" @click.self="onBackgroundClick">
                <template v-if="currentItems.length > 0">
                  <div 
                    v-for="item in currentItems" 
                    :key="item.id"
                    class="data-row group"
                    :class="{ 'is-dragging': dragId === item.id, 'selected': selectedItemIds.has(item.id) }"
                    draggable="true"
                    @dragstart="onDragStart($event, item.id)"
                    @dragover.prevent
                    @dragenter="onDragEnter(item.id)"
                    @dragend="onDragEnd"
                    @click="handleSelect(item, $event)"
                    @dblclick="handleItemClick(item)"
                  >
                    <div class="row-main">
                      <div class="row-icon">
                        <n-icon v-if="item.type === 'folder'" size="20" color="#f0a020"><FolderIcon /></n-icon>
                        <img v-else-if="item.icon" :src="item.icon" class="icon-img" />
                        <n-icon v-else size="18" class="opacity-20"><WebIcon /></n-icon>
                      </div>
                      <div class="row-info">
                        <div class="row-title">{{ item.title }}</div>
                        <div class="row-sub" v-if="item.type === 'file'">{{ item.url }}</div>
                      </div>
                    </div>
                    <div class="row-actions">
                      <n-button circle quaternary size="tiny" @click.stop="handleEdit(item)" class="action-btn edit">
                        <template #icon><n-icon size="14"><EditIcon /></n-icon></template>
                      </n-button>
                      <n-button circle quaternary size="tiny" @click.stop="confirmDelete(item)" class="action-btn delete">
                        <template #icon><n-icon size="14"><DeleteIcon /></n-icon></template>
                      </n-button>
                    </div>
                  </div>
                </template>
                <div v-else class="empty-view">
                  <n-empty description="暂无书签数据" />
                </div>
              </div>
            </n-scrollbar>
          </n-layout-content>
        </n-layout>
      </div>
    </n-card>

    <!-- 弹窗部分 -->
    <n-modal v-model:show="showAddBookmarkModal" preset="card" :title="editingItem ? '编辑书签' : '添加书签'" style="width: 440px" class="standard-modal">
      <n-form label-placement="top" size="small">
        <n-form-item label="书签链接">
          <n-input-group>
            <n-input v-model:value="form.url" placeholder="https://..." @blur="autoFetchTitle" />
            <n-button type="primary" secondary @click="autoFetchIcon" :loading="fetchingIcon">抓取</n-button>
          </n-input-group>
        </n-form-item>
        <n-form-item label="显示名称">
          <n-input v-model:value="form.title" placeholder="请输入标题" />
        </n-form-item>
        <n-form-item label="图标地址">
          <n-input v-model:value="form.icon" placeholder="选填，图标 URL" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddBookmarkModal = false">取消</n-button>
          <n-button type="primary" :disabled="!form.title" @click="saveBookmark">保存书签</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showAddFolder" preset="card" title="新建文件夹" style="width: 360px" class="standard-modal">
      <n-form label-placement="top" size="small">
        <n-form-item label="文件夹名称">
          <n-input v-model:value="folderName" placeholder="请输入名称" @keyup.enter="saveFolder" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddFolder = false">取消</n-button>
          <n-button type="primary" :disabled="!folderName" @click="saveFolder">立即创建</n-button>
        </n-space>
      </template>
    </n-modal>

    <BookmarkHealthModal
      v-model:show="showHealthModal"
      v-model:active-tab="activeTab"
      :duplicates="duplicates"
      :loading-duplicates="loadingDuplicates"
      :health-results="healthResults"
      :health-progress="healthProgress"
      :is-scanning-health="isScanningHealth"
      :bookmarks="bookmarks"
      @scan-duplicates="scanDuplicates"
      @delete-group="handleDeleteAllInGroup"
      @merge-duplicate="handleMergeDuplicate"
      @merge-all-duplicates="handleMergeAllDuplicates"
      @scan-health="() => scanHealth(bookmarks)"
      @stop-scan="stopScanHealth"
      @delete-dead="handleDeleteDead"
      @delete-batch-dead="handleDeleteBatchDead"
    />
  </div>
</template>

<script setup lang="ts">
import { h, ref, nextTick } from 'vue'
import { 
  BookmarkBorderOutlined as BookmarkIcon,
  CreateNewFolderOutlined as FolderAddIcon,
  AddCircleOutlineOutlined as AddIcon,
  CloseOutlined as CloseIcon,
  FolderOutlined as FolderIcon,
  LanguageOutlined as WebIcon,
  EditOutlined as EditIcon,
  DeleteOutlineOutlined as DeleteIcon,
  HomeOutlined as HomeIcon,
  FileDownloadOutlined as ImportIcon,
  FileUploadOutlined as ExportIcon,
  DeleteSweepOutlined as ClearIcon,
  SearchOutlined as SearchIcon,
  MedicalServicesOutlined as HealthIcon,
  ScienceOutlined as LabIcon
} from '@vicons/material'
import { useBookmarkManager } from './bookmark/useBookmarkManager'
import BookmarkHealthModal from './bookmark/components/BookmarkHealthModal.vue'
import { NIcon } from 'naive-ui'

const props = defineProps<{ isModal?: boolean }>()
defineEmits(['close'])

const fileInputRef = ref<HTMLInputElement | null>(null)

const {
  currentFolder, selectedKeys, dragId, showAddBookmark, showAddFolder, editingItem,
  fetchingIcon, folderName, form, currentItems, folderTree, showAddBookmarkModal,
  selectRoot, handleTreeSelect, handleItemClick, handleEdit, confirmDelete,
  handleClearAll, handleExport, handleImportHtml, handleTreeDrop,
  saveBookmark, saveFolder, autoFetchTitle, autoFetchIcon, onDragStart, onDragEnter, onDragEnd,
  handleAIAnalyze,
  nodeProps: dndNodeProps, selectedItemIds, handleSelect, searchQuery,
  showHealthModal, activeTab, duplicates, loadingDuplicates, scanDuplicates, handleMergeDuplicate, handleMergeAllDuplicates, handleDeleteAllInGroup,
  healthResults, healthProgress, isScanningHealth, scanHealth, stopScanHealth, handleDeleteDead, handleDeleteBatchDead, bookmarks, findItemById
} = useBookmarkManager()

const showContextMenu = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextMenuNode = ref<any>(null)

const contextMenuOptions = [
  {
    label: () => h('div', { style: 'display: flex; align-items: center; justify-content: flex-start; height: 24px;' }, '删除文件夹'),
    key: 'delete'
  }
]

const handleNodeContextMenu = ({ node, event }: { node: any, event: MouseEvent }) => {
  event.preventDefault()
  event.stopPropagation()
  showContextMenu.value = false
  nextTick().then(() => {
    contextMenuNode.value = node
    contextMenuX.value = event.clientX
    contextMenuY.value = event.clientY
    showContextMenu.value = true
  })
}

const nodeProps = ({ option }: { option: any }) => {
  const baseProps = dndNodeProps({ option })
  return {
    ...baseProps,
    onContextmenu: (e: MouseEvent) => {
      handleNodeContextMenu({ node: option, event: e })
    }
  }
}

const handleContextSelect = (key: string | number) => {
  showContextMenu.value = false
  if (key === 'delete' && contextMenuNode.value) {
    if (contextMenuNode.value.key === 'root') return
    
    // Try to find the real bookmark item from state
    const realItem = findItemById(bookmarks.value, contextMenuNode.value.key)
    
    if (realItem) {
      confirmDelete(realItem)
    } else {
      // Fallback: construct a partial object if not found (should be rare)
      confirmDelete({ 
        id: contextMenuNode.value.key, 
        title: contextMenuNode.value.label, 
        type: 'folder' 
      } as any)
    }
  }
}

const STORAGE_KEY_SIDER_WIDTH = 'lens_bookmark_sider_width'
const storedWidth = localStorage.getItem(STORAGE_KEY_SIDER_WIDTH)
const siderWidth = ref(storedWidth ? parseInt(storedWidth, 10) : 220)
const isResizing = ref(false)

const startResize = (e: MouseEvent) => {
  isResizing.value = true
  const startX = e.clientX
  const startWidth = siderWidth.value

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizing.value) return
    const newWidth = startWidth + (e.clientX - startX)
    if (newWidth > 160 && newWidth < 600) {
      siderWidth.value = newWidth
    }
  }

  const handleMouseUp = () => {
    isResizing.value = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    localStorage.setItem(STORAGE_KEY_SIDER_WIDTH, siderWidth.value.toString())
  }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const triggerFileInput = () => { fileInputRef.value?.click() }
const onFileChange = (e: Event) => { handleImportHtml(e) }
const onBackgroundClick = () => { selectedItemIds.clear() }
</script>

<style scoped>
.bookmark-manager-layout {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.bookmark-manager-layout.is-modal {
  height: 96vh;
}

.manager-card {
  flex: 1;
  min-height: 0;
  border-radius: 12px;
  overflow: hidden;
}

.header-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  gap: 16px;
}

.toolbar-btn {
  font-weight: 600;
}

.header-left-section {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.header-icon-box {
  width: 32px;
  height: 32px;
  background: rgba(var(--primary-color-rgb), 0.1);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-color);
}

.search-box {
  flex: 1;
  max-width: 400px;
}

.toolbar-actions {
  flex-shrink: 0;
}

.manager-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.layout-container {
  flex: 1;
  height: 100%;
  background: transparent;
}

.sider-component {
  background: transparent !important;
  position: relative;
}

.resize-handle {
  position: absolute;
  top: 0;
  right: 0;
  width: 6px;
  height: 100%;
  cursor: col-resize;
  z-index: 100;
  background-color: transparent;
  transition: background-color 0.2s;
}

.resize-handle:hover {
  background-color: rgba(var(--primary-color-rgb), 0.5);
}

.sider-inner {
  padding: 12px 8px;
}

.sider-section-label {
  padding: 0 12px 8px;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--text-color);
  opacity: 0.3;
  letter-spacing: 1px;
}

.sidebar-tree {
  --n-node-height: 38px;
  --n-node-color-hover: rgba(255, 255, 255, 0.05);
  --n-node-color-active: rgba(var(--primary-color-rgb), 0.1);
  --n-node-text-color: var(--text-color);
  --n-node-text-color-active: var(--primary-color);
  --n-node-border-radius: 8px;
}

.main-content {
  background: transparent;
}

.list-wrapper {
  padding: 12px;
  min-height: 100%;
}

.data-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 4px;
  border: 1px solid transparent;
}

.data-row:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.05);
}

.data-row.is-dragging {
  opacity: 0.3;
  transform: scale(0.98);
  background: var(--primary-color);
}

.data-row.selected {
  background: rgba(var(--primary-color-rgb), 0.1);
  border-color: rgba(var(--primary-color-rgb), 0.2);
}

.row-main {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  min-width: 0;
}

.row-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  flex-shrink: 0;
}

.icon-img {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.row-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.row-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
  opacity: 0.9;
}

.row-sub {
  font-size: 11px;
  color: var(--text-color);
  opacity: 0.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.data-row:hover .row-actions {
  opacity: 1;
}

.empty-view {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.5;
}

:deep(.n-h2 .n-text--primary-type) {
  color: var(--primary-color);
}

.standard-modal {
  border-radius: 16px;
}
</style>