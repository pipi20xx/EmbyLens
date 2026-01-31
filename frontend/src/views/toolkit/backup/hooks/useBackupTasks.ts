import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { backupApi, BackupTask } from '@/api/backup'

export function useBackupTasks(onRefresh?: () => void) {
  const message = useMessage()
  const showEditModal = ref(false)
  const editTask = ref<BackupTask>({
    name: '',
    mode: '7z',
    storage_type: 'ssd',
    sync_strategy: 'mirror',
    compression_level: 1,
    src_path: '',
    dst_path: '',
    enabled: true,
    schedule_type: 'cron',
    schedule_value: '0 3 * * *',
    ignore_patterns: [],
    host_id: 'local'
  })

  const resetEditTask = () => {
    editTask.value = {
      name: '',
      mode: '7z',
      storage_type: 'ssd',
      sync_strategy: 'mirror',
      compression_level: 1,
      src_path: '',
      dst_path: '',
      enabled: true,
      schedule_type: 'cron',
      schedule_value: '0 3 * * *',
      ignore_patterns: [],
      host_id: 'local'
    }
  }

  const handleAddTask = () => {
    resetEditTask()
    showEditModal.value = true
  }

  const handleEditTask = (row: BackupTask) => {
    editTask.value = { ...row }
    showEditModal.value = true
  }

  const saveTask = async () => {
    try {
      await backupApi.saveTask(editTask.value)
      message.success('保存成功')
      showEditModal.value = false
      if (onRefresh) onRefresh()
    } catch (e) {
      message.error('保存失败')
    }
  }

  const handleRunTask = async (row: BackupTask, onHistoryRefresh?: () => void) => {
    if (!row.id) return
    await backupApi.runTask(row.id)
    message.info('备份任务已启动')
    if (onHistoryRefresh) {
      setTimeout(onHistoryRefresh, 1000)
    }
  }

  return {
    showEditModal, editTask, handleAddTask, handleEditTask, saveTask, handleRunTask
  }
}
