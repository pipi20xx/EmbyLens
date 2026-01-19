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
  </div>
</template>

<script setup lang="ts">
import { ref, watch, h } from 'vue'
import { NDataTable, NTag, NButton, NSpace, NIcon, NModal, NText, NFormItem, NInput, useMessage, useDialog } from 'naive-ui'
import { EditOutlined as EditIcon } from '@vicons/material'
import axios from 'axios'
import type { DataTableColumns } from 'naive-ui'

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
const customPortForm = ref({ name: '', port: '' })

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

const showLogs = async (id: string, name: string) => {
  const res = await axios.get(`/api/docker/${props.hostId}/containers/${id}/logs?tail=200`)
  containerLogs.value = res.data.logs
  showLogsModal.value = true
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
  { title: '状态', key: 'status', width: 80, render(row) {
      return h(NTag, { type: row.status === 'running' ? 'success' : 'error', size: 'small' }, { default: () => row.status })
    }
  },
  { title: '端口映射', key: 'ports', render(row) {
      const tags: any[] = []
      const currentHost = props.hosts.find(h => h.id === props.hostId)
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
  { title: '操作', key: 'actions', width: 200, render(row) {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { size: 'tiny', secondary: true, loading: loadingActions.value[row.id], onClick: () => handleAction(row.id, row.status === 'running' ? 'stop' : 'start') }, { default: () => row.status === 'running' ? '停止' : '启动' }),
          h(NButton, { size: 'tiny', type: 'warning', secondary: true, loading: loadingActions.value[row.id], onClick: () => handleAction(row.id, 'recreate') }, { default: () => '更新' }),
          h(NButton, { size: 'tiny', type: 'error', secondary: true, loading: loadingActions.value[row.id], onClick: () => handleAction(row.id, 'remove') }, { default: () => '删除' }),
          h(NButton, { size: 'tiny', onClick: () => showLogs(row.id, row.name) }, { default: () => '日志' })
        ]
      })
    }
  }
]

defineExpose({ refresh: fetchContainers })
</script>

<style scoped>
.logs-container { background: #000; color: #0f0; padding: 10px; max-height: 500px; overflow: auto; font-size: 12px; font-family: monospace; }
</style>
