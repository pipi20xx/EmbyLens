<template>
  <div class="settings-container">
    <n-scrollbar style="max-height: calc(100vh - 4rem)">
      <div class="settings-content">
        <n-space vertical size="large">
          <div class="page-header">
            <n-h2 prefix="bar" align-text><n-text type="primary">系统集成配置</n-text></n-h2>
            <n-text depth="3">统一管理您的 Emby 核心凭据与第三方扩展 API 密钥。</n-text>
          </div>

          <!-- 1. Emby 核心连接 -->
          <n-card title="Emby 服务端连接" size="small" segmented>
            <template #header-extra>
              <n-icon size="20" color="var(--primary-color)"><ServerIcon /></n-icon>
            </template>
            <n-form label-placement="top" :model="serverForm" size="medium">
              <n-grid :cols="2" :x-gap="24" item-responsive responsive="screen">
                <n-form-item-gi span="2 m:1" label="服务器地址 (IP/URL)">
                  <n-input v-model:value="serverForm.url" placeholder="http://192.168.50.12:8096" />
                </n-form-item-gi>
                <n-form-item-gi span="2 m:1" label="管理级 API Key">
                  <n-input v-model:value="serverForm.api_key" type="password" show-password-on="mousedown" />
                </n-form-item-gi>
                <n-form-item-gi span="2 m:1" label="用户 ID (User ID)">
                  <n-input v-model:value="serverForm.user_id" placeholder="例如: 50da1234567890..." />
                </n-form-item-gi>
                <n-form-item-gi span="2 m:1" label="服务器别名">
                  <n-input v-model:value="serverForm.name" placeholder="默认服务器" />
                </n-form-item-gi>
              </n-grid>

              <n-divider title-placement="left">账号登录 (用于删除操作)</n-divider>
              <n-grid :cols="3" :x-gap="12" item-responsive responsive="screen">
                <n-form-item-gi span="3 m:1" label="Emby 用户名">
                  <n-input v-model:value="serverForm.username" placeholder="请输入管理员用户名" />
                </n-form-item-gi>
                <n-form-item-gi span="3 m:1" label="Emby 密码">
                  <n-input v-model:value="serverForm.password" type="password" show-password-on="mousedown" />
                </n-form-item-gi>
                <n-form-item-gi span="3 m:1" label="会话令牌 (Session Token)">
                  <n-input v-model:value="serverForm.session_token" disabled placeholder="登录后自动填充" />
                </n-form-item-gi>
              </n-grid>
            </n-form>
          </n-card>

          <!-- 2. 扩展 API 服务集成 (通用化) -->
          <n-card title="第三方 API 服务集成" size="small" status="info" segmented>
            <template #header-extra>
              <n-icon size="20" color="var(--primary-color)"><ApiIcon /></n-icon>
            </template>
            <n-form label-placement="left" label-width="10rem" size="medium">
              <n-form-item label="TMDB API Key">
                <n-input v-model:value="serverForm.tmdb_api_key" type="password" show-password-on="mousedown" placeholder="The Movie Database V3 Key" />
              </n-form-item>
              <n-form-item label="Bangumi API Token">
                <n-input v-model:value="serverForm.bangumi_api_token" type="password" show-password-on="mousedown" placeholder="Bangumi Access Token (Bearer)" />
              </n-form-item>
              <n-form-item label="未来扩展接口">
                <n-input disabled placeholder="更多第三方服务集成正在开发中..." />
              </n-form-item>
            </n-form>
          </n-card>

          <!-- 3. HTTP 代理配置 -->
          <n-card title="网络代理设置" size="small" segmented>
            <template #header-extra>
              <n-icon size="20" color="var(--primary-color)"><ProxyIcon /></n-icon>
            </template>
            <n-form label-placement="top" size="medium">
              <n-grid :cols="2" :x-gap="24" item-responsive responsive="screen">
                <n-form-item-gi span="2 m:1">
                  <template #label>
                    <n-space align="center" :size="4">
                      <span>启用代理</span>
                      <n-tooltip trigger="hover">
                        <template #trigger>
                          <n-icon size="16" depth="3" style="cursor: help"><info-outlined /></n-icon>
                        </template>
                        开启后，后端发起的外部网络请求将通过代理转发。
                      </n-tooltip>
                    </n-space>
                  </template>
                  <n-switch v-model:value="serverForm.proxy.enabled">
                    <template #checked>已开启代理</template>
                    <template #unchecked>已关闭代理</template>
                  </n-switch>
                </n-form-item-gi>
                <n-form-item-gi span="2 m:1">
                  <template #label>
                    <n-space align="center" :size="4">
                      <span>排除 Emby 服务器</span>
                      <n-tooltip trigger="hover">
                        <template #trigger>
                          <n-icon size="16" depth="3" style="cursor: help"><info-outlined /></n-icon>
                        </template>
                        建议开启。开启后访问本地 Emby 将不经过代理，避免大流量传输导致速度变慢或代理流量浪费。
                      </n-tooltip>
                    </n-space>
                  </template>
                  <n-switch v-model:value="serverForm.proxy.exclude_emby">
                    <template #checked>本地直连 (推荐)</template>
                    <template #unchecked>强制走代理</template>
                  </n-switch>
                </n-form-item-gi>
                <n-form-item-gi span="2" label="代理服务器地址 (Proxy URL)">
                  <n-input v-model:value="serverForm.proxy.url" placeholder="例如: http://127.0.0.1:7890" :disabled="!serverForm.proxy.enabled" />
                  <template #feedback>
                    支持 HTTP、SOCKS5 协议，例如：http://user:pass@1.2.3.4:7890
                  </template>
                </n-form-item-gi>
              </n-grid>
            </n-form>
            
            <n-blockquote style="margin-top: 12px; font-size: 13px">
              <n-text depth="3">
                <strong>代理生效范围：</strong><br/>
                1. <strong>TMDB / Bangumi：</strong> 所有元数据搜索、信息抓取和海报同步。<br/>
                2. <strong>演员实验室：</strong> 外部头像获取和第三方信息检索。<br/>
                3. <strong>系统更新：</strong> 检查新版本和下载外部配置文件。
              </n-text>
            </n-blockquote>

            <n-alert type="info" size="small" style="margin-top: 12px">
              提示：如果您的服务器位于网络受限环境，配置正确的代理是保证元数据识别成功率的关键。
            </n-alert>
          </n-card>

          <!-- 4. 操作按钮区 -->
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
  NButton, NFormItem, NTooltip, NBlockquote
} from 'naive-ui'
import { 
  DnsOutlined as ServerIcon,
  ApiOutlined as ApiIcon,
  LanguageOutlined as ProxyIcon,
  InfoOutlined
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
  bangumi_api_token: '',
  username: '',
  password: '',
  session_token: '',
  proxy: {
    enabled: false,
    url: '',
    exclude_emby: true
  }
})

