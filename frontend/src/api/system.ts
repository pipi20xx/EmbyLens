import request from '@/utils/request'

export const systemApi = {
  getConfig: () => request.get('/api/system/config'),
  saveConfig: (configs: any[]) => request.post('/api/system/config', { configs }),
  generateToken: () => request.post('/api/system/token/generate'),
  getAuditLogs: (params: any) => request.get('/api/system/audit/logs', { params })
}