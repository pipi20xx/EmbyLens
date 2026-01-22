import { ref } from 'vue'
import axios from 'axios'

export interface EmbyServer {
  id: string
  name: string
  url: string
  api_key: string
  user_id?: string
  username?: string
  password?: string
  session_token?: string
}

export const servers = ref<EmbyServer[]>([])
export const activeServerId = ref('')

export const fetchServers = async () => {
  try {
    const res = await axios.get('/api/server/list')
    servers.value = res.data.servers
    activeServerId.value = res.data.active_id
  } catch (e) {
    console.error('Failed to fetch servers:', e)
  }
}

export const activateServer = async (serverId: string) => {
  try {
    await axios.post(`/api/server/activate/${serverId}`)
    activeServerId.value = serverId
    return true
  } catch (e) {
    console.error('Failed to activate server:', e)
    return false
  }
}

export const activeServer = () => {
  return servers.value.find(s => s.id === activeServerId.value) || servers.value[0]
}
