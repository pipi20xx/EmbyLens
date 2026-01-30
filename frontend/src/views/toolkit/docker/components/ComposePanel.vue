<template>
  <div class="compose-panel">
    <n-space vertical size="medium">
      <n-space justify="space-between" v-if="hostId">
        <n-space>
          <n-button type="primary" @click="handleCreateProject">新建项目</n-button>
          <n-input
            v-model:value="searchQuery"
            placeholder="搜索项目名称或路径..."
            clearable
            style="width: 250px"
          >
            <template #prefix>
              <n-icon><SearchIcon /></n-icon>
            </template>
          </n-input>
        </n-space>
        <n-button-group>
          <n-button type="info" ghost @click="fetchProjects(true)" :loading="loading">
            <template #icon><n-icon><RefreshIcon /></n-icon></template>
            刷新列表
          </n-button>
          <n-button type="success" secondary @click="handleBulkAction('up')">全部启动/更新</n-button>
          <n-button type="error" secondary @click="handleBulkAction('down')">全部停止</n-button>
        </n-button-group>
      </n-space>
      
      <n-data-table
        :columns="columns"
        :data="filteredProjects"
        :loading="loading"
        :pagination="{ pageSize: 15 }"
      />
    </n-space>

    <!-- Compose 编辑/新建弹窗 -->
    <n-modal v-model:show="showComposeModal" preset="card" :title="isEditingProject ? '编辑项目: ' + currentProject.name : '新建 Compose 项目'" style="width: 800px">
      <n-form :model="currentProject" label-placement="left" label-width="100">
        <n-form-item label="项目名称">
          <n-input v-model:value="currentProject.name" placeholder="例如: my-awesome-app" :disabled="isEditingProject" />
        </n-form-item>
        
        <!-- 新建项目时的路径管理 -->
        <template v-if="!isEditingProject">
          <n-form-item label="基础保存路径">
            <n-input-group>
              <n-input v-model:value="baseSavePath" placeholder="选择存放项目的根目录" />
              <n-button type="primary" ghost @click="pickBasePath">选择</n-button>
            </n-input-group>
          </n-form-item>
          <n-form-item label="完整保存路径">
            <n-text depth="3" code style="word-break: break-all">
              {{ finalSavePath }}
            </n-text>
          </n-form-item>
        </template>

        <n-form-item label="YAML 内容" :feedback="yamlError" :validation-status="yamlError ? 'error' : undefined">
          <n-input
            v-model:value="currentProject.content"
            type="textarea"
            placeholder="在此输入 docker-compose.yml 内容"
            :autosize="{ minRows: 12, maxRows: 20 }"
            style="font-family: monospace"
            @input="handleYamlInput"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showComposeModal = false">取消</n-button>
          <n-button type="primary" @click="saveProject" :disabled="!!yamlError">保存项目</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 命令行输出弹窗 -->
    <n-modal v-model:show="showCommandResult" preset="dialog" title="操作结果" style="width: 600px">
      <template #default>
        <div style="background: rgba(0, 0, 0, 0.3); color: var(--text-color); padding: 12px; font-family: 'Fira Code', 'JetBrains Mono', monospace; border-radius: 4px; overflow: auto; max-height: 400px; font-size: 12px;">
          <div v-if="commandResult.stdout"><b style="color: var(--primary-color)">STDOUT:</b><br>{{ commandResult.stdout }}</div>
          <div v-if="commandResult.stderr" style="margin-top: 10px"><b style="color: #f0a020">STDERR:</b><br>{{ commandResult.stderr }}</div>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, h } from 'vue'
import { 
  NSpace, NButton, NButtonGroup, NDataTable, NTag, NIcon, NText, NEllipsis, 
  NModal, NForm, NFormItem, NInput, NInputGroup, NCheckbox, useMessage, useDialog 
} from 'naive-ui'
import { 
  PushPinOutlined as PushPinIcon, 
  FolderOutlined as FolderIcon,
  EditOutlined as EditIcon,
  DeleteOutlined as DeleteIcon,
  PlayCircleOutlined as StartIcon,
  StopCircleOutlined as StopIcon,
  CloudDownloadOutlined as PullIcon,
  SearchOutlined as SearchIcon,
  BackupTableRound as BackupIcon,
  AutorenewOutlined as RefreshIcon
} from '@vicons/material'
import axios from 'axios'
import type { DataTableColumns } from 'naive-ui'
import yaml from 'js-yaml'
import { useDockerStore } from '@/store/dockerStore'

