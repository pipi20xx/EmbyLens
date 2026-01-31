import axios from 'axios'

export const webhookApi = {
  getLogs: () => axios.get('/api/webhook/list'),
  clearLogs: () => axios.delete('/api/webhook/clear')
}
