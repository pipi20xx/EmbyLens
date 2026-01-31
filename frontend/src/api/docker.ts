import axios from 'axios'

export interface DockerHost {
  id: string
  name: string
  host: string
  port: number
  compose_scan_paths?: string
  [key: string]: any
}

export interface AutoUpdateSettings {
  enabled: boolean
  type: 'cron' | 'interval'
  value: string
}

export const dockerApi = {
  // Hosts
  getHosts: () => axios.get<DockerHost[]>('/api/docker/hosts'),
  updateHost: (id: string, data: DockerHost) => axios.put(`/api/docker/hosts/${id}`, data),
  
  // Settings
  getAutoUpdateSettings: () => axios.get<AutoUpdateSettings>('/api/docker/auto-update/settings'),
  saveAutoUpdateSettings: (data: AutoUpdateSettings) => axios.post('/api/docker/auto-update/settings', data),
  
  // Containers & Compose
  getContainers: (hostId: string, details = true) => 
    axios.get(`/api/docker/${hostId}/containers`, { params: { details } }),
  getStats: (hostId: string) => axios.get(`/api/docker/${hostId}/containers/stats`),
  getProjects: (hostId: string) => axios.get(`/api/docker/compose/${hostId}/projects`)
}
