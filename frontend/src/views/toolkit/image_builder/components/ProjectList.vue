<template>
  <div class="project-list">
    <n-space vertical>
      <n-space justify="space-between">
        <n-button type="primary" @click="openCreateModal">新建项目</n-button>
        <n-button @click="fetchProjects">刷新列表</n-button>
      </n-space>

      <n-data-table
        :columns="columns"
        :data="projects"
        :loading="loading"
        :bordered="false"
        size="small"
      />
    </n-space>

    <!-- 项目编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="card" :title="editMode ? '编辑项目' : '新建项目'" style="width: 600px">
      <n-form :model="form" label-placement="left" label-width="120" ref="formRef">
        <n-form-item label="项目名称" path="name" required>
          <n-input v-model:value="form.name" placeholder="例如: My App" />
        </n-form-item>
        <n-form-item label="构建主机" path="host_id">
          <n-select v-model:value="form.host_id" :options="hostOptions" placeholder="选择执行构建的服务器" />
        </n-form-item>
        <n-form-item label="构建上下文" path="build_context" required>
          <n-input v-model:value="form.build_context" placeholder="宿主机目录, 例如: /root/my-app" />
        </n-form-item>
        <n-form-item label="Dockerfile 路径" path="dockerfile_path" required>
          <n-input v-model:value="form.dockerfile_path" placeholder="相对于上下文的路径, 例如: Dockerfile" />
        </n-form-item>
        <n-form-item label="本地镜像名" path="local_image_name" required>
          <n-input v-model:value="form.local_image_name" placeholder="例如: my-app" />
        </n-form-item>
        <n-form-item label="远程镜像名" path="repo_image_name" required>
          <n-input v-model:value="form.repo_image_name" placeholder="例如: username/my-app" />
        </n-form-item>
        <n-form-item label="目标平台" path="platforms">
          <n-checkbox-group v-model:value="selectedPlatforms">
            <n-space item-style="display: flex;">
              <n-checkbox value="linux/amd64" label="amd64" />
              <n-checkbox value="linux/arm64" label="arm64" />
              <n-checkbox value="linux/arm/v7" label="arm/v7" />
              <n-checkbox value="linux/arm/v6" label="arm/v6" />
              <n-checkbox value="linux/386" label="386" />
            </n-space>
          </n-checkbox-group>
        </n-form-item>
        <n-form-item label="目标仓库" path="registry_id">
          <n-select v-model:value="form.registry_id" :options="registryOptions" clearable placeholder="选择推送仓库 (选填)" />
        </n-form-item>
        <n-form-item label="构建代理" path="proxy_id">
          <n-select v-model:value="form.proxy_id" :options="proxyOptions" clearable placeholder="选择代理 (选填)" />
        </n-form-item>
        <n-form-item label="构建选项">
          <n-space>
            <n-checkbox v-model:checked="form.no_cache">禁用缓存</n-checkbox>
            <n-checkbox v-model:checked="form.auto_cleanup">自动清理本地镜像</n-checkbox>
          </n-space>
        </n-form-item>

        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="saveProject">保存</n-button>
        </n-space>
      </n-form>
    </n-modal>

    <!-- 构建确认弹窗 -->
    <n-modal v-model:show="showBuildModal" preset="dialog" title="确认构建" positive-text="开始构建" negative-text="取消" @positive-click="startBuild">
      <n-form-item label="镜像标签 (Tag)">
        <n-input v-model:value="buildTag" placeholder="例如: latest, v1.0.0" />
      </n-form-item>
    </n-modal>

    <!-- 日志查看弹窗 -->
    <n-modal v-model:show="showLogModal" preset="card" title="构建日志" style="width: 900px">
      <div class="log-container">
        <pre v-if="taskLog">{{ taskLog }}</pre>
        <n-empty v-else description="无日志" />
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive } from 'vue'
import { 
  NSpace, NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSelect, 
  NCheckbox, useMessage, useDialog, NTag, NEmpty, NCheckboxGroup, NInputGroup 
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const dialog = useDialog()

const projects = ref([])
const registries = ref([])
const proxies = ref([])
const hostOptions = ref([])
const loading = ref(false)
const showModal = ref(false)
const editMode = ref(false)
const currentProjectId = ref('')

// 用于存储每个项目的构建 Tag 状态
const projectTags = reactive<Record<string, string>>({})

const selectedPlatforms = ref(['linux/amd64'])

const form = ref({
  name: '',
  host_id: null,
  build_context: '',
  dockerfile_path: 'Dockerfile',
  local_image_name: '',
  repo_image_name: '',
  platforms: 'linux/amd64',
  registry_id: null,
  proxy_id: null,
  no_cache: false,
  auto_cleanup: true
})

const registryOptions = ref([])
const proxyOptions = ref([])

const showLogModal = ref(false)
const taskLog = ref('')

const columns = [
  { title: '项目名称', key: 'name' },
  { title: '远程镜像名', key: 'repo_image_name' },
  { title: '平台', key: 'platforms', width: 180, render(row: any) {
    return h(NSpace, { size: 'small' }, { 
      default: () => row.platforms.split(',').map((p: string) => h(NTag, { size: 'small', type: 'info', ghost: true }, { default: () => p }))
    })
  }},
  {
    title: '操作',
    key: 'actions',
    width: 320,
    render(row: any) {
      if (!projectTags[row.id]) projectTags[row.id] = 'latest'
      
      return h(NSpace, { align: 'center' }, { 
        default: () => [
          h(NInputGroup, null, { 
            default: () => [
              h(NInput, {
                size: 'small',
                value: projectTags[row.id],
                placeholder: 'Tag (用 | 分隔)',
                style: { width: '120px' },
                'onUpdate:value': (v) => { projectTags[row.id] = v }
              }),
              h(NButton, {
                size: 'small',
                type: 'primary',
                onClick: () => directBuild(row)
              }, { default: () => '构建' })
            ]
          }),
          h(NButton, { size: 'small', onClick: () => viewLatestLog(row) }, { default: () => '日志' }),
          h(NButton, { size: 'small', onClick: () => openEditModal(row) }, { default: () => '编辑' }),
          h(NButton, { size: 'small', type: 'error', ghost: true, onClick: () => deleteProject(row) }, { default: () => '删除' }),
        ]
      })
    }
  }
]

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/image-builder/projects')
    projects.value = res.data
    // 初始化 Tag 状态
    res.data.forEach((p: any) => {
      if (!projectTags[p.id]) projectTags[p.id] = 'latest'
    })
  } catch (e) {
    message.error('获取项目列表失败')
  } finally {
    loading.value = false
  }
}

