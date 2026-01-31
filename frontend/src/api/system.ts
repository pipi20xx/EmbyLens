import axios from 'axios'

export const systemApi = {
  getConfig: () => axios.get('/api/system/config'),
  saveConfig: (configs: any[]) => axios.post('/api/system/config', { configs }),
  generateToken: () => axios.post('/api/system/token/generate'),
  getAuditLogs: (params: any) => axios.get('/api/system/audit/logs', { params })
}
