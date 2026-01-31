import request from '@/utils/request'

export const webhookApi = {
  getLogs: () => request.get('/api/webhook/list'),
  clearLogs: () => request.delete('/api/webhook/clear')
}