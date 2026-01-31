<template>
  <div class="project-list">
    <n-space vertical>
      <n-space justify="space-between">
        <n-button type="primary" @click="openCreateModal">新建项目</n-button>
        <n-space>
          <n-button @click="fetchProjects">刷新列表</n-button>
          <n-button type="error" ghost @click="handleClearAllLogs">清空所有记录</n-button>
        </n-space>
      </n-space>

      <n-data-table
        :columns="columns"
        :data="projects"
        :loading="loading"
        :bordered="false"
        size="small"
        scroll-x="1200"
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

    <!-- 历史记录组件 -->
    <build-history 
      v-model:show="showHistory" 
      :project-id="selectedProjectId" 
      :project-name="selectedProjectName" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import {
  NSpace, NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSelect,
  NCheckbox, useMessage, useDialog, NTag, NCheckboxGroup, NInputGroup
} from 'naive-ui'
import { imageBuilderApi } from '@/api/imageBuilder'
import BuildHistory from './BuildHistory.vue'

// 导入提取的逻辑
import { useImageBuilder } from '../hooks/useImageBuilder'

const message = useMessage()
const dialog = useDialog()

const {
  projects, registries, hostOptions, proxyOptions, registryOptions, loading, projectTags,
  fetchProjects, fetchOptions, directBuild, handleClearAllLogs, deleteProject: performDelete
} = useImageBuilder()

const showModal = ref(false)
const editMode = ref(false)
const currentProjectId = ref('')
const selectedPlatforms = ref(['linux/amd64'])

const showHistory = ref(false)
const selectedProjectId = ref('')
const selectedProjectName = ref('')

const form = ref({
  name: '', host_id: null, build_context: '', dockerfile_path: 'Dockerfile',
  local_image_name: '', repo_image_name: '', platforms: 'linux/amd64',
  registry_id: null, proxy_id: null, no_cache: false, auto_cleanup: true
})

const columns = [
  { title: '项目名称', key: 'name', minWidth: 120 },
  { title: '目标仓库', key: 'registry_id', width: 150, render(row: any) {
    const reg = registries.value.find(r => r.id === row.registry_id)
    return reg ? h(NTag, { size: 'small', type: 'warning', ghost: true }, { default: () => reg.name }) : h('span', { style: 'color: #666' }, '默认仓库')
  }},
  { title: '远程镜像名', key: 'repo_image_name', minWidth: 180 },
  { title: '平台', key: 'platforms', width: 160, render(row: any) {
    return h(NSpace, { size: 'small' }, {
      default: () => (row.platforms || '').split(',').map((p: string) => h(NTag, { size: 'small', type: 'info', ghost: true }, { default: () => p }))
    })
  }},
  {
    title: '操作',
    key: 'actions',
    width: 420,
    fixed: 'right',
    render(row: any) {
      if (!projectTags[row.id]) projectTags[row.id] = 'latest'
      return h(NSpace, { align: 'center', wrap: false }, {
        default: () => [
          h(NInputGroup, null, {
            default: () => [
              h(NInput, {
                size: 'small', value: projectTags[row.id], placeholder: 'Tag', style: { width: '100px' },
                'onUpdate:value': (v) => { projectTags[row.id] = v }
              }),
              h(NButton, { size: 'small', type: 'primary', onClick: () => directBuild(row) }, { default: () => '构建' })
            ]
          }),
          h(NButton, { size: 'small', onClick: () => openHistory(row) }, { default: () => '历史' }),
          h(NButton, { size: 'small', onClick: () => openEditModal(row) }, { default: () => '编辑' }),
          h(NButton, { size: 'small', type: 'error', ghost: true, onClick: () => deleteProject(row) }, { default: () => '删除' }),
        ]
      })
    }
  }
]

const openCreateModal = () => {
  editMode.value = false
  selectedPlatforms.value = ['linux/amd64']
  form.value = {
    name: '', host_id: hostOptions.value.length > 0 ? hostOptions.value[0].value : null,
    build_context: '', dockerfile_path: 'Dockerfile', local_image_name: '', repo_image_name: '',
    platforms: 'linux/amd64', registry_id: null, proxy_id: null, no_cache: false, auto_cleanup: true
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
    if (editMode.value) { await imageBuilderApi.updateProject(currentProjectId.value, form.value) }
    else { await imageBuilderApi.addProject(form.value) }
    message.success('保存成功')
    showModal.value = false
    fetchProjects()
  } catch (e) { message.error('保存失败') }
}

const deleteProject = (row: any) => {
  performDelete(row, fetchProjects)
}

const openHistory = (row: any) => {
  selectedProjectId.value = row.id
  selectedProjectName.value = row.name
  showHistory.value = true
}

onMounted(() => { fetchProjects(); fetchOptions() })
</script>