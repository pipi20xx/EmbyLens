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
  NTooltip
} from 'naive-ui'
import { 
  AddCircleOutlineOutlined as AddIcon,
  DragIndicatorOutlined as DragIcon,
  DeleteOutlineOutlined as DeleteIcon,
  LaunchOutlined as ItemIcon,
  ArrowForwardOutlined as QuickAddIcon
} from '@vicons/material'
import draggable from 'vuedraggable'

import ItemPool from './menu-manager/ItemPool.vue'
import GroupCard from './menu-manager/GroupCard.vue'
import { useMenuEditor } from './menu-manager/useMenuEditor'
import { watch } from 'vue'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits(['update:show'])

const {
  menuLayout,
  unallocatedItems,
  editingGroupIndex,
  addNewGroup,
  removeGroup,
  removeItemFromGroup,
  refreshUnallocated,
  addItemAsPrimary
} = useMenuEditor()

// 监听布局变化，更新功能池
watch(menuLayout, () => {
  refreshUnallocated()
}, { deep: true })

const handleClose = () => {
  emit('update:show', false)
}
</script>

<template>
  <n-modal :show="show" @update:show="handleClose" transform-origin="center">
    <n-card
      style="width: 1000px; max-height: 85vh;"
      title="导航布局管理"
      bordered
      size="medium"
      content-style="padding: 0;"
    >
      <div class="editor-container">
        <!-- 左侧：功能池 -->
        <div class="pool-container">
          <div class="section-title">未分配功能</div>
          <n-scrollbar style="max-height: 65vh;">
            <draggable
              v-model="unallocatedItems"
              :group="{ name: 'menu-items', pull: 'clone', put: false }"
              :sort="false"
              item-key="key"
              class="pool-list"
            >
              <template #item="{ element }">
                <div class="pool-item">
                  <n-space align="center" justify="space-between" style="width: 100%">
                    <n-space align="center" :size="8">
                      <n-icon class="drag-handle-icon"><DragIcon /></n-icon>
                      <span class="pool-label">{{ element.label }}</span>
                    </n-space>
                    
                    <n-tooltip trigger="hover" placement="top">
                      <template #trigger>
                        <n-button 
                          quaternary 
                          circle 
                          size="tiny" 
                          type="primary" 
                          class="quick-add-btn"
                          @click.stop="addItemAsPrimary(element)"
                        >
                          <template #icon><n-icon><QuickAddIcon /></n-icon></template>
                        </n-button>
                      </template>
                      设为一级菜单
                    </n-tooltip>
                  </n-space>
                </div>
              </template>
            </draggable>
            <div v-if="unallocatedItems.length === 0" class="pool-empty">
              所有功能已分配
            </div>
          </n-scrollbar>
        </div>

        <!-- 右侧：结构编辑器 -->
        <div class="structure-editor">
          <n-space justify="space-between" align="center" style="padding: 0 20px 12px 20px;">
            <div class="section-title">当前布局 (拖拽排序)</div>
            <n-button size="small" type="primary" secondary @click="addNewGroup">
              <template #icon><n-icon><AddIcon /></n-icon></template>
              添加新分类
            </n-button>
          </n-space>

          <n-scrollbar style="max-height: 65vh; padding: 0 20px;">
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
                      
                      <n-popconfirm @positive-click="removeGroup(index)">
                        <template #trigger>
                          <n-button quaternary circle size="small" type="error">
                            <template #icon><n-icon><DeleteIcon /></n-icon></template>
                          </n-button>
                        </template>
                        移出一级菜单？
                      </n-popconfirm>
                    </n-space>
                  </div>
                </div>
              </template>
            </draggable>
            
            <div v-if="menuLayout.length === 0" class="empty-layout">
              列表为空，请从左侧拖入功能或添加分类
            </div>
          </n-scrollbar>
        </div>
      </div>

      <template #footer>
        <n-space justify="end" style="padding: 16px;">
          <n-button type="primary" size="large" @click="handleClose">确认并保存布局</n-button>
        </n-space>
      </template>
    </n-card>
  </n-modal>
</template>

<style scoped>
.editor-container {
  display: flex;
  height: 70vh;
  background-color: #0c0c0e;
}
.pool-container {
  width: 280px;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  padding: 16px;
}
.structure-editor { flex: 1; padding: 16px 0; }
.section-title {
  font-size: 12px; font-weight: 800; color: var(--primary-color);
  margin-bottom: 16px; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.8;
}

.pool-list { display: flex; flex-direction: column; gap: 8px; min-height: 100px; }
.pool-item {
  padding: 10px 14px;
  background-color: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: grab;
  transition: all 0.2s;
}
.pool-item:hover { background-color: rgba(255, 255, 255, 0.06); border-color: var(--primary-color); }
.pool-label { font-size: 13px; font-weight: 500; }

.quick-add-btn { opacity: 0.3; transition: all 0.2s; }
.pool-item:hover .quick-add-btn { opacity: 1; transform: scale(1.1); }

.pool-empty { padding: 20px; text-align: center; color: rgba(255, 255, 255, 0.15); font-style: italic; font-size: 12px; }

.primary-list { display: flex; flex-direction: column; gap: 12px; min-height: 200px; }
.primary-node-outer { position: relative; }

.primary-item-node {
  padding: 12px 16px;
  background-color: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  transition: all 0.2s;
}

.primary-drag-handle { color: rgba(255,255,255,0.2); cursor: grab; font-size: 20px; }
.primary-drag-handle:hover { color: var(--primary-color); }

.ghost-node { opacity: 0.3; background: var(--primary-color-suppl) !important; border: 2px dashed var(--primary-color) !important; }

.empty-layout { padding: 40px; text-align: center; color: rgba(255, 255, 255, 0.15); font-style: italic; }
</style>