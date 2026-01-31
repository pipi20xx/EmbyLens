import request from '@/utils/request'

export const actorsApi = {
  searchEmby: (query: string) => request.get('/api/actors/search-emby', { params: { query } }),
  searchTmdb: (query: string) => request.get('/api/actors/search-tmdb', { params: { query } }),
  updateName: (embyId: string, newName: string) => 
    request.post('/api/actors/update-actor-name', { emby_id: embyId, new_name: newName }),
  syncActor: (embyId: string, data: any) => 
    request.post('/api/actors/update-emby-actor', { emby_id: embyId, data })
}
