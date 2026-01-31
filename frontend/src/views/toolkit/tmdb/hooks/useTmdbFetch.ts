import { ref, reactive, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { tmdbApi } from '@/api/tmdb'

export function useTmdbFetch() {
  const message = useMessage()
  const detailLoading = ref(false)
  const detailResult = ref<any>(null)

  const detailForm = reactive({
    tmdb_id: '',
    media_type: 'movie',
    language: 'zh-CN',
    recursive: false
  })

  const titlePool = computed(() => {
    if (!detailResult.value || !detailResult.value.translations) return []
    const titles = new Set<string>()
    if (detailResult.value.title) titles.add(detailResult.value.title)
    if (detailResult.value.name) titles.add(detailResult.value.name)
    if (detailResult.value.original_title) titles.add(detailResult.value.original_title)
    if (detailResult.value.original_name) titles.add(detailResult.value.original_name)
    const trans = detailResult.value.translations.translations || []
    trans.forEach((t: any) => {
      if (t.data?.title) titles.add(t.data.title)
      if (t.data?.name) titles.add(t.data.name)
    })
    return Array.from(titles).sort()
  })

  const aliasPool = computed(() => {
    if (!detailResult.value) return []
    const aliases = new Set<string>()
    const aData = detailResult.value.alternative_titles
    const list = aData?.titles || aData?.results || []
    list.forEach((item: any) => {
      if (item.title) aliases.add(item.title)
    })
    return Array.from(aliases).sort()
  })

  const keywordsList = computed(() => {
    if (!detailResult.value) return []
    const kData = detailResult.value.keywords
    return kData?.keywords || kData?.results || []
  })

  const handleFetchDetail = async () => {
    if (!detailForm.tmdb_id) {
      message.warning('请输入 TMDB ID')
      return
    }
    detailLoading.value = true
    detailResult.value = null
    const isAll = detailForm.language === 'all'
    const params = {
      tmdb_id: detailForm.tmdb_id,
      media_type: detailForm.media_type,
      language: isAll ? '' : detailForm.language,
      include_translations: isAll,
      recursive: detailForm.recursive
    }
    try {
      const res = await tmdbApi.fetch(params)
      if (res.data.error) {
        message.error(res.data.error)
      } else {
        detailResult.value = res.data
        message.success('抓取成功')
      }
    } catch (e) {
      message.error('抓取失败')
    } finally {
      detailLoading.value = false
    }
  }

  return {
    detailLoading, detailResult, detailForm, titlePool, aliasPool, keywordsList, handleFetchDetail
  }
}
