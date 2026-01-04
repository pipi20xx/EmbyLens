<template>
  <div class="toolkit-container">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">TMDB ID 深度搜索 (全信息版)</n-text></n-h2>
        <n-text depth="3">根据 TMDB ID 递归检索项目及其所有季、集的完整元数据详情。</n-text>
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
            <n-button type="primary" @click="handleSearch" :loading="loading">启动全量检索</n-button>
          </n-space>
        </n-form>
      </n-card>

      <!-- 2. 结果展示区 -->
      <div v-if="results.length > 0" class="results-area">
        <n-h3>搜索结果 ({{ results.length }})</n-h3>
        <n-collapse accordion :default-expanded-names="results[0].Id">
          <n-collapse-item v-for="item in results" :key="item.Id" :name="item.Id">
            <!-- 剧集标题栏 -->
            <template #header>
              <n-space align="center" style="width: 100%" justify="space-between">
                <n-space align="center">
                  <n-text strong style="font-size: 16px">{{ item.Name }}</n-text>
                  <n-tag size="small" type="primary" round quaternary>{{ item.ProductionYear }}</n-tag>
                  <n-tag size="small" :type="item.Type === 'Series' ? 'info' : 'success'">{{ item.Type }}</n-tag>
                </n-space>
                <n-button secondary circle size="small" type="primary" @click.stop="showJson(item)" title="本体 JSON">
                  <template #icon><n-icon><CodeIcon /></n-icon></template>
                </n-button>
              </n-space>
            </template>
            
            <n-card :bordered="false" size="small" embedded style="margin-top: 8px">
              <!-- 剧集/电影 详情描述 -->
              <n-descriptions label-placement="left" :column="2" size="small" bordered label-style="width: 120px">
                <n-descriptions-item label="名称">{{ item.Name }}</n-descriptions-item>
                <n-descriptions-item label="类型">{{ item.Type }}</n-descriptions-item>
                <n-descriptions-item label="Emby ID">{{ item.Id }}</n-descriptions-item>
                <n-descriptions-item label="路径" :span="2">{{ item.Path }}</n-descriptions-item>
                <n-descriptions-item label="提供者 ID" :span="2">
                  <n-space>
                    <n-tag v-for="(val, key) in item.ProviderIds" :key="key" size="tiny" type="info" quaternary>
                      {{ key }}: {{ val }}
                    </n-tag>
                  </n-space>
                </n-descriptions-item>
                <n-descriptions-item label="评分与分级">
                  <n-rate readonly :default-value="Math.round(item.CommunityRating || 0) / 2" size="small" />
                  <n-text depth="3" style="margin-left: 8px">{{ item.CommunityRating }} / {{ item.OfficialRating || 'NR' }}</n-text>
                </n-descriptions-item>
                <n-descriptions-item label="发行商/状态">
                  {{ item.Studios?.[0]?.Name || 'N/A' }} | {{ item.Status || 'Ended' }}
                </n-descriptions-item>
                <n-descriptions-item label="日期信息" :span="2">
                  首播: {{ item.PremiereDate?.split('T')[0] || 'N/A' }} 
                  <span v-if="item.EndDate"> | 结束: {{ item.EndDate?.split('T')[0] }}</span>
                </n-descriptions-item>
              </n-descriptions>

              <div class="overview-box" style="margin-top: 12px">
                <n-p depth="3" style="font-size: 13px">{{ item.Overview || '暂无简介' }}</n-p>
              </div>

              <!-- 递归层级：季 (Season) -->
              <div v-if="item.Seasons && item.Seasons.length > 0" style="margin-top: 24px">
                <n-divider title-placement="left"><n-text type="primary" strong>季与集 详细递归结构</n-text></n-divider>
                <n-collapse>
                  <n-collapse-item v-for="season in item.Seasons" :key="season.Id" :name="season.Id">
                    <template #header>
                      <n-space justify="space-between" style="width: 100%" align="center">
                        <n-text strong>{{ season.Name }} (ID: {{ season.Id }})</n-text>
                        <n-button secondary circle size="tiny" type="info" @click.stop="showJson(season)">
                          <template #icon><n-icon><CodeIcon /></n-icon></template>
                        </n-button>
                      </n-space>
                    </template>
                    
                    <!-- 季 详情 -->
                    <n-descriptions label-placement="left" :column="2" size="small" style="padding: 0 16px">
                      <n-descriptions-item label="季号">{{ season.IndexNumber }}</n-descriptions-item>
                      <n-descriptions-item label="父 ID">{{ season.ParentId }}</n-descriptions-item>
                      <n-descriptions-item label="年份">{{ season.ProductionYear }}</n-descriptions-item>
                      <n-descriptions-item label="已观看">{{ season.UserData?.Played ? '是' : '否' }} ({{ season.UserData?.PlayCount }}次)</n-descriptions-item>
                    </n-descriptions>

                    <!-- 递归层级：集 (Episode) -->
                    <n-list size="small" hoverable style="margin-top: 12px">
                      <n-list-item v-for="ep in season.Episodes" :key="ep.Id">
                        <n-thing :title="`EP ${ep.IndexNumber} - ${ep.Name}`">
                          <template #header-extra>
                            <n-button secondary circle size="tiny" type="primary" @click="showJson(ep)">
                              <template #icon><n-icon color="#bb86fc"><CodeIcon /></n-icon></template>
                            </n-button>
                          </template>
                          <template #description>
                            <n-descriptions label-placement="left" :column="2" size="tiny" style="margin-top: 4px">
                              <n-descriptions-item label="Emby ID">{{ ep.Id }}</n-descriptions-item>
                              <n-descriptions-item label="评分">{{ ep.CommunityRating || 'N/A' }}</n-descriptions-item>
                              <n-descriptions-item label="首播">{{ ep.PremiereDate?.split('T')[0] || 'N/A' }}</n-descriptions-item>
                              <n-descriptions-item label="时长">{{ Math.floor((ep.RunTimeTicks || 0) / 10000000 / 60) }} 分钟</n-descriptions-item>
                              <n-descriptions-item label="路径" :span="2">
                                <n-text depth="3" style="font-size: 11px">{{ ep.Path }}</n-text>
                              </n-descriptions-item>
                            </n-descriptions>
                            <n-p depth="3" style="font-size: 12px; margin-top: 8px; border-left: 2px solid #333; padding-left: 8px">
                              {{ ep.Overview || '暂无单集简介' }}
                            </n-p>
                          </template>
                        </n-thing>
                      </n-list-item>
                    </n-list>
                  </n-collapse-item>
                </n-collapse>
              </div>
            </n-card>
          </n-collapse-item>
        </n-collapse>
      </div>

      <n-empty v-else-if="searched && !loading" description="未找到匹配项目" />

      <!-- JSON 弹窗 -->
      <n-modal v-model:show="jsonModal.show" preset="card" style="width: 900px" title="元数据原始 JSON 快照">
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
import { ref, reactive } from 'vue'
import { 
  useMessage, NSpace, NH2, NH3, NText, NCard, NInput, NButton, 
  NCheckboxGroup, NCheckbox, NCode, NTag, NEmpty, NCollapse, 
  NCollapseItem, NGrid, NFormItemGi, NForm, NDescriptions, 
  NDescriptionsItem, NDivider, NList, NListItem, NRate, NModal, NP, NIcon, NThing 
} from 'naive-ui'
import { TerminalOutlined as CodeIcon } from '@vicons/material'
import axios from 'axios'

