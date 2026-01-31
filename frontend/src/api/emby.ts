import axios from 'axios'

export const embyApi = {
  getItemInfo: (itemId: string) => axios.get('/api/items/info', { params: { item_id: itemId } })
}
