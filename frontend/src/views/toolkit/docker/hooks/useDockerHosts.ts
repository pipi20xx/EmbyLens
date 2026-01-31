import { ref, computed, watch } from 'vue'
import { dockerApi, DockerHost } from '@/api/docker'

const STORAGE_KEY = 'lens_selected_docker_host'

export function useDockerHosts() {
  const hosts = ref<DockerHost[]>([])
  const selectedHostId = ref<string | null>(null)

  const hostOptions = computed(() => hosts.value.map(h => ({ label: h.name, value: h.id })))
  const currentHost = computed(() => hosts.value.find(h => h.id === selectedHostId.value))

  const fetchHosts = async () => {
    try {
      const res = await dockerApi.getHosts()
      hosts.value = Array.isArray(res.data) ? res.data : []
      
      if (hosts.value.length > 0) {
        const savedHostId = localStorage.getItem(STORAGE_KEY)
        if (savedHostId && hosts.value.some(h => h && h.id === savedHostId)) {
          selectedHostId.value = savedHostId
        } else if (!selectedHostId.value) {
          selectedHostId.value = hosts.value[0].id
        }
      }
    } catch (e) {
      hosts.value = []
    }
  }

  watch(selectedHostId, (val) => {
    if (val) localStorage.setItem(STORAGE_KEY, val)
  })

  return {
    hosts,
    selectedHostId,
    hostOptions,
    currentHost,
    fetchHosts
  }
}
