<template>
  <div class="toolkit-container">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">剧集 TMDB ID 反向查询</n-text></n-h2>
        <n-text depth="3">根据单集 (Episode) ID 向上追溯其所属剧集并提取 TMDB 唯一标识符。</n-text>
      </div>

      <!-- 1. 输入表单 -->
      <n-card title="单集溯源 (Reverse Mapping)" size="small">
        <template #header-extra>
          <n-tag type="warning" round quaternary size="small">Series Lookup</n-tag>
        </template>
        <n-input-group>
          <n-input-group-label style="width: 140px">Emby 单集 ID</n-input-group-label>
          <n-input v-model:value="episodeId" placeholder="输入 Episode ID (例如: 108)" @keyup.enter="handleLookup" />
          <n-button type="primary" @click="handleLookup" :loading="loading">立即追溯</n-button>
        </n-input-group>
      </n-card>

      <!-- 2. 结果展示 -->
      <n-grid v-if="result" :cols="1">
        <n-gi>
          <n-card :title="result.series_name" size="small" segmented>
            <template #header-extra>
              <n-text type="info">已定位到上级剧集</n-text>
            </template>
            <n-descriptions label-placement="left" :column="2" bordered size="small">
              <n-descriptions-item label="剧集名称">{{ result.series_name }}</n-descriptions-item>
              <n-descriptions-item label="TMDB ID">
                <n-tag type="success" size="small" round>{{ result.tmdb_id }}</n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="剧集 ID (SeriesId)">{{ result.series_id }}</n-descriptions-item>
              <n-descriptions-item label="媒体类型">{{ result.item_type }}</n-descriptions-item>
            </n-descriptions>
            <template #footer>
              <n-button quaternary size="tiny" block @click="copyTmdb">复制 TMDB ID</n-button>
            </template>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 3. 调试快照 -->
      <n-card title="调试：底层溯源逻辑预览" embedded :bordered="false">
        <n-code :code="`# 溯源流程解析:
# 1. GET /Items/${episodeId || 'ID'} -> 提取 SeriesId
# 2. GET /Items/{SeriesId} -> 提取 ProviderIds.Tmdb`" language="bash" />
      </n-card>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { 
  useMessage, NSpace, NH2, NText, NCard, NInput, NButton, NInputGroup, 
  NInputGroupLabel, NCode, NTag, NDescriptions, NDescriptionsItem, NGi, NGrid 
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const episodeId = ref('')
const loading = ref(false)
const result = ref<any>(null)

const handleLookup = async () => {
  if (!episodeId.value) {
    message.warning('请输入单集 ID')
    return
  }
  loading.value = true
  result.value = null
  try {
    const res = await axios.get('/api/tmdb/reverse-tmdb', {
      params: { episode_id: episodeId.value }
    })
    result.value = res.data
    message.success('溯源成功！')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '反向查询失败')
  } finally {
    loading.value = false
  }
}

const copyTmdb = () => {
  if (result.value) {
    navigator.clipboard.writeText(result.value.tmdb_id)
    message.info('TMDB ID 已复制')
  }
}
</script>

<style scoped>
.toolkit-container { 
  width: 100%; 
}
:deep(.n-h2 .n-text--primary-type) {
  color: var(--primary-color);
}
</style>
