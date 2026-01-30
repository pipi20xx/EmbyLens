import { defineStore } from 'pinia'
import axios from 'axios'

interface DockerState {
  containers: Record<string, any[]>
  containerStats: Record<string, Record<string, any>> // { hostId: { containerName: stats } }
  projects: Record<string, any[]>
  loading: Record<string, boolean>
  lastFetched: Record<string, number>
}

export const useDockerStore = defineStore('docker', {
  state: (): DockerState => ({
    containers: {},
    containerStats: {},
    projects: {},
    loading: {},
    lastFetched: {}
  }),
  
  actions: {
    async fetchContainers(hostId: string, force = false, details = true) {
      if (!hostId) return
      
      const now = Date.now()
      const cacheKey = `containers_${hostId}_${details}`
      
      if (!force && this.containers[hostId] && now - (this.lastFetched[cacheKey] || 0) < 10000) {
        return
      }

      this.loading[cacheKey] = true
      try {
        const res = await axios.get(`/api/docker/${hostId}/containers`, { params: { details } })
        this.containers = { ...this.containers, [hostId]: Array.isArray(res.data) ? res.data : [] }
        this.lastFetched[cacheKey] = now
        
        // 获取容器列表后，如果开启了增强模式，尝试获取一次 Stats
        if (details) {
          this.fetchStats(hostId)
        }
      } catch (error) {
        console.error('Failed to fetch containers', error)
        if (!this.containers[hostId]) {
          this.containers = { ...this.containers, [hostId]: [] }
        }
      } finally {
        this.loading[cacheKey] = false
      }
    },

    async fetchStats(hostId: string) {
      if (!hostId) return
      try {
        const res = await axios.get(`/api/docker/${hostId}/containers/stats`)
        this.containerStats = { ...this.containerStats, [hostId]: res.data }
      } catch (error) {
        console.error('Failed to fetch stats', error)
      }
    },

    async fetchProjects(hostId: string, force = false) {
      if (!hostId) return
      
      const now = Date.now()
      const cacheKey = `projects_${hostId}`
      
      if (!force && this.projects[hostId] && now - (this.lastFetched[cacheKey] || 0) < 10000) {
        return
      }

      this.loading[cacheKey] = true
      try {
        const res = await axios.get(`/api/docker/compose/${hostId}/projects`)
        this.projects = { ...this.projects, [hostId]: Array.isArray(res.data) ? res.data : [] }
        this.lastFetched[cacheKey] = now
      } catch (error) {
        console.error('Failed to fetch projects', error)
        if (!this.projects[hostId]) {
          this.projects = { ...this.projects, [hostId]: [] }
        }
      } finally {
        this.loading[cacheKey] = false
      }
    },

    // 静默刷新数据（强制从服务器获取并更新缓存）
    async refreshSilently(hostId: string) {
      if (!hostId) return
      await Promise.all([
        this.fetchContainers(hostId, true),
        this.fetchProjects(hostId, true)
      ])
    }
  }
})