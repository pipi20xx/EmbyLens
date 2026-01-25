<template>
  <div class="settings-container">
    <n-scrollbar style="max-height: calc(100vh - 4rem)">
      <div class="settings-content">
        <n-space vertical size="large">
          <div class="page-header">
            <n-h2 prefix="bar" align-text><n-text type="primary">系统集成配置</n-text></n-h2>
            <n-text depth="3">统一管理您的 Emby 核心凭据与第三方扩展 API 密钥。</n-text>
          </div>

          <!-- 1. Emby 服务端管理 -->
          <n-card title="Emby 服务端管理" size="small" segmented>
            <template #header-extra>
              <n-button type="primary" size="small" @click="openAddModal">
                <template #icon><n-icon><AddIcon /></n-icon></template>
                添加新服务器
              </n-button>
            </template>
            
            <n-table :single-line="false" size="small">
              <thead>
                <tr>
                  <th>名称</th>
                  <th>服务器地址</th>
                  <th>状态</th>
                  <th style="width: 200px">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in servers" :key="s.id" :class="{ 'active-row': s.id === activeServerId }">
                  <td><strong>{{ s.name }}</strong></td>
                  <td><n-text depth="3">{{ s.url }}</n-text></td>
                  <td>
                    <n-tag v-if="s.id === activeServerId" type="success" size="small" round edge>当前激活</n-tag>
                    <n-tag v-else depth="3" size="small" round>闲置</n-tag>
                  </td>
                  <td>
                    <n-space>
                      <n-button size="tiny" secondary @click="openEditModal(s)">配置</n-button>
                      <n-button v-if="s.id !== activeServerId" size="tiny" type="primary" secondary @click="handleActivate(s.id)">激活</n-button>
                      <n-popconfirm @positive-click="handleDelete(s.id)" title="确定要删除此服务器配置吗？">
                        <template #trigger>
                          <n-button size="tiny" type="error" quaternary>删除</n-button>
                        </template>
                      </n-popconfirm>
                    </n-space>
                  </td>
                </tr>
                <tr v-if="servers.length === 0">
                  <td colspan="4" style="text-align: center; padding: 30px">
                    <n-empty description="暂无服务器配置，请添加您的第一个 Emby" />
                  </td>
                </tr>
              </tbody>
            </n-table>
          </n-card>

          <!-- 2. 全局 API 服务集成 -->
          <n-card title="第三方 API 全局集成" size="small" status="info" segmented>
            <template #header-extra>
              <n-icon size="20" color="var(--primary-color)"><ApiIcon /></n-icon>
            </template>
            <n-form label-placement="left" label-width="10rem" size="medium">
              <n-form-item label="TMDB API Key">
                <n-input v-model:value="globalConfig.tmdb_api_key" type="password" show-password-on="mousedown" placeholder="The Movie Database V3 Key" />
              </n-form-item>
              <n-form-item label="Bangumi API Token">
                <n-input v-model:value="globalConfig.bangumi_api_token" type="password" show-password-on="mousedown" placeholder="Bangumi Access Token (Bearer)" />
              </n-form-item>
            </n-form>
            <template #action>
              <n-space justify="end">
                <n-button type="primary" @click="handleSaveGlobal" :loading="savingGlobal">保存全局 API 配置</n-button>
              </n-space>
            </template>
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
                    </n-space>
                  </template>
                  <n-switch v-model:value="globalConfig.proxy.enabled" />
                </n-form-item-gi>
                <n-form-item-gi span="2 m:1">
                  <template #label>
                    <n-space align="center" :size="4">
                      <span>排除 Emby 服务器</span>
                    </n-space>
                  </template>
                  <n-switch v-model:value="globalConfig.proxy.exclude_emby" />
                </n-form-item-gi>
                <n-form-item-gi span="2" label="代理服务器地址 (Proxy URL)">
                  <n-input v-model:value="globalConfig.proxy.url" placeholder="例如: http://127.0.0.1:7890" :disabled="!globalConfig.proxy.enabled" />
                </n-form-item-gi>
              </n-grid>
            </n-form>
            <template #action>
              <n-space justify="end">
                <n-button type="primary" @click="handleSaveGlobal" :loading="savingGlobal">保存代理配置</n-button>
              </n-space>
            </template>
          </n-card>

          <!-- 4. 调试：全局配置快照 -->
          <n-card title="调试：全局配置快照" embedded :bordered="false">
            <template #header-extra>
              <n-button quaternary size="tiny" @click="copyConfig">复制 JSON</n-button>
            </template>
            <div class="debug-code-wrapper">
              <n-code :code="JSON.stringify(globalConfig, null, 2)" language="json" word-wrap />
            </div>
          </n-card>
        </n-space>
      </div>
    </n-scrollbar>

    <!-- 抽离出的服务器配置弹窗 -->
    <EmbyServerModal 
      v-model:show="showServerModal" 
      :server-data="editingServer" 
      @on-success="fetchCurrent"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { 
  useMessage, NScrollbar, NSpace, NH2, NText, NCard, NTag, NIcon, 
  NForm, NGrid, NFormItemGi, NInput, NSwitch, NCode, 
  NButton, NFormItem, NTable, NEmpty, NPopconfirm
} from 'naive-ui'
import { 
  DnsOutlined as ServerIcon,
  ApiOutlined as ApiIcon,
  LanguageOutlined as ProxyIcon,
  AddOutlined as AddIcon
} from '@vicons/material'
import axios from 'axios'
import { servers, activeServerId, fetchServers, activateServer } from '../store/serverStore'
import { copyElementContent } from '../utils/clipboard'
import EmbyServerModal from '../components/EmbyServerModal.vue'

