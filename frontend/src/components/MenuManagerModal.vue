<script setup lang="ts">
import { 
  NModal, 
  NCard, 
  NSpace, 
  NButton,
  NScrollbar,
  NIcon,
  NTag,
  NSwitch,
  NPopconfirm,
  NTooltip,
  NText,
  useMessage
} from 'naive-ui'
import { 
  AddCircleOutlineOutlined as AddIcon,
  DragIndicatorOutlined as DragIcon,
  DeleteOutlineOutlined as DeleteIcon,
  LaunchOutlined as ItemIcon,
  ArrowForwardOutlined as QuickAddIcon,
  SettingsBackupRestoreOutlined as ResetIcon
} from '@vicons/material'
import draggable from 'vuedraggable'

import GroupCard from './menu-manager/GroupCard.vue'
import { useMenuEditor } from './menu-manager/useMenuEditor'
import { saveMenuLayoutToBackend } from '../store/navigationStore'
import { watch, ref } from 'vue'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits(['update:show'])
const message = useMessage()
const isSaving = ref(false)

const {
  menuLayout,
  unallocatedItems,
  editingGroupIndex,
  addNewGroup,
  removeGroup,
  removeItemFromGroup,
  refreshUnallocated,
  addItemAsPrimary,
  resetToDefault
} = useMenuEditor()

// 监听布局变化，更新功能池
watch(menuLayout, () => {
  refreshUnallocated()
}, { deep: true })

const handleSaveAndClose = async () => {
  isSaving.value = true
  try {
    await saveMenuLayoutToBackend(menuLayout.value)
    message.success('菜单布局保存成功')
    emit('update:show', false)
  } catch (err) {
    message.error('保存布局失败，请检查网络连接')
  } finally {
    isSaving.value = false
  }
}

const handleClose = () => {
  emit('update:show', false)
}
</script>

<template>
  <n-modal :show="show" @update:show="handleClose" transform-origin="center">
    <n-card
      class="menu-manager-card"
      title="导航布局管理"
      bordered
      size="medium"
      content-style="padding: 0; display: flex; flex-direction: column; overflow: hidden;"
    >
      <div class="editor-container">
        <!-- 左侧：功能池 -->
        <div class="pool-container">
          <div class="section-header">
            <div class="section-title">未分配功能</div>
            <div class="section-desc">可直接拖拽或点击快速添加</div>
          </div>
          
          <div class="pool-scroll-wrapper">
            <n-scrollbar trigger="none" class="custom-scrollbar">
              <draggable
                v-model="unallocatedItems"
                :group="{ name: 'menu-items', pull: 'clone', put: false }"
                :sort="false"
                item-key="key"
                class="pool-list"
              >
                <template #item="{ element }">
                  <div class="pool-item">
                    <n-space align="center" justify="space-between" :wrap="false" style="width: 100%">
                      <n-space align="center" :size="8" :wrap="false" style="overflow: hidden; flex: 1;">
                        <n-icon class="drag-handle-icon" :size="18"><DragIcon /></n-icon>
                        <span class="pool-label">{{ element.label }}</span>
                      </n-space>
                      
                      <n-popconfirm 
                        @positive-click="addItemAsPrimary(element)"
                        positive-text="确认添加"
                        negative-text="取消"
                      >
                        <template #trigger>
                          <n-tooltip trigger="hover" placement="top">
                            <template #trigger>
                              <n-button 
                                quaternary 
                                circle 
                                size="tiny" 
                                type="primary" 
                                class="quick-add-btn"
                                @click.stop
                              >
                                <template #icon><n-icon><QuickAddIcon /></n-icon></template>
                              </n-button>
                            </template>
                            快速设为一级菜单
                          </n-tooltip>
                        </template>
                        确定要将此功能直接添加为独立的一级菜单项吗？
                      </n-popconfirm>
                    </n-space>
                  </div>
                </template>
              </draggable>
              <div v-if="unallocatedItems.length === 0" class="pool-empty">
                所有功能已分配
              </div>
            </n-scrollbar>
          </div>
        </div>

        <!-- 右侧：结构编辑器 -->
        <div class="structure-editor">
          <div class="editor-header">
            <div class="header-left">
              <div class="section-title">当前布局结构</div>
              <div class="section-desc">支持嵌套拖拽排序</div>
            </div>
            <n-space>
              <n-popconfirm 
                @positive-click="resetToDefault"
                positive-text="确认重置"
                negative-text="取消"
              >
                <template #trigger>
                  <n-button quaternary size="small" type="warning">
                    <template #icon><n-icon><ResetIcon /></n-icon></template>
                    恢复默认布局
                  </n-button>
                </template>
                确定要放弃当前所有自定义改动，恢复到系统默认布局吗？
              </n-popconfirm>

              <n-button type="primary" secondary size="small" @click="addNewGroup">
                <template #icon><n-icon><AddIcon /></n-icon></template>
                添加新分类容器
              </n-button>
            </n-space>
          </div>

          <div class="editor-scroll-wrapper">
            <n-scrollbar trigger="none" class="custom-scrollbar">
              <div class="editor-content-wrapper">
                <draggable
                  v-model="menuLayout"
                  group="primary-groups"
                  item-key="key"
                  handle=".primary-drag-handle"
                  class="primary-list"
                  ghost-class="ghost-node"
                  animation="200"
                >
                  <template #item="{ element, index }">
                    <div class="primary-node-outer">
                      <!-- 分类容器 -->
                      <GroupCard 
                        v-if="element.type === 'group'"
                        :group="element"
                        :gIdx="index"
                        :isEditing="editingGroupIndex === index"
                        @removeGroup="removeGroup"
                        @removeItem="removeItemFromGroup"
                        @startEdit="(idx) => editingGroupIndex = idx"
                        @stopEdit="editingGroupIndex = null"
                      />

                      <!-- 独立一级项 -->
                      <div 
                        v-else
                        class="primary-item-node"
                      >
                        <n-space align="center" justify="space-between" style="width: 100%">
                          <n-space align="center" :size="12">
                            <n-icon class="primary-drag-handle"><DragIcon /></n-icon>
                            <n-switch v-model:value="element.visible" size="small" />
                            <n-tag type="primary" size="large" round class="item-tag">
                              <template #icon><n-icon><ItemIcon /></n-icon></template>
                              {{ element.label }}
                            </n-tag>
                          </n-space>
                          
                          <n-popconfirm 
                            @positive-click="removeGroup(index)"
                            positive-text="确认移出"
                            negative-text="取消"
                          >
                            <template #trigger>
                              <n-button quaternary circle size="small" type="error">
                                <template #icon><n-icon><DeleteIcon /></n-icon></template>
                              </n-button>
                            </template>
                            确定要将此项从一级菜单中移出吗？
                          </n-popconfirm>
                        </n-space>
                      </div>
                    </div>
                  </template>
                </draggable>
                
                <div v-if="menuLayout.length === 0" class="empty-layout">
                  <div class="empty-text">布局为空</div>
                  <div class="empty-subtext">请从左侧拖入功能或添加新分类</div>
                </div>
              </div>
            </n-scrollbar>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="modal-footer">
          <n-space justify="end" align="center">
            <n-text depth="3" size="small" style="margin-right: 12px;">提示：更改会实时自动同步至云端配置</n-text>
            <n-button 
              type="primary" 
              size="large" 
              style="min-width: 200px;" 
              :loading="isSaving"
              @click="handleSaveAndClose"
            >
              完成并保存布局
            </n-button>
          </n-space>
        </div>
      </template>
    </n-card>
  </n-modal>
