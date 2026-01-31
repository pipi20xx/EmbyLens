import request from '@/utils/request'
import { DockerHost, AutoUpdateSettings } from '@/types/docker'

export const dockerApi = {
  // Hosts
  getHosts: () => request.get<DockerHost[]>('/api/docker/hosts'),
  updateHost: (id: string, data: DockerHost) => request.put(`/api/docker/hosts/${id}`, data),
  
  // Settings
  getAutoUpdateSettings: () => request.get<AutoUpdateSettings>('/api/docker/auto-update/settings'),
  saveAutoUpdateSettings: (data: AutoUpdateSettings) => request.post('/api/docker/auto-update/settings', data),
  
  // Containers & Compose
  getContainers: (hostId: string, details = true) => 
    request.get(`/api/docker/${hostId}/containers`, { params: { details } }),
  getStats: (hostId: string) => request.get(`/api/docker/${hostId}/containers/stats`),
  getProjects: (hostId: string) => request.get(`/api/docker/compose/${hostId}/projects`)
}