const fetchOptions = async () => {
  try {
    const [regRes, proxRes, hostRes] = await Promise.all([
      axios.get('/api/image-builder/registries'),
      axios.get('/api/image-builder/proxies'),
      axios.get('/api/docker/hosts')
    ])
    registryOptions.value = regRes.data.map((r: any) => ({ label: r.name, value: r.id }))
    proxyOptions.value = proxRes.data.map((p: any) => ({ label: p.name, value: p.id }))
    hostOptions.value = hostRes.data.map((h: any) => ({ label: h.name, value: h.id }))
  } catch (e) {}
}

const openCreateModal = () => {
  editMode.value = false
  selectedPlatforms.value = ['linux/amd64']
  form.value = {
    name: '',
    host_id: hostOptions.value.length > 0 ? hostOptions.value[0].value : null,
    build_context: '',
    dockerfile_path: 'Dockerfile',
    local_image_name: '',
    repo_image_name: '',
    platforms: 'linux/amd64',
    registry_id: null,
    proxy_id: null,
    no_cache: false,
    auto_cleanup: true
  }
  showModal.value = true
}

const openEditModal = (row: any) => {
  editMode.value = true
  currentProjectId.value = row.id
  form.value = { ...row }
  selectedPlatforms.value = row.platforms ? row.platforms.split(',') : ['linux/amd64']
  showModal.value = true
}

const saveProject = async () => {
  form.value.platforms = selectedPlatforms.value.join(',')
  try {
    if (editMode.value) {
      await axios.put(`/api/image-builder/projects/${currentProjectId.value}`, form.value)
      message.success('更新成功')
    } else {
      await axios.post('/api/image-builder/projects', form.value)
      message.success('创建成功')
    }
    showModal.value = false
    fetchProjects()
  } catch (e) {
    message.error('保存失败')
  }
}

const deleteProject = (row: any) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除项目 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await axios.delete(`/api/image-builder/projects/${row.id}`)
        message.success('已删除')
        fetchProjects()
      } catch (e) {
        message.error('删除失败')
      }
    }
  })
}

const directBuild = async (row: any) => {
  const tag = projectTags[row.id] || 'latest'
  try {
    const res = await axios.post(`/api/image-builder/projects/${row.id}/build`, {
      tag: tag
    })
    message.success(`构建任务 [${tag}] 已启动`)
    pollLog(res.data.task_id)
  } catch (e) {
    message.error('启动构建失败')
  }
}

const viewLatestLog = async (row: any) => {
  try {
    const tasksRes = await axios.get(`/api/image-builder/projects/${row.id}/tasks`)
    if (tasksRes.data.length === 0) {
      message.info('该项目暂无构建记录')
      return
    }
    const latestTask = tasksRes.data[0]
    const logRes = await axios.get(`/api/image-builder/tasks/${latestTask.id}/log`)
    taskLog.value = logRes.data.content
    showLogModal.value = true
  } catch (e) {
    message.error('获取日志失败')
  }
}

const pollLog = async (taskId: string) => {
  showLogModal.value = true
  taskLog.value = '正在获取实时日志...\n'
  
  const timer = setInterval(async () => {
    if (!showLogModal.value) {
      clearInterval(timer)
      return
    }
    try {
      const logRes = await axios.get(`/api/image-builder/tasks/${taskId}/log`)
      taskLog.value = logRes.data.content
      if (taskLog.value.includes('--- TASK_COMPLETED ---')) {
        clearInterval(timer)
      }
    } catch (e) {
      clearInterval(timer)
    }
  }, 2000)
}

onMounted(() => {
  fetchProjects()
  fetchOptions()
})
</script>

<style scoped>
.log-container {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 4px;
  max-height: 600px;
  overflow-y: auto;
  font-family: monospace;
  white-space: pre-wrap;
}
</style>