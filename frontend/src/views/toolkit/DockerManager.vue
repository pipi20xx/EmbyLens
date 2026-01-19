<template>
  <div class="docker-manager">
    <n-space vertical size="large">
      <n-card title="Docker 容器管理" segmented>
        <template #header-extra>
          <n-space>
            <n-select
              v-model:value="selectedHostId"
              :options="hostOptions"
              placeholder="选择 Docker 主机"
              style="width: 200px"
              @update:value="fetchContainers"
            />
            <n-button type="primary" secondary @click="showHostModal = true">
              管理主机
            </n-button>
            <n-button type="info" ghost @click="fetchContainers" :loading="loading">
              刷新列表
            </n-button>
          </n-space>
        </template>

        <n-data-table
          :columns="columns"
          :data="containers"
          :loading="loading"
          :pagination="pagination"
          remote
        />
      </n-card>
    </n-space>

    <!-- 主机管理弹窗 -->
    <n-modal v-model:show="showHostModal" preset="card" title="Docker 主机管理" style="width: 600px">
      <n-space vertical>
        <n-button type="primary" block @click="handleAddHost">添加新主机</n-button>
        <n-list bordered>
          <n-list-item v-for="host in hosts" :key="host.id">
            <n-space justify="space-between" align="center">
              <div>
                <n-text strong>{{ host.name }}</n-text>
                <n-tag size="small" :type="host.type === 'local' ? 'info' : 'warning'" style="margin-left: 8px">
                  {{ host.type === 'local' ? '本地' : 'SSH' }}
                </n-tag>
                <div v-if="host.type === 'ssh'" style="font-size: 12px; color: #888">
                  {{ host.ssh_user }}@{{ host.ssh_host }}:{{ host.ssh_port }}
                </div>
              </div>
              <n-space>
                <n-button size="small" @click="testConnection(host.id)">测试</n-button>
                <n-button size="small" @click="handleEditHost(host)">编辑</n-button>
                <n-button size="small" type="error" ghost @click="deleteHost(host.id)">删除</n-button>
              </n-space>
            </n-space>
          </n-list-item>
        </n-list>
      </n-space>
    </n-modal>

    <!-- 主机编辑弹窗 -->
    <n-modal v-model:show="showEditModal" preset="card" :title="editHostForm.id ? '编辑主机' : '添加主机'" style="width: 500px">
      <n-form :model="editHostForm" label-placement="left" label-width="100">
        <n-form-item label="名称">
          <n-input v-model:value="editHostForm.name" placeholder="例如：我的服务器" />
        </n-form-item>
        <n-form-item label="类型">
          <n-select
            v-model:value="editHostForm.type"
            :options="[
              { label: '本地 Docker (Socket)', value: 'local' },
              { label: '远程 Docker (SSH)', value: 'ssh' }
            ]"
          />
        </n-form-item>
        <template v-if="editHostForm.type === 'ssh'">
          <n-form-item label="SSH 地址">
            <n-input v-model:value="editHostForm.ssh_host" placeholder="192.168.1.100" />
          </n-form-item>
          <n-form-item label="SSH 端口">
            <n-input-number v-model:value="editHostForm.ssh_port" :min="1" :max="65535" />
          </n-form-item>
          <n-form-item label="SSH 用户">
            <n-input v-model:value="editHostForm.ssh_user" placeholder="root" />
          </n-form-item>
        </template>
        <template v-else>
          <n-form-item label="Socket 路径">
            <n-input v-model:value="editHostForm.base_url" placeholder="unix://var/run/docker.sock" />
          </n-form-item>
        </template>
        <n-space justify="end">
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" @click="saveHost">保存</n-button>
        </n-space>
      </n-form>
    </n-modal>

    <!-- 日志弹窗 -->
    <n-modal v-model:show="showLogsModal" preset="card" :title="'容器日志: ' + currentContainerName" style="width: 90vw; max-width: 1000px">
      <div class="logs-container">
        <pre>{{ containerLogs }}</pre>
      </div>
      <template #footer>
        <n-space justify="end">
          <n-button @click="fetchLogs(currentContainerId)">刷新日志</n-button>
          <n-button @click="showLogsModal = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { 
  NSpace, NCard, NButton, NSelect, NDataTable, NModal, NForm, NFormItem, 
  NInput, NInputNumber, NList, NListItem, NText, NTag, useMessage, useDialog
} from 'naive-ui'
import axios from 'axios'
import type { DataTableColumns } from 'naive-ui'

interface DockerHost {
  id: string
  name: string
  type: string
  ssh_host?: string
  ssh_port?: number
  ssh_user?: string
  base_url?: string
}

interface Container {
  id: string
  full_id: string
  name: string
  image: string
  status: string
  state: any
  created: string
}

const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const hosts = ref<DockerHost[]>([])
const selectedHostId = ref<string | null>(null)
const containers = ref<Container[]>([])

