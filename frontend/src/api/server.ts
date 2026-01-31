import axios from 'axios'

export const serverApi = {
  getLibraries: () => axios.get('/api/server/libraries'),
  getUsers: () => axios.get('/api/server/users'),
  syncUsers: () => axios.post('/api/server/users/sync'),
  deleteServer: (id: string) => axios.delete(`/api/server/${id}`),
  saveGlobal: (data: any) => axios.post('/api/server/save', data),
  getCurrent: () => axios.get('/api/server/current')
}