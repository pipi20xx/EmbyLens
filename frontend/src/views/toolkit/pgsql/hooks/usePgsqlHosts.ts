import { ref, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { pgsqlApi } from '@/api/pgsql'
import { STORAGE_KEYS } from '@/constants/storage'

export function usePgsqlHosts() {
  const message = useMessage()
  const hosts = ref<any[]>([])
  const selectedHostId = ref<string | null>(null)

  const hostOptions = computed(() => hosts.value.map(h => ({ label: h.name, value: h.id })))
  const selectedHost = computed(() => hosts.value.find(h => h.id === selectedHostId.value))

  const fetchHosts = async () => {
    try {
      const res = await pgsqlApi.getHosts()
      hosts.value = res.data
      
      if (hosts.value.length > 0) {
        const savedHostId = localStorage.getItem(STORAGE_KEYS.SELECTED_PGSQL_HOST)
        if (savedHostId && hosts.value.some(h => h && h.id === savedHostId)) {
          selectedHostId.value = savedHostId
        } else if (!selectedHostId.value) {
          selectedHostId.value = hosts.value[0].id
        }
      }
    } catch (e) {
      message.error('加载主机列表失败')
    }
  }

  watch(selectedHostId, (val) => {
    if (val) localStorage.setItem(STORAGE_KEYS.SELECTED_PGSQL_HOST, val)
  })

  return {
    hosts, selectedHostId, hostOptions, selectedHost, fetchHosts
  }
}