const showHostModal = ref(false)
const showEditModal = ref(false)
const editHostForm = ref<Partial<DockerHost>>({
  type: 'local',
  ssh_port: 22,
  ssh_user: 'root'
})

const showLogsModal = ref(false)
const containerLogs = ref('')
const currentContainerId = ref('')
const currentContainerName = ref('')

const hostOptions = computed(() => {
  return hosts.value.map(h => ({
    label: h.name,
    value: h.id
  }))
})

const pagination = ref({
  pageSize: 10
})

const columns: DataTableColumns<Container> = [
  { title: '名称', key: 'name', width: 150 },
  { title: '状态', key: 'status', width: 100, render(row) {
      const type = row.status === 'running' ? 'success' : 'error'
      return h(NTag, { type, size: 'small' }, { default: () => row.status })
    }
  },
  { title: '镜像', key: 'image', ellipsis: true },
  { title: '创建时间', key: 'created', width: 200, render(row) {
      return new Date(row.created).toLocaleString()
    }
  },
  { title: '操作', key: 'actions', width: 250, render(row) {
      return h(NSpace, null, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: row.status === 'running' ? 'warning' : 'success',
            onClick: () => handleContainerAction(row.id, row.status === 'running' ? 'stop' : 'start')
          }, { default: () => row.status === 'running' ? '停止' : '启动' }),
          h(NButton, {
            size: 'small',
            type: 'info',
            onClick: () => handleContainerAction(row.id, 'restart')
          }, { default: () => '重启' }),
          h(NButton, {
            size: 'small',
            onClick: () => showLogs(row.id, row.name)
          }, { default: () => '日志' })
        ]
      })
    }
  }
]

const fetchHosts = async () => {
  try {
    const res = await axios.get('/api/docker/hosts')
    hosts.value = res.data
    if (hosts.value.length > 0 && !selectedHostId.value) {
      selectedHostId.value = hosts.value[0].id
      fetchContainers()
    }
  } catch (e) {
    message.error('获取主机列表失败')
  }
}

const fetchContainers = async () => {
  if (!selectedHostId.value) return
  loading.value = true
  try {
    const res = await axios.get(`/api/docker/${selectedHostId.value}/containers`)
    containers.value = res.data
  } catch (e) {
    message.error('获取容器列表失败')
  } finally {
    loading.value = false
  }
}

const handleContainerAction = async (containerId: string, action: string) => {
  if (!selectedHostId.value) return
  try {
    await axios.post(`/api/docker/${selectedHostId.value}/containers/${containerId}/action`, { action })
    message.success('操作执行中...')
    setTimeout(fetchContainers, 2000)
  } catch (e) {
    message.error('操作失败')
  }
}

const showLogs = async (containerId: string, name: string) => {
  currentContainerId.value = containerId
  currentContainerName.value = name
  showLogsModal.value = true
  fetchLogs(containerId)
}

const fetchLogs = async (containerId: string) => {
  if (!selectedHostId.value) return
  try {
    const res = await axios.get(`/api/docker/${selectedHostId.value}/containers/${containerId}/logs?tail=200`)
    containerLogs.value = res.data.logs
  } catch (e) {
    message.error('获取日志失败')
  }
}

const testConnection = async (hostId: string) => {
  try {
    const res = await axios.post(`/api/docker/${hostId}/test`)
    if (res.data.status === 'ok') {
      message.success('连接成功')
    } else {
      message.error('连接失败')
    }
  } catch (e) {
    message.error('测试连接出错')
  }
}

const handleAddHost = () => {
  editHostForm.value = {
    type: 'local',
    ssh_port: 22,
    ssh_user: 'root'
  }
  showEditModal.value = true
}

const handleEditHost = (host: DockerHost) => {
  editHostForm.value = { ...host }
  showEditModal.value = true
}

const saveHost = async () => {
  try {
    if (editHostForm.value.id) {
      await axios.put(`/api/docker/hosts/${editHostForm.value.id}`, editHostForm.value)
    } else {
      await axios.post('/api/docker/hosts', editHostForm.value)
    }
    message.success('保存成功')
    showEditModal.value = false
    fetchHosts()
  } catch (e) {
    message.error('保存失败')
  }
}

const deleteHost = (hostId: string) => {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这个 Docker 主机配置吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await axios.delete(`/api/docker/hosts/${hostId}`)
        message.success('删除成功')
        if (selectedHostId.value === hostId) {
          selectedHostId.value = null
          containers.value = []
        }
        fetchHosts()
      } catch (e) {
        message.error('删除失败')
      }
    }
  })
}

onMounted(() => {
  fetchHosts()
})
</script>

<style scoped>
.docker-manager {
  width: 100%;
}
.logs-container {
  background-color: #1a1a1a;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 4px;
  max-height: 60vh;
  overflow-y: auto;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
