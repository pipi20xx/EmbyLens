<template>
  <div class="settings-container">
    <n-scrollbar style="max-height: calc(100vh - 64px)">
      <div class="settings-content">
        <n-space vertical size="large">
          <div class="page-header">
            <n-h2 prefix="bar" align-text><n-text type="primary">系统集成配置</n-text></n-h2>
            <n-text depth="3">统一管理您的 Emby 核心凭据与第三方集成密钥。</n-text>
          </div>

          <!-- 1. Emby 核心连接 -->
          <n-card title="Emby 服务端连接" size="small">
            <template #header-extra>
              <n-tag type="primary" round quaternary size="small">Emby Core</n-tag>
            </template>
            <n-form label-placement="top" :model="serverForm" size="medium">
              <n-grid :cols="2" :x-gap="24">
                <n-form-item-gi label="服务器地址 (IP/URL)">
                  <n-input v-model:value="serverForm.url" placeholder="http://192.168.50.12:8096" />
                </n-form-item-gi>
                <n-form-item-gi label="管理级 API Key">
                  <n-input v-model:value="serverForm.api_key" type="password" show-password-on="mousedown" />
                </n-form-item-gi>
                <n-form-item-gi label="用户 ID (User ID)">
                  <n-input v-model:value="serverForm.user_id" placeholder="例如: 50da1234567890..." />
                </n-form-item-gi>
                <n-form-item-gi label="服务器别名">
                  <n-input v-model:value="serverForm.name" placeholder="默认服务器" />
                </n-form-item-gi>
              </n-grid>
            </n-form>
          </n-card>

          <!-- 2. 第三方 API 集成 -->
          <n-card title="第三方数据源集成" size="small">
            <template #header-extra>
              <n-tag type="info" round quaternary size="small">External API</n-tag>
            </template>
            <n-form label-placement="top" size="medium">
              <n-grid :cols="1">
                <n-form-item label="TMDB API Key (v3 auth)">
                  <n-input v-model:value="serverForm.tmdb_api_key" type="password" show-password-on="mousedown" placeholder="用于获取高清剧照、演员信息及精准元数据匹配" />
                </n-form-item>
              </n-grid>
            </n-form>
          </n-card>

          <!-- 3. 操作按钮区 -->
          <n-card :bordered="false" content-style="padding: 0">
            <n-space justify="end">
              <n-button secondary @click="handleTest" :loading="testing">测试 Emby 连通性</n-button>
              <n-button type="primary" @click="handleSave" :loading="saving">保存所有配置</n-button>
            </n-space>
          </n-card>

          <!-- 4. 调试：参数实时快照 -->
          <n-card title="调试：当前配置对象 (Full Object Snapshot)" embedded :bordered="false">
            <template #header-extra>
              <n-button quaternary size="tiny" @click="copyConfig">复制 JSON</n-button>
            </template>
            <div class="debug-code-wrapper">
              <n-code :code="JSON.stringify(serverForm, null, 2)" language="json" word-wrap />
            </div>
          </n-card>

          <n-alert title="配置说明" type="info" bordered>
            保存配置后，系统会自动尝试使用您的 API Key 进行一次全库元数据快照同步。TMDB Key 选填，但若缺失则部分高级匹配功能将无法使用。
          </n-alert>
        </n-space>
      </div>
    </n-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { 
  useMessage, NScrollbar, NSpace, NH2, NText, NCard, NTag, NIcon, 
  NForm, NGrid, NFormItemGi, NInput, NCollapseTransition, NInputNumber, 
  NSelect, NThing, NSwitch, NDivider, NRadioGroup, NRadio, NCode, NAlert,
  NButton
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const testing = ref(false)
const saving = ref(false)

const serverForm = reactive({
  name: '默认服务器',
  url: '',
  api_key: '',
  user_id: '',
  tmdb_api_key: ''
})

const fetchCurrent = async () => {
  try {
    const res = await axios.get('/api/server/current')
    if (res.data) {
      Object.assign(serverForm, res.data)
    }
  } catch (e) {}
}

onMounted(fetchCurrent)

const handleTest = async () => {
  if (!serverForm.url || !serverForm.api_key) {
    message.warning('请先填写 URL 和 API Key')
    return
  }
  testing.value = true
  try {
    await axios.post('/api/server/test', {
      url: serverForm.url,
      api_key: serverForm.api_key
    })
    message.success('Emby 连接测试成功')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '连接失败')
  } finally {
    testing.value = false
  }
}

const handleSave = async () => {
  if (!serverForm.url || !serverForm.api_key) {
    message.warning('服务器地址和 API Key 是必填项')
    return
  }
  saving.value = true
  try {
    const res = await axios.post('/api/server/save', serverForm)
    if (res.data) {
      // 关键：将后端返回的最新对象（包含数据库 ID）同步回表单
      Object.assign(serverForm, res.data)
    }
    message.success('全量配置已保存并应用')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const copyConfig = () => {
  navigator.clipboard.writeText(JSON.stringify(serverForm, null, 2))
  message.info('配置快照已复制')
}
</script>

<style scoped>
.settings-container { height: 100%; }
.settings-content { max-width: 1000px; margin: 0 auto; padding-bottom: 40px; }
.debug-code-wrapper { background-color: rgba(0, 0, 0, 0.3); padding: 12px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05); }
</style>