import { ref } from 'vue'
import { actorsApi } from '@/api/actors'

export function useActorSearch() {
  const embyMode = ref('name')
  const embyQuery = ref('')
  const embyLoading = ref(false)
  const embyResults = ref<any[]>([])
  
  const tmdbMode = ref('name')
  const tmdbQuery = ref('')
  const tmdbLoading = ref(false)
  const tmdbResults = ref<any[]>([])

  const handleEmbySearch = async () => {
    if (!embyQuery.value) return
    embyLoading.value = true
    try {
      const data = await actorsApi.searchEmby(embyQuery.value)
      embyResults.value = (data as any).results
    } finally { 
      embyLoading.value = false 
    }
  }

  const handleTmdbSearch = async () => {
    if (!tmdbQuery.value) return
    tmdbLoading.value = true
    try {
      const data = await actorsApi.searchTmdb(tmdbQuery.value)
      tmdbResults.value = (data as any).results
    } finally { 
      tmdbLoading.value = false 
    }
  }

  return {
    embyMode, embyQuery, embyLoading, embyResults,
    tmdbMode, tmdbQuery, tmdbLoading, tmdbResults,
    handleEmbySearch, handleTmdbSearch
  }
}