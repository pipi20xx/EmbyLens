import axios from 'axios'

export const accountApi = {
  getUsers: () => axios.get('/api/server/users'),
  syncUsers: () => axios.post('/api/server/users/sync'),
  updateUser: (id: string, data: any) => axios.put(`/api/server/users/${id}`, data),
  deleteUser: (id: string) => axios.delete(`/api/server/users/${id}`)
}
