<template>
  <div class="docker-manager">
    <n-space vertical size="large">
      <n-card>
        <n-tabs type="line" animated>
          <!-- 容器管理标签 -->
          <n-tab-pane name="containers" tab="容器管理">
            <n-space vertical size="medium">
              <n-space justify="space-between" align="center">
                <n-space>
                  <n-select
                    v-model:value="selectedHostId"
                    :options="hostOptions"
                    placeholder="选择 Docker 主机"
                    style="width: 200px"
                    @update:value="fetchContainers"
                  />
                  <n-button type="primary" secondary @click="showHostModal = true">管理主机</n-button>
                </n-space>
                <n-button type="info" ghost @click="fetchContainers" :loading="loading">刷新列表</n-button>
              </n-space>

              <n-data-table
                :columns="columns"
                :data="containers"
                :loading="loading"
                :pagination="pagination"
              />
            </n-space>
          </n-tab-pane>

          <!-- Compose 管理标签 -->
          <n-tab-pane name="compose" tab="Compose 项目">
            <n-space vertical size="medium">
              <n-space justify="end">
                <n-button type="primary" @click="handleCreateProject">新建项目</n-button>
                <n-button @click="fetchProjects">刷新项目</n-button>
              </n-space>
              
              <n-grid :cols="3" :x-gap="12" :y-gap="12">
                <n-gi v-for="p in projects" :key="p.name">
                  <n-card :title="p.name" size="small" hoverable>
                    <template #header-extra>
                      <n-space>
                        <n-button size="tiny" tertiary @click="editProject(p.name)">编辑</n-button>
                        <n-button size="tiny" type="error" ghost @click="deleteProject(p.name)">删除</n-button>
                      </n-space>
                    </template>
                    <n-space vertical>
                      <n-text depth="3" style="font-size: 12px">{{ p.path }}</n-text>
                      <n-space justify="space-around">
                        <n-button size="small" type="primary" secondary :loading="loadingActions[p.name]" @click="runComposeAction(p.name, 'up')">启动/更新</n-button>
                        <n-button size="small" type="warning" secondary :loading="loadingActions[p.name]" @click="runComposeAction(p.name, 'pull')">拉取</n-button>
                        <n-button size="small" type="error" secondary :loading="loadingActions[p.name]" @click="runComposeAction(p.name, 'down')">停止</n-button>
                      </n-space>
                    </n-space>
                  </n-card>
                </n-gi>
              </n-grid>
            </n-space>
          </n-tab-pane>
        </n-tabs>
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

    <!-- 主机编辑/添加弹窗 -->
    <n-modal v-model:show="showEditModal" preset="card" :title="editHostForm.id ? '编辑主机' : '添加主机'" style="width: 500px">
      <n-form :model="editHostForm" label-placement="left" label-width="100">
        <n-form-item label="名称">
          <n-input v-model:value="editHostForm.name" />
        </n-form-item>
        <n-form-item label="类型">
          <n-select
            v-model:value="editHostForm.type"
            :options="[
              { label: '本地 Docker (Socket)', value: 'local' },
              { label: '远程 Docker (SSH)', value: 'ssh' },
              { label: '远程 Docker (TCP)', value: 'tcp' }
            ]"
          />
        </n-form-item>
        <template v-if="editHostForm.type === 'ssh' || editHostForm.type === 'tcp'">
          <n-form-item :label="editHostForm.type === 'ssh' ? 'SSH 地址' : '主机地址'">
            <n-input v-model:value="editHostForm.ssh_host" />
          </n-form-item>
          <n-form-item :label="editHostForm.type === 'ssh' ? 'SSH 端口' : 'TCP 端口'">
            <n-input-number v-model:value="editHostForm.ssh_port" :min="1" :max="65535" style="width: 100%" />
          </n-form-item>
          <template v-if="editHostForm.type === 'ssh'">
            <n-form-item label="SSH 用户">
              <n-input v-model:value="editHostForm.ssh_user" />
            </n-form-item>
            <n-form-item label="SSH 密码">
              <n-input v-model:value="editHostForm.ssh_pass" type="password" show-password-on="mousedown" />
            </n-form-item>
          </template>
          <template v-if="editHostForm.type === 'tcp'">
            <n-form-item label="安全连接">
              <n-switch v-model:value="editHostForm.use_tls" />
            </n-form-item>
          </template>
        </template>
        <template v-if="editHostForm.type === 'local'">
          <n-form-item label="Socket 路径">
            <n-input v-model:value="editHostForm.base_url" />
          </n-form-item>
        </template>
        <n-space justify="end">
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" @click="saveHost">保存</n-button>
        </n-space>
      </n-form>
    </n-modal>

    <!-- Compose 编辑弹窗 -->
    <n-modal v-model:show="showComposeModal" preset="card" :title="currentProject.name ? '编辑项目: ' + currentProject.name : '新建 Compose 项目'" style="width: 800px">
      <n-form :model="currentProject">
        <n-form-item label="项目名称">
          <n-input v-model:value="currentProject.name" placeholder="请输入项目英文名" :disabled="isEditingProject" />
        </n-form-item>
        <n-form-item label="docker-compose.yml 内容">
          <n-input
            v-model:value="currentProject.content"
            type="textarea"
            placeholder="在此粘贴 YAML 内容"
            :autosize="{ minRows: 15, maxRows: 25 }"
            style="font-family: monospace"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showComposeModal = false">取消</n-button>
          <n-button type="primary" @click="saveProject">保存并应用</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 日志弹窗 -->
    <n-modal v-model:show="showLogsModal" preset="card" title="查看日志" style="width: 80vw">
      <pre class="logs-container">{{ containerLogs }}</pre>
    </n-modal>

    <!-- 命令行输出弹窗 -->
    <n-modal v-model:show="showCommandResult" preset="dialog" title="操作结果" style="width: 600px">
      <template #default>
        <div style="background: #1e1e1e; color: #adadad; padding: 10px; font-family: monospace; border-radius: 4px; overflow: auto; max-height: 400px">
          <div v-if="commandResult.stdout"><b>STDOUT:</b><br>{{ commandResult.stdout }}</div>
          <div v-if="commandResult.stderr" style="color: #ff9d9d; margin-top: 10px"><b>STDERR:</b><br>{{ commandResult.stderr }}</div>
        </div>
      </template>
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
import { ref, onMounted, h, computed } from 'vue'
import {
  NSpace, NCard, NButton, NSelect, NDataTable, NModal, NForm, NFormItem,
  NInput, NInputNumber, NList, NListItem, NText, NTag, useMessage, useDialog,
  NTabs, NTabPane, NGrid, NGi, NIcon
} from 'naive-ui'
import { EditOutlined as EditIcon } from '@vicons/material'
import axios from 'axios'
import type { DataTableColumns } from 'naive-ui'

