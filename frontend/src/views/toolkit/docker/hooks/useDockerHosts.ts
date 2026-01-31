import { ref, computed, watch } from 'vue'
import { dockerApi } from '@/api/docker'
import { DockerHost } from '@/types/docker'
import { STORAGE_KEYS } from '@/constants/storage'

export function useDockerHosts() {
  const hosts = ref<DockerHost[]>([])
  const selectedHostId = ref<string | null>(null)

  const hostOptions = computed(() => hosts.value.map(h => ({ label: h.name, value: h.id })))
  const currentHost = computed(() => hosts.value.find(h => h.id === selectedHostId.value))

  const fetchHosts = async () => {
    const data = await dockerApi.getHosts()
    hosts.value = Array.isArray(data) ? data : []
    
    if (hosts.value.length > 0) {
      const savedHostId = localStorage.getItem(STORAGE_KEYS.SELECTED_DOCKER_HOST)
      if (savedHostId && hosts.value.some(h => h && h.id === savedHostId)) {
        selectedHostId.value = savedHostId
      } else if (!selectedHostId.value) {
        selectedHostId.value = hosts.value[0].id
      }
    }
  }

  watch(selectedHostId, (val) => {
    if (val) localStorage.setItem(STORAGE_KEYS.SELECTED_DOCKER_HOST, val)
  })

  return {
    hosts,
    selectedHostId,
    hostOptions,
    currentHost,
    fetchHosts
  }
}