const props = defineProps({
  hostId: { type: String, default: null },
  hosts: { type: Array, default: [] },
  pickedPath: { type: String, default: '' }
})

const emit = defineEmits(['refresh-containers', 'refresh-hosts', 'browse-path', 'request-pick-path'])

const message = useMessage()
const dialog = useDialog()
const dockerStore = useDockerStore()

const projects = computed(() => (dockerStore.projects[props.hostId || ''] || []).sort((a: any, b: any) => a.name.localeCompare(b.name)))
const loading = computed(() => dockerStore.loading[`projects_${props.hostId}`] || false)

const loadingActions = ref<Record<string, boolean>>({})
const searchQuery = ref('')

const filteredProjects = computed(() => {
  const data = projects.value
  if (!searchQuery.value) return data
  const query = searchQuery.value.toLowerCase()
  return data.filter((p: any) => 
    p.name.toLowerCase().includes(query) || 
    (p.config_file || p.path || '').toLowerCase().includes(query)
  )
})

const showComposeModal = ref(false)
const showCommandResult = ref(false)
const commandResult = ref({ stdout: '', stderr: '' })
const currentProject = ref({ name: '', content: '', path: '' })
const isEditingProject = ref(false)
const yamlError = ref<string | null>(null)

const translateYamlError = (e: any) => {
  const reason = e.reason || ''
  const map: Record<string, string> = {
    'can not read a block mapping entry; a multiline key may not be an implicit key': '无法读取块映射条目；可能是缩进错误或缺少冒号',
    'bad indentation of a mapping entry': '映射条目缩进错误',
    'duplicated mapping key': '存在重复的键名',
    'end of the stream or a document separator is expected': '期望流结束或文档分隔符，请检查缩进',
    'incomplete explicit mapping pair': '不完整的显式映射对',
    'unknown tag': '未知的标签',
    'missed comma between flow collection entries': '流集合条目之间缺少逗号',
  }
  
  let msg = map[reason] || reason || 'YAML 格式错误'
  if (e.mark) {
    msg += ` (行 ${e.mark.line + 1}, 列 ${e.mark.column + 1})`
  }
  return msg
}

const handleYamlInput = (value: string) => {
  if (!value) {
    yamlError.value = null
    return
  }
  
  try {
    yaml.load(value)
    yamlError.value = null
  } catch (e: any) {
    yamlError.value = translateYamlError(e)
  }
}

// 状态本地化
const statusMap: Record<string, string> = {
  'running': '运行中',
  'exited': '已停止',
  'restarting': '重启中',
  'paused': '已暂停',
  'created': '已创建',
  'unknown': '未知'
}

const formatStatus = (status: string) => {
  if (!status) return '未知'
  const match = status.match(/^([a-z]+)\(?(\d*)\)?$/i)
  if (match) {
    const key = match[1].toLowerCase()
    const count = match[2]
    const text = statusMap[key] || key
    return count ? `${text}(${count})` : text
  }
  return status
}

const fetchProjects = async (force = false) => {
  if (!props.hostId) return
  await dockerStore.fetchProjects(props.hostId, force)
}

