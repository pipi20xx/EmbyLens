import axios from 'axios'

export const actorLabApi = {
  analyze: (params: any) => axios.get('/api/actor-lab/analyze', { params })
}
