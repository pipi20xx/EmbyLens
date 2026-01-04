<template>
  <div class="toolkit-container">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">TMDB ID 深度搜索</n-text></n-h2>
        <n-text depth="3">根据 TMDB 唯一标识符反向检索您的 Emby 媒体库，并递归解析剧集的完整季/集结构。</n-text>
      </div>

      <!-- 1. 搜索配置 -->
      <n-card title="检索配置" size="small">
        <n-form label-placement="left" label-width="100">
          <n-grid :cols="2" :x-gap="24">
            <n-form-item-gi label="TMDB ID">
              <n-input v-model:value="form.tmdb_id" placeholder="输入 ID (如: 94359)" @keyup.enter="handleSearch" />
            </n-form-item-gi>
            <n-form-item-gi label="检索范围">
              <n-checkbox-group v-model:value="searchTypes">
                <n-space>
                  <n-checkbox value="movies">电影</n-checkbox>
                  <n-checkbox value="series">剧集</n-checkbox>
                </n-space>
              </n-checkbox-group>
            </n-form-item-gi>
          </n-grid>
          <n-space justify="end">
            <n-button type="primary" @click="handleSearch" :loading="loading">
              启动深度检索
            </n-button>
          </n-space>
        </n-form>
      </n-card>

      <!-- 2. 结果展示区 -->
      <div v-if="results.length > 0" class="results-area">
        <n-h3>
          <n-space align="center">
            <n-icon color="#bb86fc"><SearchIcon /></n-icon>
            <span>搜索结果 ({{ results.length }})</span>
          </n-space>
        </n-h3>
        
        <n-collapse accordion :default-expanded-names="results[0].Id">
          <n-collapse-item v-for="item in results" :key="item.Id" :name="item.Id">
            <template #header>
              <n-space align="center" style="width: 100%" justify="space-between">
                <n-space align="center">
                  <n-text strong style="font-size: 16px">{{ item.Name }}</n-text>
                  <n-tag size="small" type="primary" round quaternary>{{ item.ProductionYear }}</n-tag>
                  <n-tag size="small" :type="item.Type === 'Series' ? 'info' : 'success'">{{ item.Type }}</n-tag>
                </n-space>
                <n-button quaternary circle size="small" type="primary" @click.stop="showJson(item)">
                  <template #icon><n-icon><CodeIcon /></n-icon></template>
                </n-button>
              </n-space>
            </template>
            
            <n-card :bordered="false" size="small" embedded style="margin-top: 8px">
              <!-- 本体详情顶栏 -->
              <div style="display: flex; justify-content: flex-end; margin-bottom: 12px">
                <n-button secondary type="primary" size="tiny" @click="showJson(item)">
                  <template #icon><n-icon><CodeIcon /></n-icon></template>
                  查看该条目原始 JSON
                </n-button>
              </div>

              <n-descriptions label-placement="left" :column="2" size="small" bordered label-style="width: 120px">
                <n-descriptions-item label="物理路径" :span="2">
                  <n-text depth="3" style="word-break: break-all">{{ item.Path }}</n-text>
                </n-descriptions-item>
                <n-descriptions-item label="TMDB / Emby ID">
                  <n-space>
                    <n-tag size="tiny" type="info">TMDB: {{ item.ProviderIds?.Tmdb || 'N/A' }}</n-tag>
                    <n-tag size="tiny">EMBY: {{ item.Id }}</n-tag>
                  </n-space>
                </n-descriptions-item>
                <n-descriptions-item label="社区评分">
                  <n-rate readonly :default-value="Math.round(item.CommunityRating || 0) / 2" size="small" />
                  <n-text depth="3" style="margin-left: 8px">{{ item.CommunityRating }}</n-text>
                </n-descriptions-item>
                <n-descriptions-item label="首播/上映">{{ item.PremiereDate?.split('T')[0] || 'N/A' }}</n-descriptions-item>
                <n-descriptions-item label="项目状态">
                  <n-tag :type="item.Status === 'Continuing' ? 'success' : 'default'" size="tiny" quaternary>
                    {{ item.Status === 'Continuing' ? '正在连载' : (item.Status || 'N/A') }}
                  </n-tag>
                </n-descriptions-item>
                <n-descriptions-item label="类型标签" :span="2">
                  <n-space size="small">
                    <n-tag v-for="g in item.Genres" :key="g" size="tiny" round tertiary>{{ g }}</n-tag>
                  </n-space>
                </n-descriptions-item>
                <n-descriptions-item label="制作商" :span="2">
                  <n-text depth="3">{{ item.Studios?.map((s:any)=>s.Name).join(', ') || 'N/A' }}</n-text>
                </n-descriptions-item>
              </n-descriptions>

              <div class="overview-box" style="margin-top: 16px">
                <n-p depth="3" style="margin: 0; font-size: 13px">{{ item.Overview || '暂无简介' }}</n-p>
              </div>

              <!-- 剧集结构 -->
              <div v-if="item.Seasons && item.Seasons.length > 0" style="margin-top: 24px">
                <n-divider title-placement="left">
                  <n-text type="primary" strong>季 / 集 级联结构 (JSON 探针可点击)</n-text>
                </n-divider>
                <n-collapse>
                  <n-collapse-item v-for="season in item.Seasons" :key="season.Id" :name="season.Id">
                    <template #header>
                      <n-space justify="space-between" style="width: 100%" align="center">
                        <n-text strong>{{ season.Name }}</n-text>
                        <n-button secondary circle size="tiny" type="info" @click.stop="showJson(season)">
                          <template #icon><n-icon><CodeIcon /></n-icon></template>
                        </n-button>
                      </n-space>
                    </template>
                    <n-list size="small" hoverable>
                      <n-list-item v-for="ep in season.Episodes" :key="ep.Id">
                        <template #prefix><n-tag size="tiny" round>EP {{ ep.IndexNumber }}</n-tag></template>
                        <n-text>{{ ep.Name }}</n-text>
                        <template #suffix>
                          <n-button secondary circle size="tiny" type="primary" @click="showJson(ep)">
                            <template #icon><n-icon color="#bb86fc"><CodeIcon /></n-icon></template>
                          </n-button>
                        </template>
                      </n-list-item>
                    </n-list>
                  </n-collapse-item>
                </n-collapse>
              </div>
            </n-card>
          </n-collapse-item>
        </n-collapse>
      </div>

      <n-empty v-else-if="searched && !loading" description="未能在您的 Emby 库中找到匹配项" />

      <!-- 全局 JSON 弹窗 -->
      <n-modal v-model:show="jsonModal.show" preset="card" style="width: 900px" title="元数据原始 JSON 审计">
        <template #header-extra>
          <n-tag type="info" size="small">{{ jsonModal.title }}</n-tag>
        </template>
        <div class="json-code-wrapper">
          <n-code :code="JSON.stringify(jsonModal.data, null, 2)" language="json" word-wrap />
        </div>
        <template #footer>
          <n-button block type="primary" secondary @click="copyRawJson">
            一键复制完整 JSON (用于手动调试)
          </n-button>
        </template>
      </n-modal>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { 
  useMessage, NSpace, NH2, NH3, NText, NCard, NInput, NButton, 
  NCheckboxGroup, NCheckbox, NCode, NTag, NEmpty, NCollapse, 
  NCollapseItem, NGrid, NFormItemGi, NForm, NDescriptions, 
  NDescriptionsItem, NDivider, NList, NListItem, NRate, NModal, NP, NIcon 
} from 'naive-ui'
import { 
  TerminalOutlined as CodeIcon,
  SearchOutlined as SearchIcon,
  FolderZipOutlined as FileIcon
} from '@vicons/material'
import axios from 'axios'

