import axios from 'axios'

export const toolkitApi = {
  executeAction: (endpoint: string, data: any) => axios.post(`/api/toolkit/${endpoint}`, data)
}
