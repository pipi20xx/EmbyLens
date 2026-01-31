import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { actorsApi } from '@/api/actors'

export function useActorSearch() {
  const message = useMessage()
  
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
      const res = await actorsApi.searchEmby(embyQuery.value)
      embyResults.value = res.data.results
    } catch (e) { 
      message.error('Emby 检索失败') 
    } finally { 
      embyLoading.value = false 
    }
  }

  const handleTmdbSearch = async () => {
    if (!tmdbQuery.value) return
    tmdbLoading.value = true
    try {
      const res = await actorsApi.searchTmdb(tmdbQuery.value)
      tmdbResults.value = res.data.results
    } catch (e) { 
      message.error('TMDB 检索失败') 
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
