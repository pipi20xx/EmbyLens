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
              <n-space justify="space-between" align="center">
                <n-space align="center">
                  <n-select
                    v-model:value="selectedHostId"
                    :options="hostOptions"
                    placeholder="选择 Docker 主机"
                    style="width: 200px"
                    @update:value="fetchProjects"
                  />
                  <n-space size="small" align="center" style="max-width: 600px">
                    <n-text depth="3" style="font-size: 12px">扫描范围:</n-text>
                    <template v-if="hosts.find(h => h.id === selectedHostId)?.compose_scan_paths">
                      <n-tag 
                        v-for="path in hosts.find(h => h.id === selectedHostId).compose_scan_paths.split(',').filter(p => p.trim())" 
                        :key="path" 
                        closable 
                        size="small" 
                        type="info"
                        @close="removeScanPath(path)"
                      >
                        {{ path }}
                      </n-tag>
                    </template>
                    <n-text v-else depth="3" style="font-size: 12px">仅探测运行中项目</n-text>
                  </n-space>
                  <n-button v-if="selectedHostId && hosts.find(h => h.id === selectedHostId)?.compose_scan_paths" size="tiny" type="error" quaternary @click="clearScanPaths">清空全部</n-button>
                </n-space>
                <n-space>
                  <n-button type="info" ghost @click="browseRemotePath('/')" :disabled="!selectedHostId">扫描外部目录</n-button>
                  <n-button type="primary" @click="handleCreateProject" :disabled="!selectedHostId">新建项目</n-button>
                  <n-button @click="fetchProjects" :disabled="!selectedHostId">刷新项目</n-button>
                </n-space>
              </n-space>
              
              <n-alert v-if="!selectedHostId" type="info">请先在上方或“容器管理”页选择一个 Docker 主机以查看其 Compose 项目。</n-alert>

              <n-grid :cols="3" :x-gap="12" :y-gap="12" v-else>
                <n-gi v-for="p in projects" :key="p.name">
                  <n-card :title="p.name" size="small" hoverable>
                    <template #header-extra>
                      <n-space align="center">
                        <n-tag :type="p.type === 'scanned' ? 'success' : 'warning'" size="small">
                          {{ p.type === 'scanned' ? '已记忆' : '探测到' }}
                        </n-tag>
                        <n-button v-if="p.type === 'detected'" size="tiny" circle quaternary @click="pinProject(p)" title="永久记忆此项目路径">
                          <template #icon><n-icon><push-pin-icon /></n-icon></template>
                        </n-button>
                        <n-tag :type="p.status?.includes('running') ? 'success' : 'default'" size="small">
                          {{ p.status || 'unknown' }}
                        </n-tag>
                        <n-button size="tiny" tertiary @click="editProject(p)">编辑</n-button>
                        <n-button size="tiny" type="error" ghost @click="deleteProject(p)">删除</n-button>
                      </n-space>
                    </template>
                    <n-space vertical>
                      <n-ellipsis style="max-width: 100%">
                        <n-text depth="3" style="font-size: 11px">{{ p.config_file || p.path }}</n-text>
                      </n-ellipsis>
                      <n-space justify="space-around">
                        <n-button size="small" type="primary" secondary :loading="loadingActions[p.name]" @click="runComposeAction(p, 'up')">启动/更新</n-button>
                        <n-button size="small" type="warning" secondary :loading="loadingActions[p.name]" @click="runComposeAction(p, 'pull')">拉取</n-button>
                        <n-button size="small" type="error" secondary :loading="loadingActions[p.name]" @click="runComposeAction(p, 'down')">停止</n-button>
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
                <n-tag size="small" type="warning" style="margin-left: 8px">
                  SSH 远程
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
        <n-form-item label="连接类型">
          <n-select
            v-model:value="editHostForm.type"
            :options="[
              { label: '远程 Docker (SSH)', value: 'ssh' }
            ]"
          />
        </n-form-item>
        <template v-if="editHostForm.type === 'ssh'">
          <n-form-item label="SSH 地址">
            <n-input v-model:value="editHostForm.ssh_host" placeholder="127.0.0.1 或 远程IP" />
          </n-form-item>
          <n-form-item label="SSH 端口">
            <n-input-number v-model:value="editHostForm.ssh_port" :min="1" :max="65535" style="width: 100%" />
          </n-form-item>
          <n-form-item label="SSH 用户">
            <n-input v-model:value="editHostForm.ssh_user" />
          </n-form-item>
          <n-form-item label="SSH 密码">
            <n-input v-model:value="editHostForm.ssh_pass" type="password" show-password-on="mousedown" />
          </n-form-item>
          <n-form-item label="Compose 扫描路径">
            <n-input-group>
              <n-input 
                v-model:value="editHostForm.compose_scan_paths" 
                type="textarea" 
                placeholder="例如: /opt/docker (多个路径用逗号分隔)" 
                :autosize="{ minRows: 2, maxRows: 4 }"
              />
              <n-button type="primary" ghost @click="browseRemotePath(browserPath || '/')">
                浏览
              </n-button>
            </n-input-group>
          </n-form-item>
        </template>
        <n-space justify="end">
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" @click="saveHost">保存</n-button>
        </n-space>
      </n-form>
    </n-modal>

    <!-- 远程文件夹浏览器 -->
    <n-modal v-model:show="showBrowserModal" preset="card" title="浏览远程目录" style="width: 500px">
      <n-space vertical>
        <n-breadcrumb>
          <n-breadcrumb-item @click="browseRemotePath('/')">根目录</n-breadcrumb-item>
          <n-breadcrumb-item>{{ browserPath }}</n-breadcrumb-item>
        </n-breadcrumb>
        
        <n-list hoverable clickable bordered style="max-height: 400px; overflow-y: auto">
          <n-list-item v-if="browserPath !== '/'" @click="browseRemotePath(browserPath.substring(0, browserPath.lastIndexOf('/')) || '/')">
            <n-text depth="3">.. (返回上级)</n-text>
          </n-list-item>
          <n-list-item v-for="item in browserItems" :key="item.path" @click="browseRemotePath(item.path)">
            <template #suffix>
              <n-button 
                v-if="(hosts.find(h => h.id === selectedHostId)?.compose_scan_paths || '').split(',').includes(item.path)"
                size="tiny" type="error" quaternary @click.stop="removeScanPath(item.path)"
              >
                移除
              </n-button>
              <n-button v-else size="tiny" type="primary" quaternary @click.stop="selectBrowserPath(item.path)">
                选择此文件夹
              </n-button>
            </template>
            <n-space align="center">
              <n-icon size="20" color="#fadb14"><folder-icon /></n-icon>
              {{ item.name }}
            </n-space>
          </n-list-item>
        </n-list>
      </n-space>
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
import { 
  EditOutlined as EditIcon,
  FolderOutlined as FolderIcon,
  PushPinOutlined as PushPinIcon
} from '@vicons/material'
import axios from 'axios'
import type { DataTableColumns } from 'naive-ui'

