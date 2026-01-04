<template>
  <div class="settings-container">
    <n-scrollbar style="max-height: calc(100vh - 64px)">
      <div class="settings-content">
        <n-space vertical size="large">
          <div class="page-header">
            <n-h2 prefix="bar" align-text><n-text type="primary">系统集成配置</n-text></n-h2>
            <n-text depth="3">统一管理您的 Emby 核心凭据与第三方扩展 API 密钥。</n-text>
          </div>

          <!-- 1. Emby 核心连接 -->
          <n-card title="Emby 服务端连接" size="small" segmented>
            <template #header-extra>
              <n-icon size="20" color="#bb86fc"><ServerIcon /></n-icon>
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

              <n-divider title-placement="left">账号登录 (用于删除操作)</n-divider>
              <n-grid :cols="3" :x-gap="12">
                <n-form-item-gi label="Emby 用户名">
                  <n-input v-model:value="serverForm.username" placeholder="请输入管理员用户名" />
                </n-form-item-gi>
                <n-form-item-gi label="Emby 密码">
                  <n-input v-model:value="serverForm.password" type="password" show-password-on="mousedown" />
                </n-form-item-gi>
                <n-form-item-gi label="会话令牌 (Session Token)">
                  <n-input v-model:value="serverForm.session_token" disabled placeholder="登录后自动填充" />
                </n-form-item-gi>
              </n-grid>
            </n-form>
          </n-card>

          <!-- 2. 扩展 API 服务集成 (通用化) -->
          <n-card title="第三方 API 服务集成" size="small" status="info" segmented>
            <template #header-extra>
              <n-icon size="20" color="#01b4e4"><ApiIcon /></n-icon>
            </template>
            <n-form label-placement="left" label-width="140" size="medium">
              <n-form-item label="TMDB API Key">
                <n-input v-model:value="serverForm.tmdb_api_key" type="password" show-password-on="mousedown" placeholder="The Movie Database V3 Key" />
              </n-form-item>
              <n-form-item label="未来扩展接口">
                <n-input disabled placeholder="更多第三方服务集成正在开发中..." />
              </n-form-item>
            </n-form>
          </n-card>

          <!-- 3. 操作按钮区 -->
          <n-card :bordered="false" content-style="padding: 0">
            <n-space justify="end">
              <n-button secondary @click="handleTest" :loading="testing">测试 Emby 连通性</n-button>
              <n-button type="info" secondary @click="handleLogin" :loading="loggingIn">登录并获取 Token</n-button>
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
            所有的 API Key 均加密存储于本地 SQLite 数据库中。部分原子工具可能依赖特定第三方接口，请按需填入。
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
  NForm, NGrid, NFormItemGi, NInput, NInputNumber, 
  NSelect, NThing, NSwitch, NDivider, NRadioGroup, NRadio, NCode, NAlert,
  NButton, NFormItem
} from 'naive-ui'
import { 
  DnsOutlined as ServerIcon,
  ApiOutlined as ApiIcon 
} from '@vicons/material'
import axios from 'axios'

const message = useMessage()
const testing = ref(false)
const saving = ref(false)
const loggingIn = ref(false)

const serverForm = reactive({
  name: '默认服务器',
  url: '',
  api_key: '',
  user_id: '',
  tmdb_api_key: '',
  username: '',
  password: '',
  session_token: ''
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
    message.warning('服务器配置不能为空')
    return
  }
  saving.value = true
  try {
    const res = await axios.post('/api/server/save', serverForm)
    if (res.data) {
      Object.assign(serverForm, res.data)
    }
    message.success('配置已成功保存')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleLogin = async () => {
  if (!serverForm.username) {
    message.warning('请输入用户名')
    return
  }
  // 登录前先保存现有配置，确保后端拿到最新的账号密码
  await handleSave()
  
  loggingIn.value = true
  try {
    const res = await axios.post('/api/server/login')
    message.success('登录成功，已获取会话令牌')
    serverForm.session_token = res.data.token
  } catch (e: any) {
    message.error(e.response?.data?.detail || '登录失败')
  } finally {
    loggingIn.value = false
  }
}

const copyConfig = () => {
  const config = JSON.stringify(serverForm, null, 2)
  if (copyToClipboard(config)) {
    message.info('配置快照已成功复制')
  }
}

const copyToClipboard = (text: string) => {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.style.position = "fixed";
  textArea.style.left = "-9999px";
  textArea.style.top = "0";
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  try {
    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);
    return successful;
  } catch (err) {
    document.body.removeChild(textArea);
    return false;
  }
}
</script>

<style scoped>
.settings-container { height: 100%; }
.settings-content { max-width: 1000px; margin: 0 auto; padding-bottom: 40px; }
.debug-code-wrapper { background-color: rgba(0, 0, 0, 0.3); padding: 12px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05); }
</style>
