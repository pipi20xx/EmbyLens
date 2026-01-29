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
  NPopconfirm
} from 'naive-ui'
import { 
  AddCircleOutlineOutlined as AddIcon,
  DragIndicatorOutlined as DragIcon,
  DeleteOutlineOutlined as DeleteIcon,
  LaunchOutlined as ItemIcon
} from '@vicons/material'

import ItemPool from './menu-manager/ItemPool.vue'
import GroupCard from './menu-manager/GroupCard.vue'
import { useMenuEditor } from './menu-manager/useMenuEditor'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits(['update:show'])

const {
  menuLayout,
  unallocatedItems,
  draggingGroupIndex,
  editingGroupIndex,
  addNewGroup,
  removeGroup,
  removeItemFromGroup,
  onGroupDragStart,
  onPrimaryDrop,
  onItemDragStart,
  onGroupTargetDrop
} = useMenuEditor()

const handleClose = () => {
  emit('update:show', false)
}
</script>

<template>
  <n-modal :show="show" @update:show="handleClose" transform-origin="center">
    <n-card
      style="width: 1000px; max-height: 85vh;"
      title="动态菜单布局管理 (支持独立项 & 分组)"
      bordered
      size="medium"
      content-style="padding: 0;"
    >
      <div class="editor-container">
        <!-- 左侧：功能池 -->
        <ItemPool 
          :items="unallocatedItems" 
          @dragItem="(key) => onItemDragStart(null, null, key)"
        />

        <!-- 右侧：结构编辑器 -->
        <div class="structure-editor">
          <n-space justify="space-between" align="center" style="padding: 0 20px 12px 20px;">
            <div class="section-title">布局结构 (拖拽一级/二级)</div>
            <n-button size="small" type="primary" secondary @click="addNewGroup">
              <template #icon><n-icon><AddIcon /></n-icon></template>
              添加一级分类容器
            </n-button>
          </n-space>

          <n-scrollbar style="max-height: 65vh; padding: 0 20px;">
            <div class="primary-list">
              <div 
                v-for="(node, nIdx) in menuLayout" 
                :key="node.key"
                class="primary-node"
                @dragover.prevent
                @drop="onPrimaryDrop(nIdx)"
              >
                <!-- 情况 A：一级分类容器 -->
                <GroupCard 
                  v-if="node.type === 'group'"
                  :group="node"
                  :gIdx="nIdx"
                  :isDraggingTarget="draggingGroupIndex !== null && draggingGroupIndex !== nIdx"
                  :isEditing="editingGroupIndex === nIdx"
                  @groupDragStart="onGroupDragStart"
                  @groupDrop="onPrimaryDrop"
                  @itemDragStart="onItemDragStart"
                  @itemDrop="(gIdx, iIdx) => onGroupTargetDrop(gIdx, iIdx)"
                  @groupHeaderDrop="onGroupTargetDrop"
                  @removeGroup="removeGroup"
                  @removeItem="removeItemFromGroup"
                  @startEdit="(idx) => editingGroupIndex = idx"
                  @stopEdit="editingGroupIndex = null"
                />

                <!-- 情况 B：独立一级功能项 -->
                <div 
                  v-else
                  class="primary-item-node"
                  draggable="true"
                  @dragstart="onGroupDragStart(nIdx)"
                  :class="{ 'is-dragging': draggingGroupIndex === nIdx }"
                >
                  <n-space align="center" justify="space-between" style="width: 100%">
                    <n-space align="center" :size="12">
                      <n-icon class="drag-handle"><DragIcon /></n-icon>
                      <n-switch v-model:value="node.visible" size="small" />
                      <n-tag type="primary" size="large" round class="item-tag">
                        <template #icon><n-icon><ItemIcon /></n-icon></template>
                        {{ node.label }}
                      </n-tag>
                    </n-space>
                    
                    <n-popconfirm @positive-click="removeGroup(nIdx)">
                      <template #trigger>
                        <n-button quaternary circle size="small" type="error">
                          <template #icon><n-icon><DeleteIcon /></n-icon></template>
                        </n-button>
                      </template>
                      确定将此项从一级菜单移出吗？
                    </n-popconfirm>
                  </n-space>
                </div>
              </div>
              
              <!-- 尾部 Drop 区域 -->
              <div 
                class="drop-zone-tail" 
                @dragover.prevent 
                @drop="onPrimaryDrop(menuLayout.length)"
              >
                将项目拖拽到此处添加到底部
              </div>
            </div>
          </n-scrollbar>
        </div>
      </div>

      <template #footer>
        <n-space justify="end" style="padding: 16px;">
          <n-button type="primary" block @click="handleClose">完成布局设置并应用</n-button>
        </n-space>
      </template>
    </n-card>
  </n-modal>
</template>

<style scoped>
.editor-container {
  display: flex;
  height: 70vh;
  background-color: #101014;
}
.structure-editor { flex: 1; padding: 16px 0; }
.section-title {
  font-size: 13px; font-weight: 800; color: var(--primary-color);
  margin-bottom: 16px; text-transform: uppercase; letter-spacing: 1px;
}
.primary-list { display: flex; flex-direction: column; gap: 12px; }

.primary-item-node {
  padding: 12px 16px;
  background-color: rgba(var(--primary-color-rgb), 0.05);
  border: 1px solid rgba(var(--primary-color-rgb), 0.2);
  border-radius: 12px;
  cursor: grab;
  transition: all 0.2s;
}
.primary-item-node:hover {
  background-color: rgba(var(--primary-color-rgb), 0.1);
  border-color: var(--primary-color);
}
.primary-item-node.is-dragging { opacity: 0.4; }

.item-tag { font-weight: 700; font-size: 15px; padding: 0 16px; }

.drag-handle { color: rgba(255,255,255,0.2); cursor: grab; }

.drop-zone-tail {
  height: 60px;
  border: 2px dashed rgba(255,255,255,0.05);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255,255,255,0.15);
  font-style: italic;
  margin-top: 8px;
  transition: all 0.2s;
}
.drop-zone-tail:hover {
  border-color: var(--primary-color);
  background-color: rgba(var(--primary-color-rgb), 0.05);
  color: var(--primary-color);
}
</style>