interface DockerHost { 
  id: string; 
  name: string; 
  type: string; 
  ssh_host?: string; 
  ssh_port?: number; 
  ssh_user?: string; 
  ssh_pass?: string; 
  use_tls?: boolean; 
  base_url?: string; 
  compose_scan_paths?: string; 
}
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
const showBrowserModal = ref(false)
const browserPath = ref('/')
const browserItems = ref<any[]>([])
const browserLoading = ref(false)

const browseRemotePath = async (path: string = '/') => {
  const hostId = selectedHostId.value || editHostForm.value.id
  if (!hostId) {
    message.warning('请先选择一个 Docker 主机'); return
  }
  
  browserLoading.value = true
  try {
    const res = await axios.get(`/api/docker/compose/${hostId}/ls`, {
      params: { path }
    })
    browserPath.value = res.data.current_path
    browserItems.value = res.data.items
    showBrowserModal.value = true
  } catch (e) {
    message.error('无法读取远程目录，请确保主机配置正确且已保存')
  } finally {
    browserLoading.value = false
  }
}

const selectBrowserPath = async (path: string) => {
  if (!selectedHostId.value) return
  
  const currentHost = hosts.value.find(h => h.id === selectedHostId.value)
  if (!currentHost) return

  const pathList = (currentHost.compose_scan_paths || '').split(',').map((p: string) => p.trim()).filter((p: string) => p)
  if (!pathList.includes(path)) {
    pathList.push(path)
    currentHost.compose_scan_paths = pathList.join(',')
    
    try {
      await axios.put(`/api/docker/hosts/${selectedHostId.value}`, currentHost)
      message.success(`已添加: ${path}`)
      // 保持弹窗开启，允许继续选择其他文件夹
      fetchProjects()
    } catch (e) {
      message.error('保存失败')
    }
  } else {
    message.info('该路径已在扫描列表中')
  }
}

const clearScanPaths = async () => {
  if (!selectedHostId.value) return
  const currentHost = hosts.value.find(h => h.id === selectedHostId.value)
  if (!currentHost) return

  dialog.warning({
    title: '重置扫描范围',
    content: '确定要清空所有已记录的扫描路径吗？（探测到的运行中项目不会受影响）',
    positiveText: '确定清空',
    onPositiveClick: async () => {
      currentHost.compose_scan_paths = ''
      await axios.put(`/api/docker/hosts/${selectedHostId.value}`, currentHost)
      message.success('扫描路径已重置')
      fetchProjects()
    }
  })
}

