import axios from 'axios'

export const actorsApi = {
  searchEmby: (query: string) => axios.get('/api/actors/search-emby', { params: { query } }),
  searchTmdb: (query: string) => axios.get('/api/actors/search-tmdb', { params: { query } }),
  updateName: (embyId: string, newName: string) => 
    axios.post('/api/actors/update-actor-name', { emby_id: embyId, new_name: newName }),
  syncActor: (embyId: string, data: any) => 
    axios.post('/api/actors/update-emby-actor', { emby_id: embyId, data })
}