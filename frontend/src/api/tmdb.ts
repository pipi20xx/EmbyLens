import axios from 'axios'

export const tmdbApi = {
  search: (params: any) => axios.get('/api/tmdb-lab/search', { params }),
  fetch: (params: any) => axios.get('/api/tmdb-lab/fetch', { params }),
  fetchSeason: (params: any) => axios.get('/api/tmdb-lab/fetch-season', { params }),
  fetchEpisode: (params: any) => axios.get('/api/tmdb-lab/fetch-episode', { params })
}
