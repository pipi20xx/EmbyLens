<template>
  <div class="container-panel">
    <n-data-table
      :columns="columns"
      :data="containers"
      :loading="loading"
      :pagination="{ pageSize: 15 }"
    />

    <!-- 日志弹窗 -->
    <n-modal v-model:show="showLogsModal" preset="card" title="查看日志" style="width: 80vw">
      <pre class="logs-container">{{ containerLogs }}</pre>
    </n-modal>
    
    <!-- 自定义端口弹窗 -->
    <n-modal v-model:show="showCustomPortModal" preset="card" title="设置访问端口" style="width: 400px">
      <n-space vertical>
        <n-text depth="3">对于 Host 模式或未识别到的端口，在此设置手动跳转端口。</n-text>
        <n-form-item label="自定义访问端口">
          <n-input v-model:value="customPortForm.port" placeholder="例如: 8096" />
        </n-form-item>
        <n-space justify="end">
          <n-button @click="showCustomPortModal = false">取消</n-button>
          <n-button type="primary" @click="saveCustomPort">保存</n-button>
        </n-space>
      </n-space>
    </n-modal>

    <!-- 终端弹窗 -->
    <terminal-modal
      v-model:show="showTerminalModal"
      :host-id="hostId || ''"
      :container-id="currentContainer.id"
      :container-name="currentContainer.name"
      :command="currentContainer.shell"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, h, reactive } from 'vue'
import { NDataTable, NTag, NButton, NSpace, NIcon, NModal, NText, NFormItem, NInput, useMessage, useDialog, NDropdown, NRadioGroup, NRadioButton } from 'naive-ui'
import { 
  EditOutlined as EditIcon,
  PlayCircleOutlined as StartIcon,
  StopCircleOutlined as StopIcon,
  RefreshOutlined as RecreateIcon,
  DeleteOutlined as DeleteIcon,
  TerminalOutlined as LogIcon,
  CodeOutlined as TerminalIcon
} from '@vicons/material'
import axios from 'axios'
import type { DataTableColumns } from 'naive-ui'
import TerminalModal from './TerminalModal.vue'

const props = defineProps<{
  hostId: string | null
  hosts: any[]
}>()

const message = useMessage()
const dialog = useDialog()
const containers = ref([])
const loading = ref(false)
const loadingActions = ref<Record<string, boolean>>({})
const containerSettings = ref<Record<string, any>>({})
const containerLogs = ref('')
const showLogsModal = ref(false)
const showCustomPortModal = ref(false)
const showTerminalModal = ref(false)
const currentContainer = ref({ id: '', name: '', shell: '/bin/bash' })
const customPortForm = ref({ name: '', port: '' })

// 状态本地化
const statusMap: Record<string, string> = {
  'running': '运行中',
  'exited': '已停止',
  'restarting': '重启中',
  'paused': '已暂停',
  'created': '已创建',
  'removing': '移除中',
  'dead': '已失效'
}

const fetchContainers = async () => {
  if (!props.hostId) return
  loading.value = true
  try {
    const res = await axios.get(`/api/docker/${props.hostId}/containers`)
    containers.value = res.data
    const settingsRes = await axios.get('/api/docker/container-settings')
    containerSettings.value = settingsRes.data
  } finally {
    loading.value = false
  }
}

watch(() => props.hostId, fetchContainers, { immediate: true })

const handleAction = async (id: string, action: string) => {
  loadingActions.value[id] = true
  try {
    await axios.post(`/api/docker/${props.hostId}/containers/${id}/action`, { action })
    message.success('指令已发送')
    setTimeout(fetchContainers, 2000)
  } catch (e) {
    message.error('操作失败')
  } finally {
    loadingActions.value[id] = false
  }
}

const handleDelete = (row: any) => {
  dialog.error({
    title: '确认删除容器',
    content: `确定要彻底删除容器 "${row.name}" 吗？此操作不可撤销。`,
    positiveText: '确认删除',
    negativeText: '取消',
    onPositiveClick: () => handleAction(row.id, 'remove')
  })
}

const showLogs = async (id: string, name: string) => {
  const res = await axios.get(`/api/docker/${props.hostId}/containers/${id}/logs?tail=200`)
  containerLogs.value = res.data.logs
  showLogsModal.value = true
}

const openTerminal = (row: any) => {
  if (row.status !== 'running') {
    message.warning('只有运行中的容器可以进入终端')
    return
  }
  
  const selectedShell = ref('/bin/bash')
  const shellOptions = [
    { label: 'bash', value: '/bin/bash' },
    { label: 'sh', value: '/bin/sh' },
    { label: 'ash', value: '/bin/ash' }
  ]

  dialog.info({
    title: '选择终端 Shell',
    content: () => h('div', { style: 'margin-top: 10px' }, [
      h(NRadioGroup, {
        value: selectedShell.value,
        'onUpdate:value': (val: string) => selectedShell.value = val,
        name: 'shell-type'
      }, {
        default: () => shellOptions.map(opt => h(NRadioButton, {
          key: opt.value,
          value: opt.value,
          label: opt.label
        }))
      })
    ]),
    positiveText: '进入终端',
    negativeText: '取消',
    onPositiveClick: () => {
      currentContainer.value = { 
        id: row.full_id || row.id, 
        name: row.name, 
        shell: selectedShell.value 
      }
      showTerminalModal.value = true
    }
  })
}

