<template>
  <div class="toolkit-container">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">类型与标签管理 (1:1 源码复刻)</n-text></n-h2>
        <n-text depth="3">提供类型映射、一键移除及批量新增功能。严格对齐 emby-box 的 GenreItems 深度处理逻辑。</n-text>
      </div>

      <!-- 1. 通用执行参数 -->
      <n-card title="通用执行参数" size="small" segmented>
        <n-form label-placement="left" label-width="120">
          <n-form-item label="目标媒体库">
            <n-select 
              v-model:value="common.lib_names" 
              multiple 
              filterable 
              tag 
              placeholder="输入媒体库名称并回车" 
            />
          </n-form-item>
          <n-form-item label="执行模式">
            <n-switch v-model:value="common.dry_run">
              <template #checked>预览模式 (Dry Run)</template>
              <template #unchecked>实调模式 (Execute)</template>
            </n-switch>
          </n-form-item>
        </n-form>
      </n-card>

      <!-- 2. 三大原子工具 -->
      <n-grid :cols="3" :x-gap="12">
        <!-- 工具 1: 类型映射 -->
        <n-gi>
          <n-card title="类型映射 (Mapper)" size="small" status="primary">
            <n-space vertical>
              <n-input v-model:value="forms.map.old" placeholder="旧类型 (如: 动漫)" size="small" />
              <n-input v-model:value="forms.map.new_name" placeholder="新类型 (如: Anime)" size="small" />
              <n-input v-model:value="forms.map.new_id" placeholder="新 ID (如: 16)" size="small" />
              <n-button block type="primary" secondary @click="handleAction('mapper')">执行映射</n-button>
            </n-space>
          </n-card>
        </n-gi>

        <!-- 工具 2: 类型移除 -->
        <n-gi>
          <n-card title="类型移除 (Remover)" size="small" status="error">
            <n-space vertical>
              <n-input v-model:value="forms.remove.tag" placeholder="要移除的标签名" size="small" />
              <n-p depth="3" style="font-size: 12px">留空则移除所选库中项目的所有类型。</n-p>
              <n-button block type="error" ghost @click="handleAction('remover')">执行移除</n-button>
            </n-space>
          </n-card>
        </n-gi>

        <!-- 工具 3: 类型新增 (Adder) -->
        <n-gi>
          <n-card title="类型新增 (Adder)" size="small" status="success">
            <n-space vertical>
              <n-input v-model:value="forms.add.name" placeholder="新增类型名" size="small" />
              <n-input v-model:value="forms.add.id" placeholder="新增 ID (可选)" size="small" />
              <n-button block type="success" secondary @click="handleAction('genre_adder')">执行新增</n-button>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 3. 调试：Payload 快照 -->
      <n-grid :cols="2" :x-gap="12">
        <n-gi>
          <n-card title="1. 后端接口载荷 (Back-end Payload)" embedded :bordered="false">
            <n-code :code="debugPayload" language="json" word-wrap />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card title="2. 底层 Emby API 预览 (Emby Call Preview)" embedded :bordered="false">
            <n-code :code="embyCallPreview" language="bash" word-wrap />
          </n-card>
        </n-gi>
      </n-grid>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { 
  useMessage, NSpace, NH2, NText, NCard, NP, NButton, NGrid, NGi, 
  NCode, NSwitch, NForm, NFormItem, NSelect, NInput 
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const loading = ref(false)
const lastEndpoint = ref('mapper')

const common = reactive({
  lib_names: ['电影', '动漫'],
  dry_run: true
})

const forms = reactive({
  map: { old: '', new_name: '', new_id: '' },
  remove: { tag: '' },
  add: { name: '', id: '' }
})

const debugPayload = computed(() => {
  let body: any = { ...common }
  if (lastEndpoint.value === 'mapper') {
    body.genre_mappings = [forms.map]
  } else if (lastEndpoint.value === 'remover') {
    body.genres_to_remove = forms.remove.tag ? [forms.remove.tag] : []
  } else if (lastEndpoint.value === 'genre_adder') {
    body.genre_to_add_name = forms.add.name
    body.genre_to_add_id = forms.add.id || null
  }
  return JSON.stringify({ endpoint: `/api/toolkit/${lastEndpoint.value}`, body }, null, 2)
})

const embyCallPreview = computed(() => {
  return `# Emby 底层控制代码模拟 (Code Reference):\nPOST /emby/Items/{ItemId}\nBody: {\n  "Genres": ["${lastEndpoint.value === 'remover' ? '...' : (forms.map.new_name || forms.add.name || '...')}"],\n  "GenreItems": [...]\n}`
})

const handleAction = async (endpoint: string) => {
  lastEndpoint.value = endpoint
  if (common.lib_names.length === 0) {
    message.warning('请选择媒体库')
    return
  }
  
  const payload: any = { ...common }
  if (endpoint === 'mapper') payload.genre_mappings = [forms.map]
  if (endpoint === 'remover') payload.genres_to_remove = forms.remove.tag ? [forms.remove.tag] : []
  if (endpoint === 'genre_adder') {
    payload.genre_to_add_name = forms.add.name
    payload.genre_to_add_id = forms.add.id || null
  }

  loading.value = true
  try {
    const res = await axios.post(`/api/toolkit/${endpoint}`, payload)
    message.success(`任务完成: ${res.data.message} (处理数: ${res.data.processed_count})`)
  } catch (e) { message.error('接口请求失败') }
  finally { loading.value = false }
}
</script>

<style scoped>
.toolkit-container { max-width: 1200px; margin: 0 auto; }
</style>