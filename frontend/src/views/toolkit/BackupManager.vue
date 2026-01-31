<template>
  <div class="backup-manager">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">数据备份管理</n-text></n-h2>
        <n-text depth="3">
          支持多模式增量备份，内置针对 <n-text type="info">云盘 (CloudDrive/Rclone)</n-text>、SSD 及 HDD 的传输优化逻辑。
        </n-text>
      </div>

      <!-- 任务列表组件 -->
      <task-panel 
        ref="taskPanelRef" 
        @add="handleAddTask" 
        @edit="handleEditTask" 
        @run="handleRunTask" 
        @view-history="handleViewHistory"
      />

      <!-- 历史记录组件 -->
      <history-panel ref="historyPanelRef" />
    </n-space>

    <!-- 任务历史弹窗 (乐高组件) -->
    <history-modal 
      v-model:show="showHistoryModal" 
      :task-id="historyTaskId" 
      :task-name="historyTaskName" 
    />

    <!-- 任务编辑弹窗 (乐高组件) -->
    <task-edit-modal 
      v-model:show="showEditModal" 
      :task="editTask" 
      @save="saveTask" 
      @browse="openBrowser" 
    />

    <!-- 路径浏览器 (乐高组件) -->
    <path-browser-modal 
      v-model:show="showBrowser" 
      :initial-path="browserInitialPath" 
      @select="handlePathSelect" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NSpace, NH2, NText, useMessage } from 'naive-ui'

// 导入乐高组件
import TaskPanel from './backup/components/TaskPanel.vue'
import HistoryPanel from './backup/components/HistoryPanel.vue'
import TaskEditModal from './backup/components/TaskEditModal.vue'
import PathBrowserModal from './backup/components/PathBrowserModal.vue'
import HistoryModal from './backup/components/HistoryModal.vue'

// 导入提取的逻辑
import { useBackupTasks } from './backup/hooks/useBackupTasks'
import { useBackupBrowser } from './backup/hooks/useBackupBrowser'

const message = useMessage()

const taskPanelRef = ref()
const historyPanelRef = ref()

const showHistoryModal = ref(false)
const historyTaskId = ref('')
const historyTaskName = ref('')

// 1. 任务管理逻辑
const { 
  showEditModal, editTask, handleAddTask, handleEditTask, saveTask, handleRunTask: runTask 
} = useBackupTasks(() => taskPanelRef.value?.fetchTasks())

// 2. 浏览器逻辑
const { showBrowser, browserInitialPath, openBrowser, handlePathSelect } = useBackupBrowser(editTask)

// 3. 事件封装
const handleRunTask = (row: any) => runTask(row, () => historyPanelRef.value?.fetchHistory())

const handleViewHistory = (row: any) => {
  historyTaskId.value = row.id
  historyTaskName.value = row.name
  showHistoryModal.value = true
}
</script>

<style scoped>
.page-header {
  margin-bottom: 8px;
}
</style>