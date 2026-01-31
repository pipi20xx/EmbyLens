import axios from 'axios'

export const pgsqlApi = {
  getHosts: () => axios.get('/api/pgsql/hosts'),
  // Add other pgsql endpoints if needed
}
