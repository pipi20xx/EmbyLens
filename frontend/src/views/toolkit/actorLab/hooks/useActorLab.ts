import { ref, reactive } from 'vue'
import { useMessage } from 'naive-ui'
import { actorsApi } from '@/api/actors'
import { actorLabApi } from '@/api/actorLab'

export function useActorLab() {
  const message = useMessage()
  const activeTab = ref('search')

  // 搜索逻辑
  const searchQuery = ref('')
  const searchLoading = ref(false)
  const searchResults = ref<any[]>([])

  const handleSearch = async () => {
    if (!searchQuery.value) return
    searchLoading.value = true
    try {
      const res = await actorsApi.searchTmdb(searchQuery.value)
      searchResults.value = res.data.results || []
    } catch (e) {
      message.error('搜索异常')
    } finally {
      searchLoading.value = false
    }
  }

  // 分析逻辑
  const personId = ref('')
  const detailLanguage = ref('zh-CN')
  const analyzeLoading = ref(false)
  const result = ref<any>(null)

  const handleAnalyze = async () => {
    if (!personId.value) {
      message.warning('请输入 Person ID')
      return
    }
    analyzeLoading.value = true
    result.value = null
    
    const isAll = detailLanguage.value === 'all'
    const params = {
      person_id: personId.value,
      language: isAll ? '' : detailLanguage.value,
      include_translations: isAll
    }

    try {
      const res = await actorLabApi.analyze(params)
      result.value = res.data
      message.success('深度分析完成')
    } catch (e) {
      message.error('分析失败')
    } finally {
      analyzeLoading.value = false
    }
  }

  const fillId = (person: any) => {
    personId.value = person.id.toString()
    activeTab.value = 'direct'
    handleAnalyze()
  }

  const jsonModal = reactive({ show: false, data: {} })
  const showJson = (data: any) => { jsonModal.data = data; jsonModal.show = true; }

  return {
    activeTab, searchQuery, searchLoading, searchResults, personId, detailLanguage, analyzeLoading, result, jsonModal,
    handleSearch, handleAnalyze, fillId, showJson
  }
}