const openCustomPortModal = (name: string) => {
  customPortForm.value = { name, port: containerSettings.value[name]?.custom_port || '' }
  showCustomPortModal.value = true
}

const saveCustomPort = async () => {
  await axios.post(`/api/docker/container-settings/${customPortForm.value.name}`, { custom_port: customPortForm.value.port })
  message.success('设置已保存')
  showCustomPortModal.value = false
  fetchContainers()
}

const columns: DataTableColumns<any> = [
  { title: '名称', key: 'name', width: 150 },
  { title: '状态', key: 'status', width: 100, render(row) {
      const text = statusMap[row.status] || row.status
      return h(NTag, { type: row.status === 'running' ? 'success' : 'error', size: 'small', round: true }, { default: () => text })
    }
  },
  { title: '端口映射', key: 'ports', render(row) {
      const tags: any[] = []
      const hostsList = Array.isArray(props.hosts) ? props.hosts : []
      const currentHost = hostsList.find(h => h && h.id === props.hostId)
      const targetIp = (!currentHost?.ssh_host || currentHost.ssh_host === '127.0.0.1') ? window.location.hostname : currentHost.ssh_host
      if (row.ports) {
        for (const [containerPort, bindings] of Object.entries(row.ports)) {
          if (bindings && Array.isArray(bindings)) {
            bindings.forEach((b: any) => {
              tags.push(h(NButton, { size: 'tiny', type: 'primary', quaternary: true, onClick: () => window.open(`http://${targetIp}:${b.HostPort}`, '_blank') }, { default: () => `${b.HostPort}->${containerPort}` }))
            })
          }
        }
      }
      const customPort = containerSettings.value[row.name]?.custom_port
      if (customPort) {
        tags.push(h(NButton, { size: 'tiny', type: 'warning', secondary: true, onClick: () => window.open(`http://${targetIp}:${customPort}`, '_blank') }, { default: () => `${customPort} (自定)` }))
      }
      tags.push(h(NButton, { size: 'tiny', circle: true, quaternary: true, onClick: () => openCustomPortModal(row.name) }, { default: () => h(NIcon, null, { default: () => h(EditIcon) }) }))
      return h(NSpace, { size: [4, 4], align: 'center' }, { default: () => tags })
    }
  },
  { title: '镜像', key: 'image', ellipsis: true },
  { title: '操作', key: 'actions', width: 380, render(row) {
      const isRunning = row.status === 'running'
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { size: 'tiny', type: isRunning ? 'error' : 'primary', secondary: true, loading: loadingActions.value[row.id], onClick: () => handleAction(row.id, isRunning ? 'stop' : 'start') }, { 
            icon: () => h(NIcon, null, { default: () => h(isRunning ? StopIcon : StartIcon) }),
            default: () => isRunning ? '停止' : '启动' 
          }),
          h(NButton, { size: 'tiny', type: 'warning', secondary: true, loading: loadingActions.value[row.id], onClick: () => handleAction(row.id, 'recreate') }, { 
            icon: () => h(NIcon, null, { default: () => h(RecreateIcon) }),
            default: () => '更新' 
          }),
          h(NButton, { size: 'tiny', type: 'error', secondary: true, loading: loadingActions.value[row.id], onClick: () => handleDelete(row) }, { 
            icon: () => h(NIcon, null, { default: () => h(DeleteIcon) }),
            default: () => '删除' 
          }),
          h(NButton, { size: 'tiny', type: 'info', secondary: true, onClick: () => showLogs(row.id, row.name) }, { 
            icon: () => h(NIcon, null, { default: () => h(LogIcon) }),
            default: () => '日志' 
          }),
          h(NButton, { size: 'tiny', type: 'info', secondary: true, onClick: () => openTerminal(row) }, { 
            icon: () => h(NIcon, null, { default: () => h(TerminalIcon) }),
            default: () => '终端' 
          })
        ]
      })
    }
  }
]

defineExpose({ refresh: fetchContainers })
</script>

<style scoped>
.logs-container { 
  background-color: rgba(0, 0, 0, 0.3); 
  color: var(--text-color); 
  padding: 12px; 
  max-height: 500px; 
  overflow: auto; 
  font-size: 12px; 
  font-family: 'Fira Code', 'JetBrains Mono', monospace; 
  border-radius: 4px;
}
</style>
