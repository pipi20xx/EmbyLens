import { ref, reactive, computed } from 'vue'
import { useMessage } from 'naive-ui'
import axios from 'axios'

export function useBangumi() {
  const message = useMessage()
  const loading = ref(false)
  const searchLoading = ref(false)
  const subjectResult = ref<any>(null)
  const charactersResult = ref<any>(null)
  const episodesResult = ref<any>(null)
  const searchResults = ref<any[]>([])

  const form = reactive({
    subject_id: ''
  })

  const searchForm = reactive({
    keywords: '',
    type: 2 // 默认动画
  })

  // --- 搜索逻辑 ---
  const handleSearch = async () => {
    if (!searchForm.keywords) return
    searchLoading.value = true
    try {
      const res = await axios.get('/api/bangumi_lab/search', { params: searchForm })
      searchResults.value = res.data.results || []
      if (searchResults.value.length === 0) message.warning('未找到相关条目')
    } catch (e) {
      message.error('搜索失败')
    } finally {
      searchLoading.value = false
    }
  }

  // --- 解析 Infobox ---
  const infoboxList = computed(() => {
    if (!subjectResult.value?.infobox) return []
    return subjectResult.value.infobox.map((item: any) => {
      let value = ''
      if (Array.isArray(item.value)) {
        value = item.value.map((v: any) => v.v || v).join(', ')
      } else {
        value = item.value
      }
      return { key: item.key, value }
    })
  })

  // --- 计算标题池 ---
  const titlePool = computed(() => {
    if (!subjectResult.value) return []
    const titles = new Set<string>()
    if (subjectResult.value.name) titles.add(subjectResult.value.name)
    if (subjectResult.value.name_cn) titles.add(subjectResult.value.name_cn)
    return Array.from(titles)
  })

  // --- 优化：去重后的系统标签 ---
  const uniqueMetaTags = computed(() => {
    const rawTags = subjectResult.value?.meta_tags || []
    return Array.from(new Set(rawTags.map((t: any) => {
      if (typeof t === 'string') return t.trim()
      return (t.name || t.label || '').trim()
    }))).filter(Boolean)
  })

  // --- 计算别名池 ---
  const aliasPool = computed(() => {
    if (!subjectResult.value?.infobox) return []
    const aliases = new Set<string>()
    const aliasItem = subjectResult.value.infobox.find((item: any) => 
      ['别名', 'Alias', '又名'].includes(item.key)
    )
    if (aliasItem) {
      if (Array.isArray(aliasItem.value)) {
        aliasItem.value.forEach((v: any) => {
          const val = typeof v === 'string' ? v : (v.v || v)
          if (val) aliases.add(val)
        })
      } else {
        aliases.add(aliasItem.value)
      }
    }
    return Array.from(aliases).sort()
  })

  const handleFetchAll = async () => {
    if (!form.subject_id) {
      message.warning('请输入 Subject ID')
      return
    }
    
    loading.value = true
    subjectResult.value = null
    charactersResult.value = null
    episodesResult.value = null

    try {
      const [subRes, charRes, epRes] = await Promise.all([
        axios.get(`/api/bangumi_lab/subject/${form.subject_id}`),
        axios.get(`/api/bangumi_lab/subject/${form.subject_id}/characters`),
        axios.get('/api/bangumi_lab/episodes', { params: { subject_id: form.subject_id, limit: 100 } })
      ])

      if (subRes.data.error) message.error(`条目抓取失败: ${subRes.data.error}`)
      else subjectResult.value = subRes.data

      if (charRes.data && !charRes.data.error) charactersResult.value = charRes.data
      if (epRes.data && !epRes.data.error) episodesResult.value = epRes.data

      if (subjectResult.value) message.success('抓取完成')
    } catch (e: any) {
      message.error('请求异常: ' + (e.response?.data?.detail || e.message))
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    searchLoading,
    form,
    searchForm,
    subjectResult,
    charactersResult,
    episodesResult,
    searchResults,
    infoboxList,
    uniqueMetaTags,
    titlePool,
    aliasPool,
    handleSearch,
    handleFetchAll
  }
}
