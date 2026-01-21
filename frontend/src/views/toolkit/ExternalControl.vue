<template>
  <div class="control-container">
    <n-scrollbar style="max-height: calc(100vh - 64px)">
      <div class="control-content">
        <n-space vertical size="large">
          <div class="page-header">
            <n-h2 prefix="bar" align-text>
              <n-text type="primary">外部控制体系</n-text>
            </n-h2>
            <n-text depth="3">
              管理 API 认证、安全审计及自动化对接配置。
            </n-text>
          </div>

          <n-tabs type="line" animated>
            <!-- 1. API 密钥 -->
            <n-tab-pane name="api_key" tab="API 密钥">
              <n-card :bordered="false" class="tab-card">
                <n-space vertical size="large">
                  <n-alert title="安全说明" type="info">
                    API Token 用于外部系统（如脚本、第三方应用）通过 /api 接口与本系统交互。请妥善保管，泄露后请立即重新生成。
                  </n-alert>
                  <n-form-item label="当前生效的 Token">
                    <n-input-group>
                      <n-input 
                        v-model:value="config.api_token" 
                        type="password" 
                        show-password-on="mousedown" 
                        placeholder="尚未设置 Token"
                        readonly
                      />
                      <n-button type="primary" @click="copyToken" :disabled="!config.api_token">复制</n-button>
                      <n-button secondary @click="generateNewToken">重新生成</n-button>
                    </n-input-group>
                  </n-form-item>
                  <n-text depth="3">
                    注意：更改 Token 后，所有已对接的外部应用需要同步更新。
                  </n-text>
                </n-space>
              </n-card>
            </n-tab-pane>

            <!-- 2. 安全设置 -->
            <n-tab-pane name="settings" tab="安全设置">
              <n-card :bordered="false" class="tab-card">
                <n-grid :cols="2" :x-gap="24">
                  <n-gi>
                    <n-card title="访问控制" size="small" embedded>
                      <n-space vertical>
                        <div class="setting-item">
                          <n-thing title="强制身份认证" description="开启后，所有外部 API 请求必须携带有效的 Bearer Token" />
                          <n-switch v-model:value="config.auth_enabled" @update:value="saveSettings" />
                        </div>
                        <n-divider />
                        <div class="setting-item">
                          <n-thing title="本地请求豁免" description="允许来自 127.0.0.1 的请求跳过 Token 校验" />
                          <n-switch :value="true" disabled />
                        </div>
                      </n-space>
                    </n-card>
                  </n-gi>
                  <n-gi>
                    <n-card title="审计策略" size="small" embedded>
                      <n-space vertical>
                        <div class="setting-item">
                          <n-thing title="开启全局审计" description="记录所有 API 请求的方法、路径、状态码及耗时" />
                          <n-switch v-model:value="config.audit_enabled" @update:value="saveSettings" />
                        </div>
                        <n-divider />
                        <div class="setting-item">
                          <n-thing title="Payload 捕获" description="自动脱敏并存储 POST/PUT 请求的 Body 内容" />
                          <n-switch :value="config.audit_enabled" disabled />
                        </div>
                      </n-space>
                    </n-card>
                  </n-gi>
                </n-grid>
              </n-card>
            </n-tab-pane>

            <!-- 3. 访问日志 -->
            <n-tab-pane name="logs" tab="访问日志">
              <n-card :bordered="false" class="tab-card">
                <n-data-table
                  remote
                  ref="table"
                  :columns="columns"
                  :data="auditLogs"
                  :loading="loadingLogs"
                  :pagination="pagination"
                  :row-key="row => row.id"
                  @update:page="handlePageChange"
                  @update:page-size="handlePageSizeChange"
                  size="medium"
                  :single-line="false"
                />
              </n-card>
            </n-tab-pane>

            <!-- 4. API 文档 -->
            <n-tab-pane name="docs" tab="API 文档">
              <div class="docs-wrapper">
                <iframe 
                  :key="`${config.api_token}`"
                  :src="`/api/system/docs?token=${config.api_token}`" 
                  frameborder="0" 
                  class="docs-iframe"
                ></iframe>
              </div>
            </n-tab-pane>
          </n-tabs>
        </n-space>
      </div>
    </n-scrollbar>

    <!-- Log Detail Modal -->
    <n-modal v-model:show="showLogDetail" preset="card" title="请求详情 (Payload)" style="width: 800px">
      <div class="detail-wrapper">
        <n-code :code="currentPayload" language="json" word-wrap />
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import { 
  useMessage, NScrollbar, NSpace, NH2, NText, NTabs, NTabPane, NCard, NAlert,
  NFormItem, NInput, NInputGroup, NButton, NGrid, NGi, NThing, NSwitch, NDivider,
  NDataTable, NTag, NCode, NModal
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const loadingLogs = ref(false)
const auditLogs = ref([])
const showLogDetail = ref(false)
const currentPayload = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 15,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [15, 30, 50],
  prefix: (info: any) => h('span', { style: 'font-size: 12px; opacity: 0.6;' }, `共 ${info.itemCount} 条记录`)
})

