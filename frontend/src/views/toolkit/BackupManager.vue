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
import axios from 'axios'

// 导入乐高组件
import TaskPanel from './backup/components/TaskPanel.vue'
import HistoryPanel from './backup/components/HistoryPanel.vue'
import TaskEditModal from './backup/components/TaskEditModal.vue'
import PathBrowserModal from './backup/components/PathBrowserModal.vue'
import HistoryModal from './backup/components/HistoryModal.vue'

const message = useMessage()

const taskPanelRef = ref()
const historyPanelRef = ref()

const showEditModal = ref(false)
const showBrowser = ref(false)
const showHistoryModal = ref(false)
const historyTaskId = ref('')
const historyTaskName = ref('')
const browserInitialPath = ref('/')
const browserTargetField = ref('')

const editTask = ref({
  id: '',
  name: '',
  mode: '7z',
  storage_type: 'ssd',
  sync_strategy: 'mirror',
  compression_level: 1,
  src_path: '',
  dst_path: '',
  password: '',
  enabled: true,
  schedule_type: 'cron',
  schedule_value: '0 3 * * *',
  ignore_patterns: [],
  host_id: 'local'
})

const handleAddTask = () => {
  editTask.value = {
    id: '',
    name: '',
    mode: '7z',
    storage_type: 'ssd',
    sync_strategy: 'mirror',
    compression_level: 1,
    src_path: '',
    dst_path: '',
    password: '',
    enabled: true,
    schedule_type: 'cron',
    schedule_value: '0 3 * * *',
    ignore_patterns: [],
    host_id: 'local'
  }
  showEditModal.value = true
}

const handleEditTask = (row: any) => {
  editTask.value = { ...row }
  showEditModal.value = true
}

const saveTask = async () => {
  try {
    if (editTask.value.id) {
      await axios.put(`/api/backup/tasks/${editTask.value.id}`, editTask.value)
    } else {
      await axios.post('/api/backup/tasks', editTask.value)
    }
    message.success('保存成功')
    showEditModal.value = false
    taskPanelRef.value?.fetchTasks()
  } catch (e) {
    message.error('保存失败')
  }
}

const handleRunTask = async (row: any) => {
  await axios.post(`/api/backup/tasks/${row.id}/run`)
  message.info('备份任务已启动')
  setTimeout(() => historyPanelRef.value?.fetchHistory(), 1000)
}

const handleViewHistory = (row: any) => {
  historyTaskId.value = row.id
  historyTaskName.value = row.name
  showHistoryModal.value = true
}

const openBrowser = (field: string) => {
  browserTargetField.value = field
  browserInitialPath.value = (editTask.value as any)[field === 'src' ? 'src_path' : 'dst_path'] || '/'
  showBrowser.value = true
}

const handlePathSelect = (path: string) => {
  if (browserTargetField.value === 'src') {
    editTask.value.src_path = path
  } else {
    editTask.value.dst_path = path
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 8px;
}
</style>