// 表格列定义
const columns: DataTableColumns<any> = [
  {
    title: '项目名称',
    key: 'name',
    width: 180,
    render(row) {
      return h(NSpace, { align: 'center', size: 'small' }, {
        default: () => [
          h('span', { style: 'font-weight: bold; color: var(--text-color)' }, row.name),
          row.type === 'detected' ? h(NButton, {
            size: 'tiny', circle: true, quaternary: true,
            onClick: () => pinProject(row)
          }, { default: () => h(NIcon, null, { default: () => h(PushPinIcon) }) }) : null
        ]
      })
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      const isRunning = row.status?.includes('running')
      return h(NTag, {
        type: isRunning ? 'success' : 'default',
        size: 'small',
        round: true
      }, { default: () => formatStatus(row.status) })
    }
  },
  {
    title: '类型',
    key: 'type',
    width: 90,
    render(row) {
      return h(NTag, {
        type: row.type === 'scanned' ? 'info' : 'warning',
        size: 'small',
        quaternary: true
      }, { default: () => row.type === 'scanned' ? '已记忆' : '探测到' })
    }
  },
  {
    title: '配置文件路径',
    key: 'path',
    render(row) {
      return h(NSpace, { align: 'center', size: 'small' }, {
        default: () => [
          h(NEllipsis, { style: 'max-width: 300px; font-size: 12px; color: var(--text-color); opacity: 0.6' }, { default: () => row.config_file || row.path }),
          h(NButton, {
            size: 'tiny', quaternary: true, circle: true,
            onClick: () => emit('browse-path', row.path)
          }, { default: () => h(NIcon, null, { default: () => h(FolderIcon) }) })
        ]
      })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 420,
    render(row) {
      const isLoading = loadingActions.value[row.name]
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { size: 'tiny', type: 'primary', secondary: true, loading: isLoading, onClick: () => runComposeAction(row, 'up') }, { 
            icon: () => h(NIcon, null, { default: () => h(StartIcon) }),
            default: () => '启动/更新' 
          }),
          h(NButton, { size: 'tiny', type: 'warning', secondary: true, loading: isLoading, onClick: () => runComposeAction(row, 'pull') }, { 
            icon: () => h(NIcon, null, { default: () => h(PullIcon) }),
            default: () => '拉取' 
          }),
          h(NButton, { size: 'tiny', type: 'error', secondary: true, loading: isLoading, onClick: () => runComposeAction(row, 'down') }, { 
            icon: () => h(NIcon, null, { default: () => h(StopIcon) }),
            default: () => '停止' 
          }),
          h(NButton, { size: 'tiny', secondary: true, onClick: () => editProject(row) }, { 
            icon: () => h(NIcon, null, { default: () => h(EditIcon) }),
            default: () => '编辑' 
          }),
          h(NButton, { size: 'tiny', type: 'error', secondary: true, onClick: () => deleteProject(row) }, { 
            icon: () => h(NIcon, null, { default: () => h(DeleteIcon) }),
            default: () => '删除' 
          }),
          h(NButton, { size: 'tiny', type: 'info', quaternary: true, onClick: () => createBackupTask(row) }, { 
            icon: () => h(NIcon, null, { default: () => h(BackupIcon) }),
            default: () => '备份' 
          })
        ]
      })
    }
  }
]

const createBackupTask = (p: any) => {
  dialog.info({
    title: '创建备份任务',
    content: `确定要为项目 ${p.name} 创建一个自动备份任务吗？该任务将定期备份整个项目文件夹并拉取到 Lens 本地服务器。`,
    positiveText: '确认创建',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await axios.post(`/api/docker/compose/${props.hostId}/projects/${p.name}/create-backup-task`, { 
          path: p.config_file || p.path 
        })
        message.success('备份任务已创建，可前往“数据备份管理”进行详细配置')
      } catch (e: any) {
        message.error('创建失败: ' + (e.response?.data?.detail || '未知错误'))
      }
    }
  })
}

// 路径记忆逻辑
const baseSavePath = ref('/opt/docker-compose')
const storageKey = computed(() => `lens_last_path_${props.hostId}`)

const loadLastPath = () => {
  const saved = localStorage.getItem(storageKey.value)
  if (saved) baseSavePath.value = saved
}

const finalSavePath = computed(() => {
  const base = baseSavePath.value.replace(/\/+$/, '')
  const name = currentProject.value.name.trim() || 'project_name'
  return `${base}/${name}/docker-compose.yml`
})

watch(() => props.hostId, () => {
  fetchProjects()
  loadLastPath()
}, { immediate: true })

// 监听外部传回的路径
watch(() => props.pickedPath, (val) => {
  if (val && showComposeModal.value && !isEditingProject.value) {
    baseSavePath.value = val
  }
})

const handleBulkAction = (action: string) => {
  const actionText = action === 'up' ? '启动/更新' : '停止'
  dialog.warning({
    title: `批量${actionText}`,
    content: `确定要${actionText}当前主机下的所有 Compose 项目吗？这可能会消耗较多系统资源并导致服务短暂中断。`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      const m = message.loading(`正在批量${actionText}所有项目...`, { duration: 0 })
      try {
        await axios.post(`/api/docker/compose/${props.hostId}/projects/bulk-action`, { action })
        message.success(`批量${actionText}指令已发送`)
        fetchProjects(true)
        emit('refresh-containers')
      } catch (e) {
        message.error('操作失败')
      } finally {
        m.destroy()
      }
    }
  })
}

