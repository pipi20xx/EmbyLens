import request from '@/utils/request'

export const tmdbApi = {
  search: (params: any) => request.get('/api/tmdb-lab/search', { params }),
  fetch: (params: any) => request.get('/api/tmdb-lab/fetch', { params }),
  fetchSeason: (params: any) => request.get('/api/tmdb-lab/fetch-season', { params }),
  fetchEpisode: (params: any) => request.get('/api/tmdb-lab/fetch-episode', { params })
}