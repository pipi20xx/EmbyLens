import request from '@/utils/request'

export const imageBuilderApi = {
  getProjects: () => request.get<any[]>('/api/image-builder/projects'),
  addProject: (data: any) => request.post('/api/image-builder/projects', data),
  updateProject: (id: string, data: any) => request.put(`/api/image-builder/projects/${id}`, data),
  deleteProject: (id: string) => request.delete(`/api/image-builder/projects/${id}`),
  getRegistries: () => request.get<any[]>('/api/image-builder/registries'),
  getProxies: () => request.get<any[]>('/api/image-builder/proxies'),
  buildProject: (id: string, data: { tag: string }) => request.post(`/api/image-builder/projects/${id}/build`, data),
  clearAllTasks: () => request.delete('/api/image-builder/tasks')
}
