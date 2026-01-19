<template>
  <div class="compose-panel">
    <n-space vertical size="medium">
      <n-space justify="end" v-if="hostId">
        <n-button type="primary" @click="handleCreateProject">新建项目</n-button>
      </n-space>
      
      <n-grid :cols="3" :x-gap="12" :y-gap="12">
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
                <n-button size="tiny" circle quaternary @click="$emit('browse-path', p.path)" title="浏览目录">
                  <template #icon><n-icon><folder-icon /></n-icon></template>
                </n-button>
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

        <n-form-item label="YAML 内容">
          <n-input
            v-model:value="currentProject.content"
            type="textarea"
            placeholder="在此输入 docker-compose.yml 内容"
            :autosize="{ minRows: 12, maxRows: 20 }"
            style="font-family: monospace"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showComposeModal = false">取消</n-button>
          <n-button type="primary" @click="saveProject">保存项目</n-button>
        </n-space>
      </template>
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
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, h } from 'vue'
import { NSpace, NButton, NGrid, NGi, NCard, NTag, NIcon, NText, NEllipsis, NModal, NForm, NFormItem, NInput, NInputGroup, NCheckbox, useMessage, useDialog } from 'naive-ui'
import { PushPinOutlined as PushPinIcon, FolderOutlined as FolderIcon } from '@vicons/material'
import axios from 'axios'

const props = defineProps({
  hostId: { type: String, default: null },
  hosts: { type: Array, default: [] },
  // 新增：外部传入的被选中路径，用于文件浏览器回调
  pickedPath: { type: String, default: '' }
})

const emit = defineEmits(['refresh-containers', 'refresh-hosts', 'browse-path', 'request-pick-path'])

const message = useMessage()
const dialog = useDialog()
const projects = ref<any[]>([])
const loadingActions = ref<Record<string, boolean>>({})
const showComposeModal = ref(false)
const showCommandResult = ref(false)
const commandResult = ref({ stdout: '', stderr: '' })
const currentProject = ref({ name: '', content: '', path: '' })
const isEditingProject = ref(false)

// 路径记忆逻辑
const baseSavePath = ref('/opt/docker-compose')
const storageKey = computed(() => `embylens_last_path_${props.hostId}`)

const loadLastPath = () => {
  const saved = localStorage.getItem(storageKey.value)
  if (saved) baseSavePath.value = saved
}

const finalSavePath = computed(() => {
  const base = baseSavePath.value.replace(/\/$/, '')
  const name = currentProject.value.name.trim() || 'project_name'
  return `${base}/${name}/docker-compose.yml`
})

const fetchProjects = async () => {
  if (!props.hostId) return
  const res = await axios.get(`/api/docker/compose/${props.hostId}/projects`)
  projects.value = res.data
}

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

const handleCreateProject = () => { 
  currentProject.value = { 
    name: '', 
    content: `version: "3.8"\nservices:\n  app:\n    image: `,
    path: '' 
  }
  isEditingProject.value = false
  loadLastPath()
  showComposeModal.value = true 
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
  showComposeModal.value = true 
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
    fetchProjects() 
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
        fetchProjects()
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
    commandResult.value = { stdout: res.data.stdout, stderr: res.data.stderr }
    showCommandResult.value = true
    emit('refresh-containers')
  } finally {
    loadingActions.value[p.name] = false
    fetchProjects()
  }
}

const pinProject = async (p: any) => {
  const currentHost = props.hosts.find(h => h.id === props.hostId)
  if (!currentHost) return
  const path = p.path.replace(/\/$/, '')
  const pathList = (currentHost.compose_scan_paths || '').split(',').map((i: string) => i.trim()).filter((i: string) => i)
  if (!pathList.includes(path)) {
    pathList.push(path)
    currentHost.compose_scan_paths = pathList.join(',')
    await axios.put(`/api/docker/hosts/${props.hostId}`, currentHost)
    message.success('项目路径已记忆')
    fetchProjects()
    emit('refresh-hosts')
  }
}

defineExpose({ refresh: fetchProjects })
</script>
