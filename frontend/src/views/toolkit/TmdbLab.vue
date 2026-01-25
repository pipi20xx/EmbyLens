<template>
  <div class="toolkit-container">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">TMDB 实验室</n-text></n-h2>
        <n-text depth="3">直接从 TMDB 官方抓取元数据。支持递归抓取季、集信息，并提供结构化预览与原始数据导出。</n-text>
      </div>

      <n-grid :cols="24" :x-gap="12" :y-gap="12" item-responsive>
        <!-- 输入面板 -->
        <n-gi :span="24" :lspan="8">
          <n-space vertical size="large">
            <n-card title="1. 检索/定位" size="small">
              <n-tabs v-model:value="activeTab" type="line" animated>
                <n-tab-pane name="search" tab="关键词搜索">
                  <n-form label-placement="top">
                    <n-form-item label="名称">
                      <n-input v-model:value="searchForm.query" placeholder="电影或剧集名称..." @keyup.enter="handleSearch" />
                    </n-form-item>
                    <n-grid :cols="2" :x-gap="12">
                      <n-form-item-gi label="类型">
                        <n-select v-model:value="searchForm.media_type" :options="mediaTypeOptions" />
                      </n-form-item-gi>
                      <n-form-item-gi label="语言">
                        <n-select v-model:value="searchForm.language" :options="languageOptions" filterable tag />
                      </n-form-item-gi>
                    </n-grid>
                    <n-button block type="primary" secondary :loading="searchLoading" @click="handleSearch">搜索</n-button>
                  </n-form>
                  <div v-if="searchResults.length > 0" class="search-results-list">
                    <n-divider title-placement="left">搜索结果</n-divider>
                    <n-list hoverable clickable size="small">
                      <n-list-item v-for="item in searchResults" :key="item.id" @click="fillDetail(item)">
                        <n-thing :title="item.title || item.name" :description="`ID: ${item.id} | ${item.release_date || item.first_air_date || '未知'}`" />
                      </n-list-item>
                    </n-list>
                  </div>
                </n-tab-pane>
                <n-tab-pane name="direct" tab="直接 ID 抓取">
                  <n-form label-placement="top">
                    <n-form-item label="TMDB ID">
                      <n-input v-model:value="detailForm.tmdb_id" placeholder="输入 ID" />
                    </n-form-item>
                    <n-grid :cols="2" :x-gap="12">
                      <n-form-item-gi label="类型">
                        <n-select v-model:value="detailForm.media_type" :options="mediaTypeOptions" />
                      </n-form-item-gi>
                      <n-form-item-gi label="抓取语言 / 模式">
                        <n-select v-model:value="detailForm.language" :options="languageOptions" filterable tag />
                      </n-form-item-gi>
                    </n-grid>
                    <n-form-item v-if="detailForm.media_type === 'tv'" label="深度递归抓取">
                      <n-space align="center">
                        <n-switch v-model:value="detailForm.recursive" />
                        <n-text depth="3">递归获取所有季和集详情</n-text>
                      </n-space>
                    </n-form-item>
                    <n-button block type="primary" :loading="detailLoading" @click="handleFetchDetail">启动抓取</n-button>
                  </n-form>
                </n-tab-pane>
              </n-tabs>
            </n-card>
          </n-space>
        </n-gi>

        <!-- 结果展示区 -->
        <n-gi :span="24" :lspan="16">
          <div v-if="detailResult" class="results-area">
            <n-card size="small">
              <template #header>
                <n-space align="center">
                  <n-text strong style="font-size: 18px">{{ detailResult.name || detailResult.title }}</n-text>
                  <n-tag size="small" type="primary" round>{{ detailResult.release_date || detailResult.first_air_date }}</n-tag>
                  <n-tag size="small" :type="detailForm.media_type === 'tv' ? 'info' : 'success'">{{ detailForm.media_type.toUpperCase() }}</n-tag>
                </n-space>
              </template>
              <template #header-extra>
                <n-button secondary circle size="small" type="primary" @click="showJson(detailResult, 'main')" title="查看本体 JSON">
                  <template #icon><n-icon><CodeIcon /></n-icon></template>
                </n-button>
              </template>

              <!-- 基本信息 -->
              <n-descriptions label-placement="left" :column="2" size="small" bordered label-style="width: 100px">
                <n-descriptions-item label="原始标题">{{ detailResult.original_name || detailResult.original_title }}</n-descriptions-item>
                <n-descriptions-item label="状态">{{ detailResult.status }}</n-descriptions-item>
                <n-descriptions-item label="评分">{{ detailResult.vote_average }} ({{ detailResult.vote_count }} 票)</n-descriptions-item>
                <n-descriptions-item label="TMDB ID">{{ detailResult.id }}</n-descriptions-item>
                <n-descriptions-item label="流派" :span="2">
                  <n-space><n-tag v-for="g in detailResult.genres" :key="g.id" size="tiny" quaternary>{{ g.name }}</n-tag></n-space>
                </n-descriptions-item>
              </n-descriptions>

              <div class="overview-box" style="margin-top: 12px">
                <n-p depth="3">{{ detailResult.overview || '暂无简介' }}</n-p>
              </div>

              <!-- 详细名称对照表 -->
              <div class="lab-report-card">
                <div class="report-header">
                  <n-icon color="#bb86fc" size="18" style="margin-right: 8px"><TitleIcon /></n-icon>
                  <span class="report-title">详细名称对照表 (分拣参考)</span>
                </div>

                <!-- 1. 流派 -->
                <div class="report-row">
                  <div class="row-label"><n-icon size="14"><GenreIcon /></n-icon> 1. 所有流派</div>
                  <div class="row-content">
                    <span v-for="g in detailResult.genres" :key="g.id" class="data-tag">
                      {{ g.name }} ({{ g.id }})
                    </span>
                    <n-text v-if="!detailResult.genres?.length" depth="3">N/A</n-text>
                  </div>
                </div>

                <!-- 2. 制作公司 -->
                <div class="report-row">
                  <div class="row-label"><n-icon size="14"><CompanyIcon /></n-icon> 2. 制作公司</div>
                  <div class="row-content">
                    <span v-for="c in detailResult.production_companies" :key="c.id" class="data-tag">
                      {{ c.name }} ({{ c.id }})
                    </span>
                    <n-text v-if="!detailResult.production_companies?.length" depth="3">N/A</n-text>
                  </div>
                </div>

                <!-- 3. 关键词 -->
                <div class="report-row">
                  <div class="row-label"><n-icon size="14"><TagIcon /></n-icon> 3. 关键标签 (Keywords)</div>
                  <div class="row-content">
                    <span v-for="k in keywordsList" :key="k.id" class="data-tag">
                      {{ k.name }} ({{ k.id }})
                    </span>
                    <n-text v-if="!keywordsList.length" depth="3">N/A</n-text>
                  </div>
                </div>

                <!-- 4. 标题池 -->
                <div class="report-row">
                  <div class="row-label"><n-icon size="14"><TitleIcon /></n-icon> 4. 全量标题池 ({{ titlePool.length }})</div>
                  <div class="row-content" style="margin-top: 6px">
                    <div v-if="titlePool.length > 0">
                      <span v-for="t in titlePool" :key="t" class="data-tag">{{ t }}</span>
                    </div>
                    <div v-else class="pool-box" style="color: rgba(255,255,255,0.3)">
                      <n-text v-if="detailForm.language === 'all'" depth="3">暂无翻译标题</n-text>
                      <n-text v-else depth="3">未获取全量标题。请在左侧选择“全语言抓取”模式。</n-text>
                    </div>
                  </div>
                </div>

                <!-- 5. 别名池 -->
                <div class="report-row">
                  <div class="row-label" style="color: #f0a020"><n-icon size="14"><AliasIcon /></n-icon> 5. 全量别名池 ({{ aliasPool.length }})</div>
                  <div class="row-content" style="margin-top: 6px">
                    <div v-if="aliasPool.length > 0">
                      <span v-for="a in aliasPool" :key="a" class="data-tag tag-orange">{{ a }}</span>
                    </div>
                    <div v-else class="pool-box" style="color: rgba(255,255,255,0.2)">
                      暂无别名信息
                    </div>
                  </div>
                </div>
              </div>

              <!-- 递归季和集信息 -->
              <div v-if="detailResult.full_seasons_data" style="margin-top: 24px">
                <n-divider title-placement="left"><n-text type="primary" strong>季与集 递归详情</n-text></n-divider>
                <n-collapse>
                  <n-collapse-item v-for="season in detailResult.full_seasons_data" :key="season.id" :name="season.id">
                    <template #header>
                      <n-space justify="space-between" style="width: 100%" align="center">
                        <n-text strong>{{ season.name }} ({{ season.episodes?.length || 0 }} 集)</n-text>
                        <n-space>
                          <n-button secondary circle size="tiny" type="default" @click.stop="showJson(season, 'season', false)" title="查看当前快照">
                            <template #icon><n-icon><SnippetIcon /></n-icon></template>
                          </n-button>
                          <n-button secondary circle size="tiny" type="info" @click.stop="showJson(season, 'season', true)" title="全语言深度探针">
                            <template #icon><n-icon><CodeIcon /></n-icon></template>
                          </n-button>
                        </n-space>
                      </n-space>
                    </template>
                    
                    <n-list size="small" hoverable style="margin-top: 8px">
                      <n-list-item v-for="ep in season.episodes" :key="ep.id">
                        <n-thing :title="`EP ${ep.episode_number} - ${ep.name}`">
                          <template #header-extra>
                            <n-space>
                              <n-button secondary circle size="tiny" type="default" @click="showJson(ep, 'episode', false)" title="查看当前快照">
                                <template #icon><n-icon><SnippetIcon /></n-icon></template>
                              </n-button>
                              <n-button secondary circle size="tiny" type="primary" @click="showJson(ep, 'episode', true)" title="全语言深度探针">
                                <template #icon><n-icon><CodeIcon /></n-icon></template>
                              </n-button>
                            </n-space>
                          </template>
                          <template #description>
                            <n-space size="small">
                              <n-tag size="tiny" type="warning">⭐ {{ ep.vote_average }}</n-tag>
                              <n-tag size="tiny" type="info">{{ ep.air_date }}</n-tag>
                              <n-tag v-if="ep.runtime" size="tiny">{{ ep.runtime }} min</n-tag>
                            </n-space>
                            <n-p depth="3" style="font-size: 12px; margin-top: 6px">{{ ep.overview }}</n-p>
                          </template>
                        </n-thing>
                      </n-list-item>
                    </n-list>
                  </n-collapse-item>
                </n-collapse>
              </div>
              <div v-else-if="detailForm.media_type === 'tv' && !detailForm.recursive" style="margin-top: 12px">
                <n-alert type="info" size="small">仅获取了剧集概况，如需查看季、集详情，请在左侧开启“深度递归抓取”后重新执行。</n-alert>
              </div>
            </n-card>
          </div>
          <div v-else class="empty-holder">
            <n-empty description="等待抓取数据..." />
          </div>
        </n-gi>
      </n-grid>

      <!-- JSON 详情弹窗 -->
      <n-modal v-model:show="jsonModal.show" preset="card" style="width: 900px" :title="jsonModal.title">
        <n-progress
          v-if="jsonModal.loading"
          type="line"
          :percentage="100"
          :show-indicator="false"
          processing
          style="margin-bottom: 12px"
        />
        <div class="json-code-wrapper">
          <n-code :code="JSON.stringify(jsonModal.data, null, 2)" language="json" word-wrap />
        </div>
        <template #footer>
          <n-button block type="primary" secondary @click="copyRawJson">复制 JSON 数据</n-button>
        </template>
      </n-modal>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { 
  useMessage, NSpace, NH2, NH3, NText, NCard, NInput, NButton, 
  NCode, NTag, NEmpty, NGrid, NGi, NForm, NFormItem, NFormItemGi,
  NSelect, NDivider, NList, NListItem, NThing, NSwitch, NTabs, NTabPane,
  NDescriptions, NDescriptionsItem, NCollapse, NCollapseItem, NP, NIcon, NAlert, NModal, NCheckbox, NProgress
} from 'naive-ui'
import { 
  TerminalOutlined as CodeIcon,
  ArticleOutlined as SnippetIcon,
  TranslateOutlined as TitleIcon,
  LabelOutlined as AliasIcon,
  BusinessOutlined as CompanyIcon,
  StyleOutlined as GenreIcon,
  LocalOfferOutlined as TagIcon
} from '@vicons/material'
import axios from 'axios'
import { copyElementContent } from '../../utils/clipboard'

