import request from '@/utils/request'

export const serverApi = {
  getLibraries: () => request.get('/api/server/libraries'),
  getUsers: () => request.get('/api/server/users'),
  syncUsers: () => request.post('/api/server/users/sync'),
  deleteServer: (id: string) => request.delete(`/api/server/${id}`),
  saveGlobal: (data: any) => request.post('/api/server/save', data),
  getCurrent: () => request.get('/api/server/current')
}
