<template>
  <div class="bookmark-manager-full">
    <n-card :bordered="false" size="small" class="manager-card" content-style="padding: 0;">
      <!-- 头部工具栏 -->
      <div class="header-toolbar">
        <div class="flex items-center gap-2">
          <div class="header-icon-box">
            <n-icon size="18" color="var(--primary-color)"><BookmarkIcon /></n-icon>
          </div>
          <span class="header-title">书签同步管理</span>
        </div>

        <n-space :size="8">
          <n-button secondary size="small" @click="showAddFolder = true" class="toolbar-btn">
            <template #icon><n-icon><FolderAddIcon /></n-icon></template>
            文件夹
          </n-button>
          
          <!-- 导入按钮及其隐藏输入框 -->
          <div class="inline-block">
            <n-button secondary size="small" @click="triggerFileInput" class="toolbar-btn">
              <template #icon><n-icon><ImportIcon /></n-icon></template>
              导入
            </n-button>
            <input 
              type="file" 
              ref="fileInputRef" 
              style="display: none" 
              accept=".html,.htm" 
              @change="onFileChange"
            />
          </div>

          <n-button secondary size="small" @click="handleExport" class="toolbar-btn">
            <template #icon><n-icon><ExportIcon /></n-icon></template>
            导出
          </n-button>

          <n-button quaternary type="error" size="small" @click="handleClearAll" class="toolbar-btn">
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
            collapse-mode="width"
            :collapsed-width="0"
            :width="200"
            show-trigger="arrow-circle"
            class="sider-component"
          >
            <div class="sider-inner">
              <div class="sider-section-label">收藏导航</div>
              <div 
                class="nav-node-item" 
                :class="{ 'is-active': !currentFolder }"
                @click="selectRoot"
              >
                <div class="node-indicator"></div>
                <n-icon size="18" class="node-icon"><HomeIcon /></n-icon>
                <span class="node-label">我的书签</span>
              </div>
              <n-tree
                block-line
                expand-on-click
                :data="folderTree"
                :selected-keys="selectedKeys"
                @update:selected-keys="handleTreeSelect"
                class="sidebar-tree"
              />
            </div>
          </n-layout-sider>

          <!-- 右侧：内容区 -->
          <n-layout-content class="main-content">
            <n-scrollbar style="max-height: 540px;">
              <div class="list-wrapper">
                <template v-if="currentItems.length > 0">
                  <div 
                    v-for="item in currentItems" 
                    :key="item.id"
                    class="data-row group"
                    :class="{ 'is-dragging': dragId === item.id }"
                    draggable="true"
                    @dragstart="onDragStart(item.id)"
                    @dragover.prevent
                    @dragenter="onDragEnter(item.id)"
                    @dragend="onDragEnd"
                    @click="handleItemClick(item)"
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
                  <n-empty description="暂无书签" />
                </div>
              </div>
            </n-scrollbar>
          </n-layout-content>
        </n-layout>
      </div>
    </n-card>

    <!-- 弹窗 -->
    <n-modal v-model:show="showAddBookmarkModal" preset="card" :title="editingItem ? '编辑书签' : '添加书签'" style="width: 440px" class="rounded-2xl">
      <n-form label-placement="top" size="small">
        <n-form-item label="网址">
          <n-input-group>
            <n-input v-model:value="form.url" placeholder="https://..." @blur="autoFetchTitle" />
            <n-button type="primary" secondary @click="autoFetchIcon" :loading="fetchingIcon">自动抓取</n-button>
          </n-input-group>
        </n-form-item>
        <n-form-item label="标题">
          <n-input v-model:value="form.title" placeholder="显示名称" />
        </n-form-item>
        <n-form-item label="图标 URL">
          <n-input v-model:value="form.icon" placeholder="图片 URL" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="closeBookmarkModal">取消</n-button>
          <n-button type="primary" :disabled="!form.title" @click="saveBookmark">保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showAddFolder" preset="card" title="新建文件夹" style="width: 360px" class="rounded-2xl">
      <n-form label-placement="top" size="small">
        <n-form-item label="名称">
          <n-input v-model:value="folderName" placeholder="文件夹名称" @keyup.enter="saveFolder" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddFolder = false">取消</n-button>
          <n-button type="primary" :disabled="!folderName" @click="saveFolder">创建</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue' // 显式导入 ref 以便声明 fileInputRef
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
  DeleteSweepOutlined as ClearIcon
} from '@vicons/material'
import { useBookmarkManager } from './sitenav/useBookmarkManager'

