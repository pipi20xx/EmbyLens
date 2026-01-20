<template>
  <div class="toolkit-container">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">TMDB 演员实验室</n-text></n-h2>
        <n-text depth="3">基于 TMDB 数据的智能探测工具。能够根据出生地自动匹配母语姓名，并生成全量别名池。</n-text>
      </div>

      <n-grid :cols="24" :x-gap="12" :y-gap="12" item-responsive>
        <!-- 左侧：输入与搜索 -->
        <n-gi :span="24" :lspan="8">
          <n-space vertical size="large">
            <n-card title="1. 演员定位" size="small">
              <n-tabs v-model:value="activeTab" type="line" animated>
                <n-tab-pane name="search" tab="姓名搜索">
                  <n-form label-placement="top">
                    <n-form-item label="演员姓名">
                      <n-input v-model:value="searchQuery" placeholder="中文或英文姓名..." @keyup.enter="handleSearch" />
                    </n-form-item>
                    <n-button block type="primary" secondary :loading="searchLoading" @click="handleSearch">执行全局检索</n-button>
                  </n-form>
                  
                  <div v-if="searchResults.length > 0" class="search-results-list">
                    <n-divider title-placement="left">搜索结果</n-divider>
                    <n-list hoverable clickable size="small">
                      <n-list-item v-for="person in searchResults" :key="person.id" @click="fillId(person)">
                        <template #prefix>
                          <n-avatar round size="small" :src="person.profile_path ? `https://image.tmdb.org/t/p/w200${person.profile_path}` : ''" />
                        </template>
                        <n-thing :title="person.name" :description="`Known for: ${person.known_for_department} | ID: ${person.id}`" />
                      </n-list-item>
                    </n-list>
                  </div>
                </n-tab-pane>
                <n-tab-pane name="direct" tab="直接 ID 探测">
                  <n-form label-placement="top">
                    <n-form-item label="TMDB Person ID">
                      <n-input v-model:value="personId" placeholder="例如: 60063" />
                    </n-form-item>
                    <n-form-item label="抓取语言 / 模式">
                      <n-select v-model:value="detailLanguage" :options="languageOptions" filterable tag />
                    </n-form-item>
                    <n-button block type="primary" :loading="analyzeLoading" @click="handleAnalyze">启动深度分析</n-button>
                  </n-form>
                </n-tab-pane>
              </n-tabs>
            </n-card>
          </n-space>
        </n-gi>

        <!-- 右侧：分析报告 -->
        <n-gi :span="24" :lspan="16">
          <div v-if="result" class="results-area">
            <n-card size="small" class="actor-report-card">
              <!-- 头像与核心身份 -->
              <div class="actor-hero">
                <n-avatar 
                  round 
                  :size="100" 
                  :src="result.profile_path ? `https://image.tmdb.org/t/p/h632${result.profile_path}` : ''"
                  class="hero-avatar"
                />
                <div class="hero-info">
                  <n-h2 style="margin: 0; color: var(--primary-color)">{{ result.origin_name }}</n-h2>
                  <n-text depth="3" style="font-size: 16px">{{ result.main_name }}</n-text>
                  <n-space style="margin-top: 8px">
                    <n-tag size="small" type="primary" quaternary>{{ result.chinese_name }}</n-tag>
                    <n-tag v-if="result.imdb_id" size="small" type="info" quaternary>IMDB: {{ result.imdb_id }}</n-tag>
                    <n-tag size="small" tertiary>TMDB: {{ result.id }}</n-tag>
                  </n-space>
                </div>
                <div class="hero-extra">
                  <n-button secondary circle type="primary" @click="showJson(result.raw)">
                    <template #icon><n-icon><CodeIcon /></n-icon></template>
                  </n-button>
                </div>
              </div>

              <!-- 详细情报对照表 -->
              <div class="lab-report-card" style="margin-top: 20px">
                <div class="report-header">
                  <n-icon color="#bb86fc" size="18" style="margin-right: 8px"><ReportIcon /></n-icon>
                  <span class="report-title">演员关键信息深度解析 (扫描报告)</span>
                </div>

                <div class="report-row">
                  <n-grid :cols="2">
                    <n-gi>
                      <div class="row-label">1. 中文/通用名</div>
                      <div class="row-content"><span class="data-tag">{{ result.chinese_name }}</span></div>
                    </n-gi>
                    <n-gi>
                      <div class="row-label">2. 原产地/母语名</div>
                      <div class="row-content"><span class="data-tag tag-purple">{{ result.origin_name }}</span></div>
                    </n-gi>
                  </n-grid>
                </div>

                <div class="report-row">
                  <n-grid :cols="2">
                    <n-gi>
                      <div class="row-label">3. 出生地</div>
                      <div class="row-content"><n-text depth="2">{{ result.place_of_birth || '未知' }}</n-text></div>
                    </n-gi>
                    <n-gi>
                      <div class="row-label">4. 生日/逝世</div>
                      <div class="row-content">
                        <n-text depth="2">{{ result.birthday || '未知' }}</n-text>
                        <n-text v-if="result.deathday" type="error"> 至 {{ result.deathday }}</n-text>
                      </div>
                    </n-gi>
                  </n-grid>
                </div>

                <div class="report-row">
                  <div class="row-label">5. 全量别名池 (Alias Pool - {{ result.name_pool.length }})</div>
                  <div class="row-content">
                    <span v-for="name in result.name_pool" :key="name" class="data-tag">{{ name }}</span>
                  </div>
                </div>

                <!-- 作品列表 - 改为文本列表 -->
                <div class="report-row">
                  <div class="row-label">6. 代表作品 (Top Works)</div>
                  <div class="works-text-list">
                    <div v-for="work in result.top_works" :key="work.id" class="work-text-item">
                      <n-space justify="space-between">
                        <n-space align="center">
                          <n-tag size="tiny" :type="work.media_type === 'movie' ? 'success' : 'info'" quaternary>
                            {{ work.media_type === 'movie' ? '电影' : '剧集' }}
                          </n-tag>
                          <n-text strong>{{ work.title }}</n-text>
                          <n-text depth="3">({{ work.original_title }})</n-text>
                        </n-space>
                        <n-space>
                          <n-text depth="3" style="font-family: monospace">{{ work.release_date || '未知' }}</n-text>
                          <n-text style="color: #f0a020">⭐ {{ work.vote_average?.toFixed(1) }}</n-text>
                        </n-space>
                      </n-space>
                    </div>
                  </div>
                </div>
              </div>
            </n-card>
          </div>
          <div v-else class="empty-holder">
            <n-empty description="等待探测指令..." />
          </div>
        </n-gi>
      </n-grid>

      <!-- JSON 弹窗 -->
      <n-modal v-model:show="jsonModal.show" preset="card" style="width: 900px" title="演员原始元数据 (Raw JSON)">
        <div class="json-code-wrapper">
          <n-code :code="JSON.stringify(jsonModal.data, null, 2)" language="json" word-wrap />
        </div>
      </n-modal>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { 
  useMessage, NSpace, NH2, NText, NCard, NInput, NButton, 
  NCode, NTag, NEmpty, NGrid, NGi, NForm, NFormItem,
  NSelect, NDivider, NList, NListItem, NThing, NSwitch, NTabs, NTabPane,
  NIcon, NModal, NAvatar
} from 'naive-ui'
import { 
  TerminalOutlined as CodeIcon,
  AssignmentIndOutlined as ReportIcon,
  SearchOutlined as SearchIcon
} from '@vicons/material'
import axios from 'axios'

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
    const res = await axios.get('/api/actors/search-tmdb', { params: { query: searchQuery.value } })
    searchResults.value = res.data.results || []
  } catch (e) {
    message.error('搜索异常')
  } finally {
    searchLoading.value = false
  }
}

