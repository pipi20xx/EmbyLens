import axios from 'axios'

export const authApi = {
  getMe: () => axios.get('/api/auth/me'),
  getStatus: () => axios.get('/api/auth/status'),
  setup2fa: () => axios.get('/api/auth/2fa/setup'),
  enable2fa: (code: string) => axios.post(`/api/auth/2fa/enable?code=${code}`),
  disable2fa: () => axios.post('/api/auth/2fa/disable'),
  updateSystemConfig: (configs: any[]) => axios.post('/api/system/config', { configs }),
  changePassword: (data: any) => axios.post('/api/auth/change-password', data) // 假设存在
}