const message = useMessage()
const activeTab = ref('search')
const searchLoading = ref(false)
const searchResults = ref<any[]>([])
const detailLoading = ref(false)
const detailResult = ref<any>(null)

// 选项配置
const mediaTypeOptions = [
  { label: '电影 (Movie)', value: 'movie' },
  { label: '剧集 (TV)', value: 'tv' }
]

const languageOptions = [
  { label: '全语言抓取 (All Translations)', value: 'all' },
  { label: '简体中文 (zh-CN)', value: 'zh-CN' },
  { label: '繁体中文 (zh-TW)', value: 'zh-TW' },
  { label: '英文 (en-US)', value: 'en-US' },
  { label: '日语 (ja-JP)', value: 'ja-JP' }
]

const searchForm = reactive({
  query: '',
  media_type: 'movie',
  language: 'zh-CN'
})

const detailForm = reactive({
  tmdb_id: '',
  media_type: 'movie',
  language: 'zh-CN',
  recursive: false
})

// --- 计算属性 ---

// 全量标题池
const titlePool = computed(() => {
  if (!detailResult.value || !detailResult.value.translations) return []
  const titles = new Set<string>()
  
  // 基础字段
  if (detailResult.value.title) titles.add(detailResult.value.title)
  if (detailResult.value.name) titles.add(detailResult.value.name)
  if (detailResult.value.original_title) titles.add(detailResult.value.original_title)
  if (detailResult.value.original_name) titles.add(detailResult.value.original_name)
  
  // 翻译列表
  const trans = detailResult.value.translations.translations || []
  trans.forEach((t: any) => {
    if (t.data?.title) titles.add(t.data.title)
    if (t.data?.name) titles.add(t.data.name)
  })
  
  return Array.from(titles).sort()
})

