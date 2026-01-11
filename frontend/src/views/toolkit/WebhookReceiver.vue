<template>
  <div class="toolkit-container">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">Webhook 情报中心</n-text></n-h2>
        <n-text depth="3">实时捕获、持久化存储 Emby 服务器发出的所有通知事件。为您提供最原始的 JSON 审计链路。</n-text>
        <n-alert type="warning" size="small" :bordered="false" style="margin-top: 12px">
          <b>声明：</b>本页面仅用于接收测试、展示 Emby 的原始推送数据，不具备任何后台自动化联动功能。如需自动化打标签，请前往“自动标签助手”。
        </n-alert>
      </div>

      <!-- 1. 接收地址提示 -->
      <n-alert title="Webhook 接收地址" type="info" bordered>
        请在 Emby 管理后台 -> Webhook 中添加以下地址：
        <code class="code-url">http://{{ currentHost }}:6565/api/webhook/receive</code>
      </n-alert>

      <!-- 2. 事件列表 -->
      <n-card title="事件捕获日志 (最近 50 条)" size="small">
        <template #header-extra>
          <n-space>
            <n-button quaternary circle size="small" type="error" @click="handleClear" title="清空全部日志">
              <template #icon><n-icon><ClearIcon /></n-icon></template>
            </n-button>
            <n-button quaternary circle size="small" @click="fetchLogs" :loading="loading" title="刷新列表">
              <template #icon><n-icon><RefreshIcon /></n-icon></template>
            </n-button>
          </n-space>
        </template>

        <n-data-table
          :columns="columns"
          :data="logs"
          :pagination="{ pageSize: 10 }"
          size="small"
          :bordered="false"
        />
      </n-card>

      <!-- 3. JSON 探针弹窗 -->
      <n-modal v-model:show="showModal" preset="card" style="width: 850px" title="Webhook 原始 JSON 载荷">
        <div class="json-code-wrapper">
          <n-code :code="JSON.stringify(selectedPayload, null, 2)" language="json" word-wrap />
        </div>
        <template #footer>
          <n-button block type="primary" secondary @click="copyPayload">
            复制原始载荷 (Payload)
          </n-button>
        </template>
      </n-modal>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { 
  useMessage, useDialog, NSpace, NH2, NText, NCard, NAlert, NDataTable, NButton, 
  NIcon, NTag, NModal, NCode 
} from 'naive-ui'
import { 
  RefreshRound as RefreshIcon,
  TerminalOutlined as CodeIcon,
  DeleteSweepRound as ClearIcon 
} from '@vicons/material'
import axios from 'axios'

const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const logs = ref([])
const showModal = ref(false)
const selectedPayload = ref({})
const currentHost = window.location.hostname

const fetchLogs = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/webhook/list')
    logs.value = res.data
  } catch (e) {
    message.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

const handleClear = () => {
  dialog.warning({
    title: '确认清空日志',
    content: '确定要物理删除所有的 Webhook 历史记录吗？此操作无法撤销。',
    positiveText: '确定清空',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await axios.delete('/api/webhook/clear')
        message.success('日志已全部物理清理')
        fetchLogs()
      } catch (e) {
        message.error('清理失败')
      }
    }
  })
}

const showJson = (payload: any) => {
  selectedPayload.value = payload
  showModal.value = true
}

const copyPayload = () => {
  const text = JSON.stringify(selectedPayload.value, null, 2)
  const textArea = document.createElement("textarea")
  textArea.value = text; document.body.appendChild(textArea); textArea.select()
  document.execCommand('copy'); document.body.removeChild(textArea)
  message.success('已复制到剪贴板')
}

const columns = [
  {
    title: '捕获时间',
    key: 'created_at',
    render(row: any) {
      return new Date(row.created_at).toLocaleString()
    }
  },
  {
    title: '事件类型',
    key: 'event_type',
    render(row: any) {
      return h(NTag, { type: 'primary', quaternary: true, size: 'small' }, { default: () => row.event_type })
    }
  },
  {
    title: '来源 IP',
    key: 'source_ip'
  },
  {
    title: '操作',
    key: 'actions',
    render(row: any) {
      return h(
        NButton,
        {
          size: 'tiny',
          secondary: true,
          type: 'primary',
          onClick: () => showJson(row.payload)
        },
        { 
          icon: () => h(NIcon, null, { default: () => h(CodeIcon) }),
          default: () => '查看原始 JSON'
        }
      )
    }
  }
]

onMounted(fetchLogs)
</script>

<style scoped>

.toolkit-container { 

  width: 100%; 

}

:deep(.n-h2 .n-text--primary-type) {

  color: var(--primary-color);

}

.code-url {

  margin-left: 8px;

  color: var(--primary-color);

  background: rgba(0, 0, 0, 0.2);

  padding: 2px 6px;

  border-radius: 4px;

}

.json-code-wrapper { 

  background: #000; 

  padding: 16px; 

  border-radius: 8px; 

  max-height: 60vh; 

  overflow-y: auto; 

  border: 1px solid var(--border-color); 

}

</style>