const removeScanPath = async (path: string) => {
  if (!selectedHostId.value) return
  const currentHost = hosts.value.find(h => h.id === selectedHostId.value)
  if (!currentHost) return

  let pathList = (currentHost.compose_scan_paths || '').split(',').map((p: string) => p.trim()).filter((p: string) => p)
  pathList = pathList.filter(p => p !== path)
  currentHost.compose_scan_paths = pathList.join(',')
  
  try {
    await axios.put(`/api/docker/hosts/${selectedHostId.value}`, currentHost)
    message.info(`已移除路径: ${path}`)
    fetchProjects()
  } catch (e) {
    message.error('保存失败')
  }
}

const pinProject = async (p: any) => {
  if (!selectedHostId.value) return
  const currentHost = hosts.value.find(h => h.id === selectedHostId.value)
  if (!currentHost) return

  const path = p.path
  const pathList = (currentHost.compose_scan_paths || '').split(',').map((item: string) => item.trim()).filter((item: string) => item)
  
  if (!pathList.includes(path)) {
    pathList.push(path)
    currentHost.compose_scan_paths = pathList.join(',')
    try {
      await axios.put(`/api/docker/hosts/${selectedHostId.value}`, currentHost)
      message.success(`项目路径已永久记忆: ${path}`)
      fetchProjects()
    } catch (e) {
      message.error('保存失败')
    }
  }
}

const editHostForm = ref<Partial<DockerHost>>({})
const containerLogs = ref('')
const commandResult = ref({ stdout: '', stderr: '' })
const currentPortForm = ref({ name: '', port: '' })
const containerSettings = ref<Record<string, any>>({})
const currentProject = ref({ name: '', content: '', path: '' })
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
  if (hosts.value.length > 0 && !selectedHostId.value) { 
    selectedHostId.value = hosts.value[0].id; 
    fetchContainers();
    fetchProjects();
  }
}
const fetchContainers = async () => {
  if (!selectedHostId.value) return; loading.value = true
  try { const res = await axios.get(`/api/docker/${selectedHostId.value}/containers`); containers.value = res.data } 
  catch (e) { message.error('获取容器失败') } finally { loading.value = false }
}
const fetchProjects = async () => { 
  if (!selectedHostId.value) return;
  const res = await axios.get(`/api/docker/compose/${selectedHostId.value}/projects`); 
  projects.value = res.data 
}
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
    image: `,
    path: ''
  }; 
  isEditingProject.value = false; 
  showComposeModal.value = true 
}
const editProject = async (p: any) => { 
  const res = await axios.get(`/api/docker/compose/${selectedHostId.value}/projects/${p.name}`, {
    params: { path: p.config_file || p.path }
  }); 
  currentProject.value = { ...res.data, path: p.config_file || p.path }; 
  isEditingProject.value = true; 
  showComposeModal.value = true 
}
const saveProject = async () => { 
  await axios.post(`/api/docker/compose/${selectedHostId.value}/projects`, 
    { name: currentProject.value.name, content: currentProject.value.content },
    { params: { path: currentProject.value.path } }
  ); 
  message.success('保存成功'); 
  showComposeModal.value = false; 
  fetchProjects() 
}
const deleteProject = (p: any) => { 
  dialog.error({ 
    title: '删除项目', 
    content: `确定从视图中移除项目 ${p.name} 吗？（不会删除远程文件）`, 
    positiveText: '确认', 
    onPositiveClick: async () => { 
      await axios.delete(`/api/docker/compose/${selectedHostId.value}/projects/${p.name}`, {
        params: { path: p.config_file || p.path }
      }); 
      fetchProjects() 
    } 
  }) 
}
const runComposeAction = async (p: any, action: string) => {
  if (!selectedHostId.value) return;
  loadingActions.value[p.name] = true
  try {
    const res = await axios.post(`/api/docker/compose/${selectedHostId.value}/projects/${p.name}/action`, { 
      action,
      path: p.config_file || p.path
    })
    commandResult.value = { stdout: res.data.stdout, stderr: res.data.stderr }; showCommandResult.value = true
  } finally { loadingActions.value[p.name] = false; fetchContainers(); fetchProjects() }
}
const showLogs = async (id: string, name: string) => { const res = await axios.get(`/api/docker/${selectedHostId.value}/containers/${id}/logs?tail=200`); containerLogs.value = res.data.logs; showLogsModal.value = true }
const testConnection = async (id: string) => { const res = await axios.post(`/api/docker/${id}/test`); message.info(res.data.status === 'ok' ? '连接正常' : '连接失败') }
const handleAddHost = () => { editHostForm.value = { type: 'ssh', ssh_port: 22, ssh_user: 'root' }; showEditModal.value = true }
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