</template>

<style scoped>
.menu-manager-card {
  width: 90vw;
  max-width: 1400px;
  height: 85vh;
}

.editor-container {
  display: flex;
  flex: 1;
  background-color: #0c0c0e;
  overflow: hidden;
}

.pool-container {
  width: 320px;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
}

.pool-scroll-wrapper, .editor-scroll-wrapper {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.custom-scrollbar {
  flex: 1;
  height: 100%;
}

.section-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.section-title {
  font-size: 15px;
  font-weight: 800;
  color: var(--primary-color);
  text-transform: uppercase;
  letter-spacing: 1.5px;
}

.section-desc {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  margin-top: 4px;
}

.pool-list {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pool-item {
  padding: 12px 14px;
  background-color: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: grab;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.pool-item:hover {
  background-color: rgba(255, 255, 255, 0.06);
  border-color: var(--primary-color);
  transform: translateX(4px);
}

.quick-add-btn { opacity: 0; transition: all 0.2s; }
.pool-item:hover .quick-add-btn { opacity: 1; }

.structure-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.editor-header {
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.editor-content-wrapper {
  padding: 24px;
  box-sizing: border-box;
}

.primary-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 60px;
}

.primary-item-node {
  padding: 16px 20px;
  background-color: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
}

.ghost-node {
  opacity: 0.4;
  border: 2px dashed var(--primary-color) !important;
  background: rgba(var(--primary-color-rgb), 0.1) !important;
}

.modal-footer {
  padding: 16px 24px;
  background-color: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.pool-empty { padding: 40px 20px; text-align: center; color: rgba(255,255,255,0.1); font-style: italic; }
.empty-layout { padding: 80px 0; text-align: center; border: 2px dashed rgba(255, 255, 255, 0.05); border-radius: 20px; }
.empty-text { font-size: 18px; font-weight: 700; color: rgba(255, 255, 255, 0.1); }

.item-tag { font-weight: 700; font-size: 15px; padding: 0 20px; }
.primary-drag-handle { color: rgba(255,255,255,0.15); cursor: grab; font-size: 22px; }
.primary-drag-handle:hover { color: var(--primary-color); }
</style>