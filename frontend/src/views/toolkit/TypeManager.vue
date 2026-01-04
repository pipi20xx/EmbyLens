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
              :options="libOptions"
              placeholder="请选择要操作的媒体库" 
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

      <!-- 2. 原子工具卡片 -->
      <n-grid :cols="3" :x-gap="12">
        <n-gi>
          <n-card title="类型映射 (Mapper)" size="small" status="primary">
            <n-space vertical>
              <n-input v-model:value="forms.map.old" placeholder="旧类型名" size="small" />
              <n-input v-model:value="forms.map.new_name" placeholder="新类型名" size="small" />
              <n-input v-model:value="forms.map.new_id" placeholder="新 ID (可选)" size="small" />
              <n-button block type="primary" secondary @click="runMapper" :loading="loading">执行映射</n-button>
            </n-space>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="类型移除 (Remover)" size="small" status="error">
            <n-space vertical>
              <n-input v-model:value="forms.remove.tag" placeholder="要移除的标签名" size="small" />
              <n-p depth="3" style="font-size: 12px">留空则清空该库所有类型。</n-p>
              <n-button block type="error" ghost @click="runRemover" :loading="loading">执行移除</n-button>
            </n-space>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="类型新增 (Adder)" size="small" status="success">
            <n-space vertical>
              <n-input v-model:value="forms.add.name" placeholder="新增类型名" size="small" />
              <n-input v-model:value="forms.add.id" placeholder="新增 ID (可选)" size="small" />
              <n-button block type="success" secondary @click="runAdder" :loading="loading">执行新增</n-button>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 3. 调试：Payload 快照 -->
      <n-grid :cols="2" :x-gap="12">
        <n-gi>
          <n-card title="1. 后端接口载荷" embedded :bordered="false">
            <n-code :code="debugPayload" language="json" word-wrap />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card title="2. 底部提示" embedded :bordered="false">
            <n-alert type="info">点击按钮后请立即打开左下角终端查看执行详情。</n-alert>
          </n-card>
        </n-gi>
      </n-grid>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { 
  useMessage, NSpace, NH2, NText, NCard, NP, NButton, NGrid, NGi, 
  NCode, NSwitch, NForm, NFormItem, NSelect, NInput, NAlert 
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const loading = ref(false)
const libOptions = ref([])
const currentEndpoint = ref('')

const common = reactive({
  lib_names: JSON.parse(localStorage.getItem('embylens_toolkit_common') || '{"lib_names":[]}').lib_names,
  dry_run: true
})

watch(common, (val) => {
  localStorage.setItem('embylens_toolkit_common', JSON.stringify(val))
}, { deep: true })

const fetchLibraries = async () => {
  try {
    const res = await axios.get('/api/server/libraries')
    libOptions.value = res.data
  } catch (e) {}
}

onMounted(fetchLibraries)

const forms = reactive({
  map: { old: '', new_name: '', new_id: '' },
  remove: { tag: '' },
  add: { name: '', id: '' }
})

const debugPayload = computed(() => {
  return JSON.stringify({
    common: common,
    forms: forms,
    current_action: currentEndpoint.value
  }, null, 2)
})

// --- 显式的按钮处理器，确保请求必达 ---

const runMapper = async () => {
  if (common.lib_names.length === 0) { message.warning('请选择媒体库'); return; }
  if (!forms.map.old || !forms.map.new_name) { message.warning('请填写映射规则'); return; }
  
  currentEndpoint.value = '/api/toolkit/mapper'
  loading.value = true
  try {
    const payload = {
      ...common,
      genre_mappings: [{
        old: forms.map.old,
        new_name: forms.map.new_name,
        new_id: forms.map.new_id || "0"
      }]
    }
    console.log('Sending Mapper Request:', payload)
    const res = await axios.post('/api/toolkit/mapper', payload)
    message.success(`映射完成: 处理项目数 ${res.data.processed_count}`)
  } catch (e) {
    message.error('映射请求发送失败')
  } finally {
    loading.value = false
  }
}

const runRemover = async () => {
  if (common.lib_names.length === 0) { message.warning('请选择媒体库'); return; }
  currentEndpoint.value = '/api/toolkit/remover'
  loading.value = true
  try {
    const payload = {
      ...common,
      genres_to_remove: forms.remove.tag ? [forms.remove.tag] : []
    }
    await axios.post('/api/toolkit/remover', payload)
    message.success('移除请求已发出，请查看日志')
  } catch (e) { message.error('请求失败') }
  finally { loading.value = false }
}

const runAdder = async () => {
  if (common.lib_names.length === 0) { message.warning('请选择媒体库'); return; }
  currentEndpoint.value = '/api/toolkit/genre_adder'
  loading.value = true
  try {
    const payload = {
      ...common,
      genre_to_add_name: forms.add.name,
      genre_to_add_id: forms.add.id || null
    }
    await axios.post('/api/toolkit/genre_adder', payload)
    message.success('新增请求已发出，请查看日志')
  } catch (e) { message.error('请求失败') }
  finally { loading.value = false }
}
</script>

<style scoped>
.toolkit-container { max-width: 1200px; margin: 0 auto; }
</style>