const message = useMessage()
const loading = ref(false)
const searched = ref(false)
const results = ref<any[]>([])
const searchTypes = ref(['movies', 'series'])
const form = reactive({ tmdb_id: '' })
const jsonModal = reactive({ show: false, title: '', data: {} as any })

const showJson = (item: any) => { 
  jsonModal.data = item; 
  jsonModal.title = item.Name || `Item ID: ${item.Id}`;
  jsonModal.show = true; 
}

const copyRawJson = () => { 
  navigator.clipboard.writeText(JSON.stringify(jsonModal.data, null, 2)); 
  message.success('JSON 已复制到剪贴板'); 
}

const handleSearch = async () => {
  if (!form.tmdb_id) {
    message.warning('请输入 TMDB ID');
    return;
  }
  loading.value = true
  searched.value = true
  results.value = []
  try {
    const res = await axios.post('/api/tmdb-search/search-by-id', {
      tmdb_id: form.tmdb_id,
      search_movies: searchTypes.value.includes('movies'),
      search_series: searchTypes.value.includes('series')
    })
    results.value = res.data.results
    if (results.value.length === 0) {
      message.info('未找到匹配项目')
    }
  } catch (e) { 
    message.error('搜索任务异常') 
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.toolkit-container { max-width: 1200px; margin: 0 auto; }
.json-code-wrapper { 
  background: #050505; 
  padding: 16px; 
  border-radius: 8px; 
  max-height: 65vh; 
  overflow-y: auto; 
  border: 1px solid #333;
}
.overview-box { 
  background: rgba(255,255,255,0.03); 
  padding: 16px; 
  border-left: 4px solid #bb86fc; 
  border-radius: 4px;
}
:deep(.n-code) {
  font-family: 'Fira Code', monospace;
  font-size: 13px;
}
</style>