// 全量别名池
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

// 关键词列表
const keywordsList = computed(() => {
  if (!detailResult.value) return []
  const kData = detailResult.value.keywords
  return kData?.keywords || kData?.results || []
})

// --- 业务逻辑 ---

const handleSearch = async () => {
  if (!searchForm.query) return
  searchLoading.value = true
  try {
    const res = await axios.get('/api/tmdb-lab/search', { params: searchForm })
    searchResults.value = res.data.results || []
    if (searchResults.value.length === 0) message.warning('未找到相关结果')
  } catch (e) {
    message.error('搜索异常')
  } finally {
    searchLoading.value = false
  }
}

const fillDetail = (item: any) => {
  detailForm.tmdb_id = item.id.toString()
  detailForm.media_type = searchForm.media_type
  detailForm.language = searchForm.language
  detailForm.recursive = (searchForm.media_type === 'tv')
  activeTab.value = 'direct'
  message.info('已填入 ID，请确认配置后启动抓取')
}

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
    const res = await axios.get('/api/tmdb-lab/fetch', { params })
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

// JSON 弹窗逻辑
const jsonModal = reactive({
  show: false,
  title: '原始 JSON 数据',
  loading: false,
  data: {} as any
})

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

const fetchFullSeason = async (season: any) => {
  jsonModal.loading = true
  jsonModal.title = `深度探针: ${season.name}`
  jsonModal.show = true
  jsonModal.data = { message: '正在从 TMDB 实时抓取该季全量数据...' }
  
  try {
    const isAll = detailForm.language === 'all'
    const res = await axios.get('/api/tmdb-lab/fetch-season', {
      params: {
        tmdb_id: detailResult.value.id,
        season_number: season.season_number,
        language: isAll ? '' : detailForm.language,
        include_translations: isAll
      }
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
    const res = await axios.get('/api/tmdb-lab/fetch-episode', {
      params: {
        tmdb_id: detailResult.value.id,
        season_number: ep.season_number,
        episode_number: ep.episode_number,
        language: isAll ? '' : detailForm.language,
        include_translations: isAll
      }
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

const copyRawJson = () => {
  const selector = document.querySelector('.json-code-wrapper pre') ? '.json-code-wrapper pre' : '.json-code-wrapper'
  if (copyElementContent(selector)) {
    message.success('已复制到剪贴板')
  } else {
    message.error('复制失败')
  }
}
</script>

<style scoped>
.toolkit-container { 
  width: 100%;
  transition: all 0.3s ease;
}
.search-results-list {
  margin-top: 12px;
  max-height: 400px;
  overflow-y: auto;
}
.json-code-wrapper {
  background: #000;
  padding: 16px;
  border-radius: 8px;
  max-height: 65vh;
  overflow-y: auto;
}
.overview-box {
  background: rgba(255, 255, 255, 0.03);
  padding: 12px;
  border-left: 4px solid var(--primary-color);
  border-radius: 4px;
}
.empty-holder {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed var(--border-color);
  border-radius: 8px;
}
.results-area {
  animation: slide-up 0.3s ease-out;
}
@keyframes slide-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 统一分拣参考表样式 - 使用变量 */
.lab-report-card {
  margin-top: var(--space-lg);
  background: var(--modal-bg-color) !important;
  border: 1px solid var(--primary-border-color) !important;
  border-radius: 8px;
  overflow: hidden;
}
.report-header {
  background: linear-gradient(90deg, var(--primary-border-color) 0%, transparent 100%);
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--primary-border-color);
  display: flex;
  align-items: center;
}
.report-title {
  font-family: var(--font-mono);
  font-weight: 800;
  color: var(--primary-color);
  letter-spacing: 1px;
  font-size: 1rem;
  text-shadow: 0 0 8px var(--primary-border-color);
}
.report-row {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-color);
}
.report-row:last-child { border-bottom: none; }
.row-label {
  font-size: 0.8rem;
  color: var(--primary-color);
  opacity: 0.8;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.data-tag {
  font-family: var(--font-mono);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.85rem;
  color: var(--text-color);
  display: inline-block;
  margin: 0 0.5rem 0.5rem 0;
  transition: all 0.2s;
}
.data-tag:hover {
  border-color: var(--primary-color);
  background: rgba(255, 255, 255, 0.05);
}
.tag-orange {
  color: #f0a020;
  border-color: rgba(240, 160, 32, 0.3);
}
.tag-orange:hover {
  border-color: #f0a020;
}
.pool-box {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color);
  padding: 0.75rem;
  border-radius: 6px;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--text-color);
  opacity: 0.9;
  word-break: break-all;
}
.alias-text { color: #f0a020 !important; }
</style>
