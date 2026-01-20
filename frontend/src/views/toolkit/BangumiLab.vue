<template>
  <div class="toolkit-container">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">Bangumi 实验室</n-text></n-h2>
        <n-text depth="3">直接从 Bangumi (番组计划) 官方抓取条目与角色元数据。采用乐高模块化设计。</n-text>
      </div>

      <n-grid :cols="24" :x-gap="12" :y-gap="12" item-responsive>
        <!-- 1. 输入面板 -->
        <n-gi :span="24" :lspan="8">
          <n-space vertical size="large">
            <n-card title="检索/定位" size="small">
              <n-tabs type="line" animated v-model:value="activeTab">
                <n-tab-pane name="search" tab="关键词搜索">
                  <!-- 零件 E: 搜索面板 -->
                  <SearchPanel 
                    :searchForm="searchForm" 
                    :results="searchResults" 
                    :loading="searchLoading"
                    @search="handleSearch"
                    @select="fillSubject"
                  />
                </n-tab-pane>

                <n-tab-pane name="direct" tab="直接 ID 抓取">
                  <n-form label-placement="top">
                    <n-form-item label="Subject ID (条目 ID)">
                      <n-input v-model:value="form.subject_id" placeholder="例如: 253, 302506..." @keyup.enter="handleFetchAll" />
                    </n-form-item>
                    <n-button block type="primary" :loading="loading" @click="handleFetchAll">执行全量抓取</n-button>
                  </n-form>
                </n-tab-pane>
              </n-tabs>
            </n-card>

            <n-card v-if="subjectResult" title="快捷工具" size="small">
              <n-space vertical>
                <n-button block secondary @click="showJson(subjectResult, 'Subject')">查看条目原始 JSON</n-button>
                <n-button block secondary @click="showJson(episodesResult, 'Episodes')">查看章节原始 JSON</n-button>
                <n-button block secondary @click="showJson(charactersResult, 'Characters')">查看角色原始 JSON</n-button>
              </n-space>
            </n-card>
          </n-space>
        </n-gi>

        <!-- 2. 结果展示区 (乐高组装) -->
        <n-gi :span="24" :lspan="16">
          <div v-if="subjectResult" class="results-area">
            <n-space vertical size="large">
              <!-- 零件 A: 详情卡片 -->
              <SubjectCard :subject="subjectResult" />
              
              <!-- 零件 B: 探针报告 -->
              <MetadataCard 
                :subject="subjectResult" 
                :infobox="infoboxList" 
                :metaTags="uniqueMetaTags"
                :titlePool="titlePool" 
                :aliasPool="aliasPool" 
              />

              <!-- 零件 C: 角色面板 -->
              <CharacterPanel :characters="charactersResult" />

              <!-- 零件 D: 章节面板 -->
              <EpisodePanel :episodes="episodesResult" />
            </n-space>
          </div>
          <div v-else class="empty-holder">
            <n-empty description="等待抓取 Bangumi 数据..." />
          </div>
        </n-gi>
      </n-grid>

      <!-- JSON 弹窗 (公共零件) -->
      <n-modal v-model:show="jsonModal.show" preset="card" style="width: 800px" :title="jsonModal.title">
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
import { reactive, ref } from 'vue'
import { 
  NSpace, NH2, NText, NCard, NInput, NButton, NEmpty, NGrid, NGi, NForm, NFormItem, NModal, NCode, useMessage,
  NTabs, NTabPane
} from 'naive-ui'
import { useBangumi } from './bangumi/useBangumi'
import SubjectCard from './bangumi/components/SubjectCard.vue'
import MetadataCard from './bangumi/components/MetadataCard.vue'
import CharacterPanel from './bangumi/components/CharacterPanel.vue'
import EpisodePanel from './bangumi/components/EpisodePanel.vue'
import SearchPanel from './bangumi/components/SearchPanel.vue'

const message = useMessage()
const { 
  loading, searchLoading, form, searchForm, subjectResult, charactersResult, episodesResult, searchResults,
  infoboxList, uniqueMetaTags, titlePool, aliasPool, handleSearch, handleFetchAll 
} = useBangumi()

const activeTab = ref('search')

const fillSubject = (item: any) => {
  form.subject_id = item.id.toString()
  activeTab.value = 'direct'
  handleFetchAll()
}

// JSON 弹窗逻辑
const jsonModal = reactive({
  show: false,
  title: '原始 JSON 数据',
  data: {} as any
})

const showJson = (data: any, title: string) => {
  jsonModal.data = data
  jsonModal.title = `Bangumi ${title} JSON`
  jsonModal.show = true
}

const copyRawJson = () => {
  const text = JSON.stringify(jsonModal.data, null, 2)
  const textArea = document.createElement("textarea")
  textArea.value = text
  document.body.appendChild(textArea)
  textArea.select()
  try {
    document.execCommand('copy')
    message.success('已复制到剪贴板')
  } catch (err) {
    message.error('复制失败')
  }
  document.body.removeChild(textArea)
}
</script>

<style scoped>
.toolkit-container { width: 100%; }
.json-code-wrapper { background: #000; padding: 16px; border-radius: 8px; max-height: 60vh; overflow-y: auto; }
.empty-holder {
  height: 400px; display: flex; align-items: center; justify-content: center;
  border: 1px dashed var(--border-color); border-radius: 8px;
}
.results-area { animation: slide-up 0.3s ease-out; }
@keyframes slide-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>