const props = defineProps<{ isModal?: boolean }>()
defineEmits(['close'])

// 声明 Template Ref
const fileInputRef = ref<HTMLInputElement | null>(null)

const {
  currentFolder, selectedKeys, dragId, showAddBookmark, showAddFolder, editingItem,
  fetchingIcon, folderName, form, currentItems, folderTree, showAddBookmarkModal,
  selectRoot, handleTreeSelect, handleItemClick, handleEdit, confirmDelete,
  handleClearAll, handleExport, handleImportHtml,
  saveBookmark, saveFolder, autoFetchTitle, autoFetchIcon, onDragStart, onDragEnter, onDragEnd
} = useBookmarkManager()

// 手动中转方法，确保连接正常
const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const onFileChange = (e: Event) => {
  handleImportHtml(e)
}

const closeBookmarkModal = () => {
  showAddBookmarkModal.value = false
}
</script>

<style scoped>
/* 保持原有样式不变 */
.bookmark-manager-full { width: 100%; height: 100%; color: #fff; }
.manager-card { background: transparent !important; border-radius: 16px; overflow: hidden; }
.header-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: rgba(255, 255, 255, 0.03); border-bottom: 1px solid rgba(255, 255, 255, 0.06); }
.header-icon-box { width: 32px; height: 32px; background: rgba(var(--primary-color-rgb, 32, 128, 240), 0.1); border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.header-title { font-size: 16px; font-weight: 700; opacity: 0.9; }
.toolbar-btn { border-radius: 8px; font-weight: 600; }
.manager-body { height: 540px; background: rgba(0, 0, 0, 0.1); }
.layout-container { height: 100%; background: transparent; }
.sider-component { background: rgba(255, 255, 255, 0.02) !important; }
.sider-inner { padding: 12px 8px; }
.sider-section-label { padding: 0 12px 8px; font-size: 11px; font-weight: 800; text-transform: uppercase; color: rgba(255, 255, 255, 0.2); letter-spacing: 1px; }
.nav-node-item { position: relative; display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 8px; cursor: pointer; font-size: 13px; color: rgba(255, 255, 255, 0.6); transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); margin-bottom: 2px; }
.nav-node-item:hover { background: rgba(255, 255, 255, 0.05); color: #fff; }
.nav-node-item.is-active { background: rgba(var(--primary-color-rgb, 32, 128, 240), 0.1); color: var(--primary-color); font-weight: 600; }
.node-indicator { position: absolute; left: 0; top: 20%; bottom: 20%; width: 3px; background: var(--primary-color); border-radius: 0 4px 4px 0; opacity: 0; transition: opacity 0.3s; }
.nav-node-item.is-active .node-indicator { opacity: 1; }
.sidebar-tree { --n-node-height: 38px; --n-node-color-hover: rgba(255, 255, 255, 0.05); --n-node-color-active: rgba(var(--primary-color-rgb, 32, 128, 240), 0.1); --n-node-text-color: rgba(255, 255, 255, 0.6); --n-node-text-color-active: var(--primary-color); --n-node-border-radius: 8px; }
.main-content { background: rgba(255, 255, 255, 0.01); }
.list-wrapper { padding: 8px; }
.data-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; border-radius: 10px; cursor: pointer; transition: all 0.2s ease; margin-bottom: 2px; }
.data-row:hover { background: rgba(255, 255, 255, 0.04); }
.data-row.is-dragging { opacity: 0.2; transform: scale(0.98); background: var(--primary-color); }
.row-main { display: flex; align-items: center; gap: 14px; flex: 1; min-width: 0; }
.row-icon { width: 36px; height: 32px; display: flex; align-items: center; justify-content: center; background: rgba(0, 0, 0, 0.2); border-radius: 8px; flex-shrink: 0; }
.icon-img { width: 20px; height: 20px; object-fit: contain; }
.row-info { display: flex; flex-direction: column; min-width: 0; gap: 2px; }
.row-title { font-size: 13px; font-weight: 600; color: rgba(255, 255, 255, 0.9); }
.row-sub { font-size: 10px; color: rgba(255, 255, 255, 0.25); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.row-actions { display: flex; gap: 6px; opacity: 0; transition: opacity 0.2s; }
.data-row:hover .row-actions { opacity: 1; }
.empty-view { padding: 120px 0; opacity: 0.3; }
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
</style>
