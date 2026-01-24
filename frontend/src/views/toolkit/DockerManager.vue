<template>
  <div class="docker-manager">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">Docker 容器与项目管理</n-text></n-h2>
        <n-text depth="3">统一管理多台远程主机的 Docker 容器及 Docker Compose 项目，支持一键部署与日志回溯。</n-text>
      </div>

      <n-card size="small" segmented>
        <template #header>
          <n-space align="center" justify="space-between" style="width: 100%">
            <n-space align="center" size="large">
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
              <n-button type="warning" ghost @click="openAutoUpdateModal">计划设置</n-button>
              <n-button type="info" ghost @click="showBrowserModal = true" :disabled="!selectedHostId" v-if="activeTab === 'compose'">扫描外部目录</n-button>
              <n-button type="info" ghost @click="refreshAll" :loading="refreshing">全部刷新</n-button>
            </n-space>
          </n-space>
        </template>

        <n-tabs v-model:value="activeTab" type="line" animated>
          <n-tab-pane name="containers" tab="容器管理">
            <container-panel ref="containerPanelRef" :host-id="selectedHostId" :hosts="hosts" />
          </n-tab-pane>
          <n-tab-pane name="compose" tab="Compose 管理">
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
          <n-tab-pane name="system" tab="环境检测">
            <system-info-panel :host-id="selectedHostId" />
          </n-tab-pane>
          <n-tab-pane name="maintenance" tab="配置">
            <maintenance-panel :host-id="selectedHostId" />
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

    <!-- 自动更新设置弹窗 -->
    <n-modal v-model:show="showAutoUpdateModal" preset="card" title="自动更新全局设置" style="width: 450px">
      <n-space vertical size="large">
        <n-alert type="info" title="说明" bordered>
          此处设置将决定系统何时执行镜像检查。开启后，仅会对在容器列表中手动勾选了“自动更新”标记的容器生效。
        </n-alert>
        
        <n-form-item label="启用全局调度">
          <n-switch v-model:value="autoUpdateSettings.enabled" />
        </n-form-item>

        <n-form-item label="执行模式">
          <n-radio-group v-model:value="autoUpdateSettings.type">
            <n-radio-button value="cron">每日定时 (Cron)</n-radio-button>
            <n-radio-button value="interval">固定间隔 (Interval)</n-radio-button>
          </n-radio-group>
        </n-form-item>

        <!-- 每日定时模式：使用时间选择器 -->
        <n-form-item v-if="autoUpdateSettings.type === 'cron'" label="执行时间 (每天)">
          <n-time-picker 
            v-model:formatted-value="autoUpdateSettings.value" 
            value-format="HH:mm" 
            format="HH:mm" 
            style="width: 100%"
          />
        </n-form-item>

        <!-- 固定间隔模式：使用天/时/分组合 -->
        <n-form-item v-if="autoUpdateSettings.type === 'interval'" label="执行间隔">
          <n-grid :cols="3" :x-gap="12">
            <n-form-item-gi label="天">
              <n-input-number v-model:value="intervalParts.d" :min="0" placeholder="0" />
            </n-form-item-gi>
            <n-form-item-gi label="时">
              <n-input-number v-model:value="intervalParts.h" :min="0" :max="23" placeholder="0" />
            </n-form-item-gi>
            <n-form-item-gi label="分">
              <n-input-number v-model:value="intervalParts.m" :min="0" :max="59" placeholder="0" />
            </n-form-item-gi>
          </n-grid>
          <template #feedback>
            当前合计: {{ (intervalParts.d * 1440) + (intervalParts.h * 60) + intervalParts.m }} 分钟
          </template>
        </n-form-item>

        <n-space justify="end" style="margin-top: 20px">
          <n-button @click="showAutoUpdateModal = false">取消</n-button>
          <n-button type="primary" :loading="savingAutoUpdate" @click="saveAutoUpdateSettings">保存并生效</n-button>
        </n-space>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { NSpace, NCard, NText, NSelect, NButton, NTag, NTabs, NTabPane, useMessage, useDialog, NH2, NModal, NFormItem, NRadioGroup, NRadioButton, NInput, NSwitch, NAlert, NTimePicker, NGrid, NFormItemGi, NInputNumber } from 'naive-ui'
import axios from 'axios'

// 导入乐高组件
import ContainerPanel from './docker/components/ContainerPanel.vue'
import ComposePanel from './docker/components/ComposePanel.vue'
import MaintenancePanel from './docker/components/MaintenancePanel.vue'
import SystemInfoPanel from './docker/components/SystemInfoPanel.vue'
import HostManagerModal from './docker/components/HostManagerModal.vue'
import FileBrowserModal from './docker/components/FileBrowserModal.vue'

const message = useMessage()
const dialog = useDialog()

const hosts = ref<any[]>([])
const selectedHostId = ref<string | null>(null)
const activeTab = ref('containers')
const refreshing = ref(false)

const STORAGE_KEY = 'lens_selected_docker_host'

// 记忆选择的主机
watch(selectedHostId, (val) => {
  if (val) localStorage.setItem(STORAGE_KEY, val)
})

const showHostModal = ref(false)
const showBrowserModal = ref(false)
const browserInitialPath = ref('/')
const isPickingForNewProject = ref(false)
const pickedPathForNewProject = ref('')

const showAutoUpdateModal = ref(false)
const savingAutoUpdate = ref(false)
const autoUpdateSettings = ref({
  enabled: true,
  type: 'cron',
  value: '03:00'
})

// 用于间隔模式的拆解数据
const intervalParts = ref({ d: 0, h: 0, m: 0 })

const openAutoUpdateModal = async () => {
  try {
    const res = await axios.get('/api/docker/auto-update/settings')
    autoUpdateSettings.value = res.data
    
    // 如果是间隔模式，反向拆解分钟数为天/时/分
    if (autoUpdateSettings.value.type === 'interval') {
      const totalMin = parseInt(autoUpdateSettings.value.value) || 0
      intervalParts.value.d = Math.floor(totalMin / 1440)
      intervalParts.value.h = Math.floor((totalMin % 1440) / 60)
      intervalParts.value.m = totalMin % 60
    }
    
    showAutoUpdateModal.value = true
  } catch (e) {
    message.error('获取设置失败')
  }
}

const saveAutoUpdateSettings = async () => {
  savingAutoUpdate.value = true
  try {
    // 如果是间隔模式，保存前先合并数据
    if (autoUpdateSettings.value.type === 'interval') {
      const totalMin = (intervalParts.value.d * 1440) + (intervalParts.value.h * 60) + intervalParts.value.m
      if (totalMin <= 0) {
        message.warning('执行间隔不能为 0')
        savingAutoUpdate.value = false
        return
      }
      autoUpdateSettings.value.value = String(totalMin)
    }

    await axios.post('/api/docker/auto-update/settings', autoUpdateSettings.value)
    message.success('设置已保存，调度器已重载')
    showAutoUpdateModal.value = false
  } catch (e) {
    message.error('保存失败')
  } finally {
    savingAutoUpdate.value = false
  }
}

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
  try {
    const res = await axios.get('/api/docker/hosts')
    hosts.value = Array.isArray(res.data) ? res.data : []
    
    if (hosts.value.length > 0) {
      const savedHostId = localStorage.getItem(STORAGE_KEY)
      // 如果有记忆的 ID 且在当前列表中，则恢复它
      if (savedHostId && hosts.value.some(h => h && h.id === savedHostId)) {
        selectedHostId.value = savedHostId
      } else if (!selectedHostId.value) {
        selectedHostId.value = hosts.value[0].id
      }
    }
  } catch (e) {
    hosts.value = []
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