interface DockerHost { id: string; name: string; type: string; ssh_host?: string; ssh_port?: number; ssh_user?: string; ssh_pass?: string; use_tls?: boolean; base_url?: string; }
interface Container { id: string; name: string; image: string; status: string; created: string; ports?: any; }

const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const hosts = ref<DockerHost[]>([])
const selectedHostId = ref<string | null>(null)
const containers = ref<Container[]>([])
const projects = ref<any[]>([])
const loadingActions = ref<Record<string, boolean>>({})

// 弹窗状态
const showHostModal = ref(false)
const showEditModal = ref(false)
const showComposeModal = ref(false)
const showLogsModal = ref(false)
const showCommandResult = ref(false)
const showCustomPortModal = ref(false)

const editHostForm = ref<Partial<DockerHost>>({})
const containerLogs = ref('')
const commandResult = ref({ stdout: '', stderr: '' })
const customPortForm = ref({ name: '', port: '' })
const containerSettings = ref<Record<string, any>>({})
const currentProject = ref({ name: '', content: '' })
const isEditingProject = ref(false)

const columns: DataTableColumns<Container> = [
  { title: '名称', key: 'name', width: 150 },
  { title: '状态', key: 'status', width: 80, render(row) {
      return h(NTag, { type: row.status === 'running' ? 'success' : 'error', size: 'small' }, { default: () => row.status })
    }
  },
  { title: '端口映射', key: 'ports', render(row) {
      const tags: any[] = []
      const currentHost = hosts.value.find(h => h.id === selectedHostId.value)
      const targetIp = (currentHost?.type === 'local' || !currentHost?.ssh_host) ? window.location.hostname : currentHost.ssh_host
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
          h(NButton, { size: 'tiny', secondary: true, loading: loadingActions.value[row.id], onClick: () => handleContainerAction(row.id, row.status === 'running' ? 'stop' : 'start') }, { default: () => row.status === 'running' ? '停止' : '启动' }),
                    h(NButton, { 
                      size: 'tiny', type: 'warning', secondary: true, 
                      loading: loadingActions.value[row.id],
                      onClick: () => handleRecreate(row.id) 
                    }, { default: () => '更新' }),
                    h(NButton, { 
                      size: 'tiny', type: 'error', secondary: true, 
                      loading: loadingActions.value[row.id],
                      onClick: () => handleDeleteContainer(row.id, row.name) 
                    }, { default: () => '删除' }),
                    h(NButton, { size: 'tiny', onClick: () => showLogs(row.id, row.name) }, { default: () => '日志' })
                  ]
                })
    }
  }
]

