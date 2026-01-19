<template>
  <div class="docker-manager">
    <n-space vertical size="large">
      <n-card>
        <template #header>
          <n-space align="center" justify="space-between" style="width: 100%">
            <n-space align="center" size="large">
              <n-text strong style="font-size: 16px">Docker 管理</n-text>
              <n-select
                v-model:value="selectedHostId"
                :options="hostOptions"
                placeholder="选择 Docker 主机"
                style="width: 220px"
              />
              <n-button type="primary" secondary @click="showHostModal = true">管理主机</n-button>
              
              <!-- 全局扫描范围展示 -->
              <n-space size="small" align="center" v-if="selectedHostId" style="max-width: 500px">
                <n-text depth="3" style="font-size: 12px">扫描范围:</n-text>
                <template v-if="currentHost?.compose_scan_paths">
                  <n-tag 
                    v-for="path in currentHost.compose_scan_paths.split(',').filter(p => p.trim())" 
                    :key="path" closable size="small" type="info" @close="removeScanPath(path)"
                  >
                    {{ path }}
                  </n-tag>
                </template>
                <n-text v-else depth="3" style="font-size: 12px">仅探测运行中项目</n-text>
              </n-space>
            </n-space>
            
            <n-space>
              <n-button type="info" ghost @click="showBrowserModal = true" :disabled="!selectedHostId" v-if="activeTab === 'compose'">扫描外部目录</n-button>
              <n-button type="info" ghost @click="refreshAll" :loading="refreshing">全部刷新</n-button>
            </n-space>
          </n-space>
        </template>

        <n-tabs v-model:value="activeTab" type="line" animated>
          <n-tab-pane name="containers" tab="容器管理">
            <container-panel ref="containerPanelRef" :host-id="selectedHostId" :hosts="hosts" />
          </n-tab-pane>
          <n-tab-pane name="compose" tab="Compose 项目">
            <compose-panel 
              ref="composePanelRef" 
              :host-id="selectedHostId" 
              :hosts="hosts" 
              :picked-path="pickedPathForNewProject"
              @refresh-containers="refreshContainers" 
              @refresh-hosts="fetchHosts" 
              @browse-path="browseRemotePath"
              @request-pick-path="handleRequestPickPath"
            />
          </n-tab-pane>
        </n-tabs>
      </n-card>
    </n-space>

    <!-- 模块化弹窗 -->
    <host-manager-modal v-model:show="showHostModal" :hosts="hosts" @refresh="fetchHosts" />
    <file-browser-modal 
      v-model:show="showBrowserModal" 
      :host-id="selectedHostId" 
      :selected-paths="currentHostPaths" 
      :initial-path="browserInitialPath"
      @select="handleFileSelect" 
      @remove="removeScanPath" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { NSpace, NCard, NText, NSelect, NButton, NTag, NTabs, NTabPane, useMessage, useDialog } from 'naive-ui'
import axios from 'axios'

// 导入乐高组件
import ContainerPanel from './docker/components/ContainerPanel.vue'
import ComposePanel from './docker/components/ComposePanel.vue'
import HostManagerModal from './docker/components/HostManagerModal.vue'
import FileBrowserModal from './docker/components/FileBrowserModal.vue'

const message = useMessage()
const dialog = useDialog()

const hosts = ref<any[]>([])
const selectedHostId = ref<string | null>(null)
const activeTab = ref('containers')
const refreshing = ref(false)

const showHostModal = ref(false)
const showBrowserModal = ref(false)
const browserInitialPath = ref('/')
const isPickingForNewProject = ref(false)
const pickedPathForNewProject = ref('')

const browseRemotePath = async (path: string = '/') => {
  if (!selectedHostId.value) {
    message.warning('请先选择一个 Docker 主机'); return
  }
  isPickingForNewProject.value = false
  browserInitialPath.value = path
  showBrowserModal.value = true
}

const handleRequestPickPath = (currentPath: string) => {
  isPickingForNewProject.value = true
  browserInitialPath.value = currentPath || '/'
  showBrowserModal.value = true
}

const handleFileSelect = (path: string) => {
  if (isPickingForNewProject.value) {
    pickedPathForNewProject.value = path
    // 触发更新后清空，防止下次干扰
    setTimeout(() => { pickedPathForNewProject.value = '' }, 500)
    showBrowserModal.value = false
  } else {
    addScanPath(path)
  }
}


const containerPanelRef = ref()
const composePanelRef = ref()

const hostOptions = computed(() => hosts.value.map(h => ({ label: h.name, value: h.id })))
const currentHost = computed(() => hosts.value.find(h => h.id === selectedHostId.value))
const currentHostPaths = computed(() => (currentHost.value?.compose_scan_paths || '').split(',').map(p => p.trim()).filter(p => p))

const fetchHosts = async () => {
  const res = await axios.get('/api/docker/hosts')
  hosts.value = res.data
  if (hosts.value.length > 0 && !selectedHostId.value) {
    selectedHostId.value = hosts.value[0].id
  }
}

const addScanPath = async (path: string) => {
  if (!currentHost.value) return
  const pathList = [...currentHostPaths.value]
  if (!pathList.includes(path)) {
    pathList.push(path)
    currentHost.value.compose_scan_paths = pathList.join(',')
    await axios.put(`/api/docker/hosts/${selectedHostId.value}`, currentHost.value)
    message.success('已添加扫描路径')
    composePanelRef.value?.refresh()
  }
}

const removeScanPath = async (path: string) => {
  if (!currentHost.value) return
  const pathList = currentHostPaths.value.filter(p => p !== path)
  currentHost.value.compose_scan_paths = pathList.join(',')
  await axios.put(`/api/docker/hosts/${selectedHostId.value}`, currentHost.value)
  message.info('已移除路径')
  composePanelRef.value?.refresh()
}

const refreshContainers = () => containerPanelRef.value?.refresh()
const refreshAll = async () => {
  refreshing.value = true
  await Promise.all([fetchHosts(), containerPanelRef.value?.refresh(), composePanelRef.value?.refresh()])
  refreshing.value = false
}

onMounted(fetchHosts)
</script>