const columns = [
  {
    title: '时间',
    key: 'timestamp',
    render: (row: any) => new Date(row.timestamp).toLocaleString()
  },
  {
    title: '方法',
    key: 'method',
    render: (row: any) => h(NTag, { type: row.method === 'GET' ? 'success' : 'info', size: 'small' }, { default: () => row.method })
  },
  {
    title: '路径',
    key: 'path',
    ellipsis: true
  },
  {
    title: '状态',
    key: 'status_code',
    render: (row: any) => h(NTag, { type: row.status_code < 400 ? 'success' : 'error', size: 'small' }, { default: () => row.status_code })
  },
  {
    title: '来源 IP',
    key: 'client_ip'
  },
  {
    title: '耗时',
    key: 'process_time',
    render: (row: any) => `${row.process_time.toFixed(1)}ms`
  },
  {
    title: '详情',
    key: 'actions',
    render: (row: any) => {
      return h(NButton, {
        size: 'tiny',
        secondary: true,
        disabled: !row.payload,
        onClick: () => {
          try {
            currentPayload.value = JSON.stringify(JSON.parse(row.payload), null, 2)
          } catch {
            currentPayload.value = row.payload || ''
          }
          showLogDetail.value = true
        }
      }, { default: () => '详情' })
    }
  }
]

const config = reactive({
  api_token: '',
  auth_enabled: false,
  audit_enabled: true
})

const loadConfig = async () => {
  try {
    const res = await axios.get('/api/system/config')
    config.api_token = res.data.api_token || ''
    config.auth_enabled = res.data.ui_auth_enabled === 'true' || res.data.ui_auth_enabled === true
    config.audit_enabled = res.data.audit_enabled !== 'false' && res.data.audit_enabled !== false
  } catch (err) {
    message.error('加载配置失败')
  }
}

const saveSettings = async () => {
  try {
    await axios.post('/api/system/config', {
      configs: [
        { key: 'ui_auth_enabled', value: String(config.auth_enabled) },
        { key: 'audit_enabled', value: String(config.audit_enabled) }
      ]
    })
    message.success('设置已保存')
  } catch (err) {
    message.error('保存设置失败')
  }
}

const generateNewToken = async () => {
  try {
    const res = await axios.post('/api/system/token/generate')
    const newToken = res.data.token
    // 强制触发保存接口
    await axios.post('/api/system/config', {
      configs: [{ key: 'api_token', value: newToken }]
    })
    config.api_token = newToken
    message.success('新 Token 已生成并同步至 config.json')
  } catch (err) {
    message.error('生成 Token 失败')
  }
}

const copyToken = () => {
  navigator.clipboard.writeText(config.api_token)
  message.info('Token 已复制到剪贴板')
}

const fetchLogs = async () => {
  loadingLogs.value = true
  try {
    const res = await axios.get('/api/system/audit/logs', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize
      }
    })
    auditLogs.value = res.data.items
    pagination.itemCount = res.data.total
  } catch (err) {
    message.error('加载审计日志失败')
  } finally {
    loadingLogs.value = false
  }
}

const handlePageChange = (page: number) => {
  pagination.page = page
  fetchLogs()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  fetchLogs()
}

onMounted(() => {
  loadConfig()
  fetchLogs()
})
</script>

<style scoped>
.control-container {
  height: 100%;
  padding: 24px;
}
.control-content {
  max-width: 1200px;
  margin: 0 auto;
}
.tab-card {
  background-color: transparent;
}
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.docs-wrapper {
  height: 800px;
  background-color: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  overflow: hidden;
}
.docs-iframe {
  width: 100%;
  height: 100%;
}
</style>
