import { ref, reactive } from 'vue'
import { useMessage } from 'naive-ui'
import { tmdbApi } from '@/api/tmdb'

export function useTmdbSearch() {
  const message = useMessage()
  const searchLoading = ref(false)
  const searchResults = ref<any[]>([])
  
  const searchForm = reactive({
    query: '',
    media_type: 'movie',
    language: 'zh-CN'
  })

  const handleSearch = async () => {
    if (!searchForm.query) return
    searchLoading.value = true
    try {
      const data = await tmdbApi.search(searchForm)
      searchResults.value = (data as any).results || []
      if (searchResults.value.length === 0) message.warning('未找到相关结果')
    } finally {
      searchLoading.value = false
    }
  }

  return {
    searchLoading, searchResults, searchForm, handleSearch
  }
}