const message = useMessage()
const savingGlobal = ref(false)
const showServerModal = ref(false)
const editingServer = ref(null)

const globalConfig = reactive({
  tmdb_api_key: '',
  bangumi_api_token: '',
  proxy: {
    enabled: false,
    url: '',
    exclude_emby: true
  }
})

const fetchCurrent = async () => {
  await fetchServers()
  try {
    const res = await axios.get('/api/server/current')
    const data = res.data
    if (data) {
      globalConfig.tmdb_api_key = data.tmdb_api_key || ''
      globalConfig.bangumi_api_token = data.bangumi_api_token || ''
      if (data.proxy) {
        globalConfig.proxy.enabled = !!data.proxy.enabled
        globalConfig.proxy.url = data.proxy.url || ''
        globalConfig.proxy.exclude_emby = data.proxy.exclude_emby !== false
      }
    }
  } catch (e) {
    console.error('Failed to load global config:', e)
  }
}

onMounted(fetchCurrent)

const openAddModal = () => {
  editingServer.value = null
  showServerModal.value = true
}

const openEditModal = (s: any) => {
  editingServer.value = s
  showServerModal.value = true
}

const handleActivate = async (serverId: string) => {
  const success = await activateServer(serverId)
  if (success) {
    message.success('已切换当前激活服务器')
    await fetchCurrent()
  } else {
    message.error('切换失败')
  }
}

const handleDelete = async (serverId: string) => {
  try {
    await axios.delete(`/api/server/${serverId}`)
    message.success('服务器已删除')
    await fetchCurrent()
  } catch (e) {
    message.error('删除失败')
  }
}

const handleSaveGlobal = async () => {
  savingGlobal.value = true
  try {
    await axios.post('/api/server/save', globalConfig)
    message.success('全局配置已保存')
    await fetchCurrent()
  } catch (e: any) {
    message.error('保存失败')
  } finally {
    savingGlobal.value = false
  }
}

const copyConfig = () => {
  // 尝试优先获取 n-code 内部的 pre 标签
  const selector = document.querySelector('.debug-code-wrapper pre') ? '.debug-code-wrapper pre' : '.debug-code-wrapper'
  
  if (copyElementContent(selector)) {
    message.info('配置快照已复制')
  } else {
    message.error('复制失败')
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
.active-row {
  background-color: rgba(var(--primary-color-rgb), 0.1);
}
:deep(.n-h2 .n-text--primary-type) {
  color: var(--primary-color);
}
</style>