const handleCreateProject = () => { 
  currentProject.value = { 
    name: '', 
    content: `version: "3.8"\nservices:\n  app:\n    image: `,
    path: '' 
  }
  isEditingProject.value = false
  yamlError.value = null
  loadLastPath()
  showComposeModal.value = true 
  handleYamlInput(currentProject.value.content)
}

const pickBasePath = () => {
  emit('request-pick-path', baseSavePath.value)
}

const editProject = async (p: any) => { 
  const res = await axios.get(`/api/docker/compose/${props.hostId}/projects/${p.name}`, {
    params: { path: p.config_file || p.path }
  })
  currentProject.value = { ...res.data, path: p.config_file || p.path }
  isEditingProject.value = true
  yamlError.value = null
  showComposeModal.value = true 
  handleYamlInput(currentProject.value.content)
}

const saveProject = async () => { 
  if (!currentProject.value.name.trim()) {
    message.error('请输入项目名称')
    return
  }

  const savePath = isEditingProject.value ? currentProject.value.path : finalSavePath.value
  
  try {
    await axios.post(`/api/docker/compose/${props.hostId}/projects`, 
      { name: currentProject.value.name, content: currentProject.value.content },
      { params: { path: savePath } }
    )
    message.success('保存成功')
    
    // 记忆路径
    if (!isEditingProject.value) {
      localStorage.setItem(storageKey.value, baseSavePath.value)
    }

    showComposeModal.value = false
    fetchProjects(true) 
    // 自动扫描新路径
    if (!isEditingProject.value) pinProject({ path: savePath.substring(0, savePath.lastIndexOf('/')) })
  } catch (e) {
    message.error('保存失败')
  }
}

const deleteProject = (p: any) => {
  const deleteFiles = ref(false)
  
  dialog.error({
    title: '移除项目',
    content: () => h('div', null, [
      h('p', null, `确定要从视图中移除项目 ${p.name} 吗？`),
      h(NCheckbox, {
        checked: deleteFiles.value,
        'onUpdate:checked': (val) => deleteFiles.value = val,
        style: 'margin-top: 10px; color: #ff4d4f'
      }, { default: () => '同时彻底删除磁盘上的文件夹及 YML 文件' })
    ]),
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await axios.delete(`/api/docker/compose/${props.hostId}/projects/${p.name}`, { 
          params: { 
            path: p.config_file || p.path,
            delete_files: deleteFiles.value
          } 
        })
        message.success(deleteFiles.value ? '项目及文件已删除' : '项目已从视图移除')
        fetchProjects(true)
      } catch (e) {
        message.error('操作失败: ' + (e.response?.data?.detail || '未知错误'))
      }
    }
  })
}

const runComposeAction = async (p: any, action: string) => {
  loadingActions.value[p.name] = true
  try {
    const res = await axios.post(`/api/docker/compose/${props.hostId}/projects/${p.name}/action`, { action, path: p.config_file || p.path })
    
    if (res.data.success) {
      const noise = ['Started', 'Stopped', 'Stopping', 'Removing', 'Removed', 'Network', 'default']
      const stderr = res.data.stderr || ''
      const isNoise = noise.some(n => stderr.includes(n))
      
      const hasRealOutput = res.data.stdout?.trim() || (stderr.trim() && !isNoise)
      
      if (!hasRealOutput) {
        message.success('操作成功')
      } else {
        commandResult.value = { stdout: res.data.stdout, stderr: res.data.stderr }
        showCommandResult.value = true
      }
    } else {
      commandResult.value = { stdout: res.data.stdout, stderr: res.data.stderr }
      showCommandResult.value = true
      message.error('操作异常')
    }
    emit('refresh-containers')
  } catch (e) {
    message.error('请求失败')
  } finally {
    loadingActions.value[p.name] = false
    fetchProjects(true)
  }
}

const pinProject = async (p: any) => {
  const currentHost = props.hosts.find(h => h.id === props.hostId)
  if (!currentHost) return
  const path = p.path.replace(/.+$/, '')
  const pathList = (currentHost.compose_scan_paths || '').split(',').map((i: string) => i.trim()).filter((i: string) => i)
  if (!pathList.includes(path)) {
    pathList.push(path)
    currentHost.compose_scan_paths = pathList.join(',')
    await axios.put(`/api/docker/hosts/${props.hostId}`, currentHost)
    message.success('项目路径已记忆')
    fetchProjects(true)
    emit('refresh-hosts')
  }
}

defineExpose({ refresh: fetchProjects })
</script>