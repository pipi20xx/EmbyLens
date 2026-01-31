import { ref, computed, watch } from 'vue'
import { dockerApi } from '@/api/docker'
import { DockerHost } from '@/types/docker'

const STORAGE_KEY = 'lens_selected_docker_host'

export function useDockerHosts() {
  const hosts = ref<DockerHost[]>([])
  const selectedHostId = ref<string | null>(null)

  const hostOptions = computed(() => hosts.value.map(h => ({ label: h.name, value: h.id })))
  const currentHost = computed(() => hosts.value.find(h => h.id === selectedHostId.value))

  const fetchHosts = async () => {
    // 拦截器会自动处理错误弹窗，这里只需要关注业务
    const data = await dockerApi.getHosts()
    hosts.value = Array.isArray(data) ? data : []
    
    if (hosts.value.length > 0) {
      const savedHostId = localStorage.getItem(STORAGE_KEY)
      if (savedHostId && hosts.value.some(h => h && h.id === savedHostId)) {
        selectedHostId.value = savedHostId
      } else if (!selectedHostId.value) {
        selectedHostId.value = hosts.value[0].id
      }
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