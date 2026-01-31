import { reactive } from 'vue'
import { useMessage } from 'naive-ui'
import { tmdbApi } from '@/api/tmdb'

export function useTmdbJson(detailResult: any, detailForm: any) {
  const message = useMessage()
  const jsonModal = reactive({
    show: false,
    title: '原始 JSON 数据',
    loading: false,
    data: {} as any
  })

  const fetchFullSeason = async (season: any) => {
    jsonModal.loading = true
    jsonModal.title = `深度探针: ${season.name}`
    jsonModal.show = true
    jsonModal.data = { message: '正在从 TMDB 实时抓取该季全量数据...' }
    try {
      const isAll = detailForm.language === 'all'
      const res = await tmdbApi.fetchSeason({
        tmdb_id: detailResult.value.id,
        season_number: season.season_number,
        language: isAll ? '' : detailForm.language,
        include_translations: isAll
      })
      jsonModal.data = res.data
      jsonModal.title = `季全量详情 - ${res.data.name}`
    } catch (e) {
      message.error('季详情抓取失败')
      jsonModal.data = season
    } finally {
      jsonModal.loading = false
    }
  }

  const fetchFullEpisode = async (ep: any) => {
    jsonModal.loading = true
    jsonModal.title = `深度抓取单集: EP ${ep.episode_number}`
    jsonModal.show = true
    jsonModal.data = { message: '正在从 TMDB 实时获取单集全量数据...' }
    try {
      const isAll = detailForm.language === 'all'
      const res = await tmdbApi.fetchEpisode({
        tmdb_id: detailResult.value.id,
        season_number: ep.season_number,
        episode_number: ep.episode_number,
        language: isAll ? '' : detailForm.language,
        include_translations: isAll
      })
      jsonModal.data = res.data
      jsonModal.title = `单集全量 JSON - EP ${ep.episode_number}: ${res.data.name}`
    } catch (e) {
      message.error('单集详情抓取失败')
      jsonModal.data = ep
    } finally {
      jsonModal.loading = false
    }
  }

  const showJson = (data: any, type: 'main' | 'season' | 'episode' = 'main', isDeep: boolean = false) => {
    if (isDeep) {
      if (type === 'episode') fetchFullEpisode(data)
      else if (type === 'season') fetchFullSeason(data)
    } else {
      jsonModal.data = data
      jsonModal.title = `元数据快照 - ${data.name || data.title || '详情'}`
      jsonModal.show = true
      jsonModal.loading = false
    }
  }

  return {
    jsonModal, showJson
  }
}
