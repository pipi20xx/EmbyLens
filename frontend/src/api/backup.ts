import request from '@/utils/request'

export interface BackupTask {
  id?: string
  name: string
  mode: string
  storage_type: string
  sync_strategy: string
  compression_level: number
  src_path: string
  dst_path: string
  password?: string
  enabled: boolean
  schedule_type: string
  schedule_value: string
  ignore_patterns: string[]
  host_id: string
}

export const backupApi = {
  getTasks: () => request.get<BackupTask[]>('/api/backup/tasks'),
  saveTask: (task: BackupTask) => {
    if (task.id) {
      return request.put(`/api/backup/tasks/${task.id}`, task)
    } else {
      return request.post('/api/backup/tasks', task)
    }
  },
  runTask: (id: string) => request.post(`/api/backup/tasks/${id}/run`),
  getHistory: (taskId?: string) => request.get('/api/backup/history', { params: { task_id: taskId } })
}