<template>
  <div class="control-container">
    <div class="control-content">
      <div class="page-header">
        <n-h2 prefix="bar" align-text>
          <n-text type="primary">外部控制体系</n-text>
        </n-h2>
        <n-text depth="3">管理 API 认证、安全审计及自动化对接配置。</n-text>
      </div>

      <n-tabs v-model:value="activeTab" type="line" animated class="control-tabs">
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
              <n-text depth="3">注意：更改 Token 后，所有已对接的外部应用需要同步更新。</n-text>
            </n-space>
          </n-card>
        </n-tab-pane>

        <!-- 2. 安全设置 -->
        <n-tab-pane name="settings" tab="安全设置">
          <n-card :bordered="false" class="tab-card">
            <n-grid x-gap="24" y-gap="24" cols="1 s:1 m:2 l:2" responsive="screen">
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
              ref="docsIframe"
              :key="`${currentThemeType}-${config.api_token}`"
              :src="`/api/system/docs?theme=${currentThemeType}&token=${config.api_token}`" 
              frameborder="0" 
              class="docs-iframe"
              @load="initIframeMonitor"
              scrolling="no"
            ></iframe>
          </div>
        </n-tab-pane>
      </n-tabs>
    </div>

    <!-- Log Detail Modal -->
    <n-modal v-model:show="showLogDetail" preset="card" title="请求详情 (Payload)" style="width: 800px">
      <div class="detail-wrapper">
        <n-code :code="currentPayload" language="json" word-wrap />
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, watch, nextTick } from 'vue'
import { 
  useMessage, NSpace, NH2, NText, NTabs, NTabPane, NCard, NAlert,
  NFormItem, NInput, NInputGroup, NButton, NGrid, NGi, NThing, NSwitch, NDivider,
  NDataTable, NTag, NCode, NModal
} from 'naive-ui'

// 导入提取的逻辑
import { useExternalControl } from './externalControl/hooks/useExternalControl'
import { useTheme } from '../../hooks/useTheme'

const message = useMessage()
const { currentThemeType } = useTheme()

const {
  config, auditLogs, loadingLogs, pagination, showLogDetail, currentPayload, activeTab,
  loadConfig, saveSettings, generateNewToken, copyToken, fetchLogs, handlePageChange, handlePageSizeChange
} = useExternalControl()

const docsIframe = ref<HTMLIFrameElement | null>(null)

// 核心：高度监视器
const initIframeMonitor = () => {
  const iframe = docsIframe.value
  if (!iframe || !iframe.contentWindow) return
  const updateHeight = () => {
    try {
      const doc = iframe.contentWindow?.document
      if (doc) {
        const height = Math.max(doc.body.scrollHeight, doc.documentElement.scrollHeight)
        iframe.style.height = (height + 50) + 'px'
      }
    } catch (e) {
      iframe.style.height = '2000px'
    }
  }
  updateHeight()
  try {
    const observer = new MutationObserver(updateHeight)
    observer.observe(iframe.contentWindow.document.body, { attributes: true, childList: true, subtree: true })
  } catch (e) {
    setInterval(updateHeight, 1000)
  }
}

watch(activeTab, (val) => {
  if (val === 'docs') { nextTick(() => initIframeMonitor()) }
})

const columns = [
  { title: '时间', key: 'timestamp', width: 180, render: (row: any) => new Date(row.timestamp).toLocaleString() },
  { title: '方法', key: 'method', width: 80, render: (row: any) => h(NTag, { type: row.method === 'GET' ? 'success' : 'info', size: 'small' }, { default: () => row.method }) },
  { title: '路径', key: 'path', ellipsis: true },
  { title: '状态', key: 'status_code', width: 80, render: (row: any) => h(NTag, { type: row.status_code < 400 ? 'success' : 'error', size: 'small' }, { default: () => row.status_code }) },
  { title: '来源 IP', key: 'client_ip', width: 130 },
  { title: '耗时', key: 'process_time', width: 100, render: (row: any) => `${row.process_time.toFixed(1)}ms` },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    render: (row: any) => {
      return h(NButton, {
        size: 'tiny', secondary: true, disabled: !row.payload,
        onClick: () => {
          try { currentPayload.value = JSON.stringify(JSON.parse(row.payload), null, 2) } 
          catch { currentPayload.value = row.payload || '' }
          showLogDetail.value = true
        }
      }, { default: () => '详情' })
    }
  }
]

// 注入 pagination 的前缀渲染逻辑
pagination.prefix = (info: any) => h('span', { style: 'font-size: 12px; opacity: 0.6;' }, `共 ${info.itemCount} 条记录`)

onMounted(() => { loadConfig(); fetchLogs() })
</script>

<style scoped>
.control-container {
  padding: 16px;
  width: 100%;
}
@media (min-width: 768px) {
  .control-container { padding: 24px; }
}
.control-content { width: 100%; }
.tab-card { background-color: transparent; padding-top: 16px; }
.setting-item { display: flex; justify-content: space-between; align-items: center; }

.docs-wrapper {
  margin-top: 16px;
  width: 100%;
}

.docs-iframe {
  width: 100%;
  min-height: 800px;
  border: none;
  display: block;
  overflow: hidden;
}

/* 彻底移除 Naive UI 内部的高度和滚动封印 */
:deep(.n-tabs-content) { height: auto !important; }
:deep(.n-tab-pane) { height: auto !important; overflow: visible !important; }
</style>