const fillId = (person: any) => {
  personId.value = person.id.toString()
  activeTab.value = 'direct'
  handleAnalyze()
}

// 分析逻辑
const personId = ref('')
const detailLanguage = ref('zh-CN')
const analyzeLoading = ref(false)
const result = ref<any>(null)

const languageOptions = [
  { label: '全语言抓取 (All Translations)', value: 'all' },
  { label: '简体中文 (zh-CN)', value: 'zh-CN' },
  { label: '繁体中文 (zh-TW)', value: 'zh-TW' },
  { label: '英文 (en-US)', value: 'en-US' },
  { label: '日语 (ja-JP)', value: 'ja-JP' }
]

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
    const res = await axios.get('/api/actor-lab/analyze', { params })
    result.value = res.data
    message.success('深度分析完成')
  } catch (e) {
    message.error('分析失败')
  } finally {
    analyzeLoading.value = false
  }
}

// JSON 弹窗
const jsonModal = reactive({ show: false, data: {} })
const showJson = (data: any) => { jsonModal.data = data; jsonModal.show = true; }
</script>

<style scoped>
.toolkit-container { width: 100%; }
.search-results-list { margin-top: 12px; max-height: 400px; overflow-y: auto; }

.actor-hero {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px;
  background: linear-gradient(135deg, rgba(187, 134, 252, 0.05) 0%, transparent 100%);
  border-radius: 12px;
}
.hero-avatar { border: 3px solid var(--primary-border-color); box-shadow: 0 0 20px rgba(187, 134, 252, 0.2); }
.hero-info { flex: 1; }

.lab-report-card {
  background: var(--modal-bg-color) !important;
  border: 1px solid var(--primary-border-color) !important;
  border-radius: 8px;
  overflow: hidden;
}
.report-header {
  background: linear-gradient(90deg, var(--primary-border-color) 0%, transparent 100%);
  padding: 10px 16px;
  border-bottom: 1px solid var(--primary-border-color);
  display: flex;
  align-items: center;
}
.report-title {
  font-family: 'Fira Code', monospace;
  font-weight: 800;
  color: var(--primary-color);
  letter-spacing: 1px;
}
.report-row { padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.row-label { font-size: 12px; color: var(--primary-color); opacity: 0.8; margin-bottom: 6px; }

.data-tag {
  font-family: 'Fira Code', monospace;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
  margin: 0 6px 6px 0;
  display: inline-block;
}
.tag-purple { color: var(--primary-color); border-color: var(--primary-border-color); }

.works-text-list {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  padding: 8px;
  border: 1px solid var(--border-color);
}
.work-text-item {
  padding: 6px 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}
.work-text-item:last-child { border-bottom: none; }
.work-text-item:hover { background: rgba(255, 255, 255, 0.02); }

.json-code-wrapper { 
  background: #000; padding: 16px; border-radius: 8px; 
  max-height: 65vh; overflow-y: auto; border: 1px solid var(--border-color); 
}
.empty-holder {
  height: 400px; display: flex; align-items: center; justify-content: center;
  border: 1px dashed var(--border-color); border-radius: 8px;
}
</style>
