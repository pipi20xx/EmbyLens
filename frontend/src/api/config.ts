import axios from 'axios'

export const configApi = {
  getCurrent: () => axios.get('/api/server/current'),
  saveGlobal: (data: any) => axios.post('/api/server/save', data),
  exportConfig: () => axios.get('/api/system/config/export'),
  importConfig: (formData: FormData) => axios.post('/api/system/config/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const serverApi = {
  getServers: () => axios.get('/api/server'),
  activateServer: (id: string) => axios.post(`/api/server/activate/${id}`),
  deleteServer: (id: string) => axios.delete(`/api/server/${id}`),
  getLibraries: () => axios.get('/api/server/libraries'),
  getUsers: () => axios.get('/api/server/users'),
  syncUsers: () => axios.post('/api/server/users/sync')
}
