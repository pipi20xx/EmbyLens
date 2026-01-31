import axios from 'axios'

export const imageBuilderApi = {
  getProjects: () => axios.get('/api/image-builder/projects'),
  addProject: (data: any) => axios.post('/api/image-builder/projects', data),
  updateProject: (id: string, data: any) => axios.put(`/api/image-builder/projects/${id}`, data),
  deleteProject: (id: string) => axios.delete(`/api/image-builder/projects/${id}`),
  getRegistries: () => axios.get('/api/image-builder/registries'),
  getProxies: () => axios.get('/api/image-builder/proxies'),
  buildProject: (id: string, data: { tag: string }) => axios.post(`/api/image-builder/projects/${id}/build`, data),
  clearAllTasks: () => axios.delete('/api/image-builder/tasks')
}
