import request from '@/utils/request'

export const notificationApi = {
  getSettings: () => request.get('/api/notification/settings'),
  saveSettings: (data: any) => request.post('/api/notification/settings', data),
  addBot: (data: any) => request.post('/api/notification/bots', data),
  updateBot: (id: string, data: any) => request.put(`/api/notification/bots/${id}`, data),
  deleteBot: (id: string) => request.delete(`/api/notification/bots/${id}`),
  testBot: (data: { bot_id: string; message: string }) => request.post('/api/notification/test', data)
}
