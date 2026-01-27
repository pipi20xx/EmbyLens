<template>
  <div class="registry-manager">
    <n-grid :cols="2" :x-gap="12">
      <n-gi>
        <n-card title="仓库配置" size="small">
          <template #header-extra>
            <n-button size="small" type="primary" @click="openRegistryModal()">添加仓库</n-button>
          </template>
          <n-data-table :columns="registryColumns" :data="registries" size="small" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="凭据管理" size="small">
          <template #header-extra>
            <n-button size="small" type="primary" @click="openCredModal()">添加凭据</n-button>
          </template>
          <n-data-table :columns="credColumns" :data="credentials" size="small" />
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Registry Modal -->
    <n-modal v-model:show="showRegistryModal" preset="card" :title="editRegistryMode ? '编辑仓库' : '添加仓库'" style="width: 450px">
      <n-form :model="registryForm" label-placement="left" label-width="100">
        <n-form-item label="名称">
          <n-input v-model:value="registryForm.name" placeholder="例如: Docker Hub" />
        </n-form-item>
        <n-form-item label="URL">
          <n-input v-model:value="registryForm.url" placeholder="例如: docker.io" />
        </n-form-item>
        <n-form-item label="HTTPS">
          <n-switch v-model:value="registryForm.is_https" />
        </n-form-item>
        <n-form-item label="关联凭据">
          <n-select v-model:value="registryForm.credential_id" :options="credOptions" clearable />
        </n-form-item>
        <n-space justify="end">
          <n-button @click="showRegistryModal = false">取消</n-button>
          <n-button type="primary" @click="saveRegistry">保存</n-button>
        </n-space>
      </n-form>
    </n-modal>

    <!-- Credential Modal -->
    <n-modal v-model:show="showCredModal" preset="card" :title="editCredMode ? '编辑凭据' : '添加凭据'" style="width: 450px">
      <n-form :model="credForm" label-placement="left" label-width="100">
        <n-form-item label="名称">
          <n-input v-model:value="credForm.name" placeholder="例如: my-docker-hub-login" />
        </n-form-item>
        <n-form-item label="用户名">
          <n-input v-model:value="credForm.username" />
        </n-form-item>
        <n-form-item label="密码/Token">
          <n-input v-model:value="credForm.password" type="password" show-password-on="click" :placeholder="editCredMode ? '留空表示不修改' : ''" />
        </n-form-item>
        <n-space justify="end">
          <n-button @click="showCredModal = false">取消</n-button>
          <n-button type="primary" @click="saveCredential">保存</n-button>
        </n-space>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { 
  NGrid, NGi, NCard, NButton, NDataTable, NModal, NForm, NFormItem, 
  NInput, NSelect, NSwitch, NSpace, useMessage, useDialog 
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const dialog = useDialog()

const registries = ref([])
const credentials = ref([])
const showRegistryModal = ref(false)
const showCredModal = ref(false)
const editRegistryMode = ref(false)
const editCredMode = ref(false)
const currentRegistryId = ref('')
const currentCredId = ref('')
const testingId = ref('')

const registryForm = ref({
  name: '',
  url: '',
  is_https: true,
  credential_id: null
})

const credForm = ref({
  name: '',
  username: '',
  password: ''
})

const credOptions = ref([])

const registryColumns = [
  { title: '名称', key: 'name' },
  { title: 'URL', key: 'url' },
  {
    title: '操作',
    key: 'actions',
    render(row: any) {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { 
            size: 'small', 
            type: 'info', 
            ghost: true,
            loading: testingId.value === row.id,
            onClick: () => testRegistry(row) 
          }, { default: () => '测试' }),
          h(NButton, { size: 'small', onClick: () => openRegistryModal(row) }, { default: () => '编辑' }),
          h(NButton, { size: 'small', type: 'error', ghost: true, onClick: () => deleteRegistry(row.id) }, { default: () => '删除' })
        ]
      })
    }
  }
]

const credColumns = [
  { title: '名称', key: 'name' },
  { title: '用户名', key: 'username' },
  {
    title: '操作',
    key: 'actions',
    render(row: any) {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { size: 'small', onClick: () => openCredModal(row) }, { default: () => '编辑' }),
          h(NButton, { size: 'small', type: 'error', ghost: true, onClick: () => deleteCredential(row.id) }, { default: () => '删除' })
        ]
      })
    }
  }
]

const fetchData = async () => {
  try {
    const [regRes, credRes] = await Promise.all([
      axios.get('/api/image-builder/registries'),
      axios.get('/api/image-builder/credentials')
    ])
    registries.value = regRes.data
    credentials.value = credRes.data
    credOptions.value = credentials.value.map((c: any) => ({ label: c.name, value: c.id }))
  } catch (e) {}
}

const openRegistryModal = (row: any = null) => {
  if (row) {
    editRegistryMode.value = true
    currentRegistryId.value = row.id
    registryForm.value = { ...row }
  } else {
    editRegistryMode.value = false
    registryForm.value = { name: '', url: '', is_https: true, credential_id: null }
  }
  showRegistryModal.value = true
}

const openCredModal = (row: any = null) => {
  if (row) {
    editCredMode.value = true
    currentCredId.value = row.id
    credForm.value = { name: row.name, username: row.username, password: '' }
  } else {
    editCredMode.value = false
    credForm.value = { name: '', username: '', password: '' }
  }
  showCredModal.value = true
}

const saveRegistry = async () => {
  try {
    if (editRegistryMode.value) {
      await axios.put(`/api/image-builder/registries/${currentRegistryId.value}`, registryForm.value)
    } else {
      await axios.post('/api/image-builder/registries', registryForm.value)
    }
    message.success('已保存')
    showRegistryModal.value = false
    fetchData()
  } catch (e) {
    message.error('保存失败')
  }
}

const saveCredential = async () => {
  try {
    if (editCredMode.value) {
      await axios.put(`/api/image-builder/credentials/${currentCredId.value}`, credForm.value)
    } else {
      await axios.post('/api/image-builder/credentials', credForm.value)
    }
    message.success('已保存')
    showCredModal.value = false
    fetchData()
  } catch (e) {
    message.error('保存失败')
  }
}

const testRegistry = async (row: any) => {
  testingId.value = row.id
  try {
    const res = await axios.post(`/api/image-builder/registries/${row.id}/test`)
    if (res.data.success) {
      message.success(res.data.message)
    } else {
      message.error(res.data.message)
    }
  } catch (e) {
    message.error('测试请求失败')
  } finally {
    testingId.value = ''
  }
}

const deleteRegistry = async (id: string) => {
  dialog.warning({
    title: '确认删除',
    content: '删除仓库配置可能导致关联的构建任务失败，是否继续？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await axios.delete(`/api/image-builder/registries/${id}`)
        fetchData()
      } catch (e) {}
    }
  })
}

const deleteCredential = async (id: string) => {
  dialog.warning({
    title: '确认删除',
    content: '删除凭据将导致所有使用该凭据的仓库无法登录，是否继续？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await axios.delete(`/api/image-builder/credentials/${id}`)
        fetchData()
      } catch (e) {}
    }
  })
}

onMounted(fetchData)
</script>