const message = useMessage()
const loading = ref(false)
const searched = ref(false)
const results = ref<any[]>([])
const searchTypes = ref(['movies', 'series'])
const form = reactive({ tmdb_id: '' })
const jsonModal = reactive({ show: false, data: {} as any })

const showJson = (item: any) => { jsonModal.data = item; jsonModal.show = true; }
const copyRawJson = () => { navigator.clipboard.writeText(JSON.stringify(jsonModal.data, null, 2)); message.success('已复制'); }

const handleSearch = async () => {
  if (!form.tmdb_id) return
  loading.value = true; searched.value = true; results.value = []
  try {
    const res = await axios.post('/api/tmdb-search/search-by-id', {
      tmdb_id: form.tmdb_id,
      search_movies: searchTypes.value.includes('movies'),
      search_series: searchTypes.value.includes('series')
    })
    results.value = res.data.results
  } catch (e) { message.error('搜索异常') }
  finally { loading.value = false }
}
</script>

<style scoped>
.toolkit-container { max-width: 1200px; margin: 0 auto; }
.json-code-wrapper { background: #050505; padding: 16px; border-radius: 8px; max-height: 65vh; overflow-y: auto; }
.overview-box { background: rgba(255,255,255,0.03); padding: 12px; border-left: 4px solid #bb86fc; border-radius: 4px; }
</style>