const fetchHosts = async () => {
  const res = await axios.get('/api/docker/hosts'); hosts.value = res.data
  if (hosts.value.length > 0 && !selectedHostId.value) { selectedHostId.value = hosts.value[0].id; fetchContainers() }
}
const fetchContainers = async () => {
  if (!selectedHostId.value) return; loading.value = true
  try { const res = await axios.get(`/api/docker/${selectedHostId.value}/containers`); containers.value = res.data } 
  catch (e) { message.error('获取容器失败') } finally { loading.value = false }
}
const fetchProjects = async () => { const res = await axios.get('/api/docker/compose/projects'); projects.value = res.data }
const fetchContainerSettings = async () => { const res = await axios.get('/api/docker/container-settings'); containerSettings.value = res.data }

const handleContainerAction = async (id: string, action: string) => {
  loadingActions.value[id] = true
  try {
    await axios.post(`/api/docker/${selectedHostId.value}/containers/${id}/action`, { action })
    message.success('指令已发送')
    setTimeout(fetchContainers, 2000)
  } catch (e) { message.error('操作失败') }
  finally { setTimeout(() => { loadingActions.value[id] = false }, 1000) }
}
const handleRecreate = (id: string) => {
  dialog.warning({ 
    title: '重构容器', 
    content: '将拉取镜像并重新创建，确定吗？', 
    positiveText: '确定', 
    negativeText: '取消', 
    onPositiveClick: () => {
      // 不直接返回 handleContainerAction 的 Promise，让弹窗立即关闭
      handleContainerAction(id, 'recreate')
    } 
  })
}
const handleDeleteContainer = (id: string, name: string) => {
  dialog.error({ 
    title: '危险操作', 
    content: `确定要【强制删除】容器 ${name} 吗？此操作无法撤销。`, 
    positiveText: '确认删除', 
    negativeText: '点错了', 
    onPositiveClick: () => {
      handleContainerAction(id, 'remove')
    } 
  })
}
const openCustomPortModal = (name: string) => { customPortForm.value = { name, port: containerSettings.value[name]?.custom_port || '' }; showCustomPortModal.value = true }
const saveCustomPort = async () => {
  await axios.post(`/api/docker/container-settings/${customPortForm.value.name}`, { custom_port: customPortForm.value.port })
  message.success('设置已保存'); showCustomPortModal.value = false; fetchContainerSettings()
}

const handleCreateProject = () => { 
  currentProject.value = { 
    name: '', 
    content: `version: "3.8"
services:
  app:
    image: ` 
  }; 
  isEditingProject.value = false; 
  showComposeModal.value = true 
}
const editProject = async (name: string) => { const res = await axios.get(`/api/docker/compose/projects/${name}`); currentProject.value = res.data; isEditingProject.value = true; showComposeModal.value = true }
const saveProject = async () => { await axios.post('/api/docker/compose/projects', currentProject.value); message.success('保存成功'); showComposeModal.value = false; fetchProjects() }
const deleteProject = (name: string) => { dialog.error({ title: '删除项目', content: `确定删除 ${name} 吗？`, positiveText: '删除', onPositiveClick: async () => { await axios.delete(`/api/docker/compose/projects/${name}`); fetchProjects() } }) }
const runComposeAction = async (name: string, action: string) => {
  loadingActions.value[name] = true
  try {
    const res = await axios.post(`/api/docker/compose/projects/${name}/action`, { action })
    commandResult.value = { stdout: res.data.stdout, stderr: res.data.stderr }; showCommandResult.value = true
  } finally { loadingActions.value[name] = false; fetchContainers() }
}
const showLogs = async (id: string, name: string) => { const res = await axios.get(`/api/docker/${selectedHostId.value}/containers/${id}/logs?tail=200`); containerLogs.value = res.data.logs; showLogsModal.value = true }
const testConnection = async (id: string) => { const res = await axios.post(`/api/docker/${id}/test`); message.info(res.data.status === 'ok' ? '连接正常' : '连接失败') }
const handleAddHost = () => { editHostForm.value = { type: 'local', ssh_port: 22, ssh_user: 'root' }; showEditModal.value = true }
const handleEditHost = (h: any) => { editHostForm.value = { ...h }; showEditModal.value = true }
const saveHost = async () => {
  if (editHostForm.value.id) await axios.put(`/api/docker/hosts/${editHostForm.value.id}`, editHostForm.value)
  else await axios.post('/api/docker/hosts', editHostForm.value)
  showEditModal.value = false; fetchHosts()
}
const deleteHost = (id: string) => { axios.delete(`/api/docker/hosts/${id}`).then(() => fetchHosts()) }
const hostOptions = computed(() => hosts.value.map(h => ({ label: h.name, value: h.id })))
const pagination = { pageSize: 15 }

onMounted(() => { fetchHosts(); fetchProjects(); fetchContainerSettings() })
</script>

<style scoped>
.logs-container { background: #000; color: #0f0; padding: 10px; max-height: 500px; overflow: auto; font-size: 12px; font-family: monospace; }
</style>