const fetchCurrent = async () => {
  try {
    const res = await axios.get('/api/server/current')
    const data = res.data
    if (data && typeof data === 'object') {
      serverForm.name = data.name || ''
      serverForm.url = data.url || ''
      serverForm.api_key = data.api_key || ''
      serverForm.user_id = data.user_id || ''
      serverForm.tmdb_api_key = data.tmdb_api_key || ''
      serverForm.bangumi_api_token = data.bangumi_api_token || ''
      serverForm.username = data.username || ''
      serverForm.password = data.password || ''
      serverForm.session_token = data.session_token || ''
      
      if (data.proxy) {
        serverForm.proxy.enabled = !!data.proxy.enabled
        serverForm.proxy.url = data.proxy.url || ''
        serverForm.proxy.exclude_emby = data.proxy.exclude_emby !== false
      }
    }
  } catch (e) {
    console.error('Failed to load server config:', e)
  }
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
.settings-container { 
  height: 100%; 
  width: 100%;
}
.settings-content { 
  width: 100%;
  padding-bottom: 40px; 
}
.debug-code-wrapper { 
  background-color: rgba(0, 0, 0, 0.3); 
  padding: 12px; 
  border-radius: 8px; 
  border: 1px solid var(--border-color); 
}
:deep(.n-h2 .n-text--primary-type) {
  color: var(--primary-color);
}
</style>
