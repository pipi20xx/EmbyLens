import axios from 'axios'

export const notificationApi = {
  getSettings: () => axios.get('/api/notification/settings'),
  saveSettings: (data: any) => axios.post('/api/notification/settings', data),
  addBot: (data: any) => axios.post('/api/notification/bots', data),
  updateBot: (id: string, data: any) => axios.put(`/api/notification/bots/${id}`, data),
  deleteBot: (id: string) => axios.delete(`/api/notification/bots/${id}`),
  testBot: (data: { bot_id: string; message: string }) => axios.post('/api/notification/test', data)
}