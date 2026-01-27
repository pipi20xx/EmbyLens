<template>
  <div class="registry-manager">
    <n-grid :cols="2" :x-gap="12">
      <n-gi>
        <n-card title="仓库配置" size="small">
          <template #header-extra>
            <n-button size="small" type="primary" @click="showRegistryModal = true">添加仓库</n-button>
          </template>
          <n-data-table :columns="registryColumns" :data="registries" size="small" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="凭据管理" size="small">
          <template #header-extra>
            <n-button size="small" type="primary" @click="showCredModal = true">添加凭据</n-button>
          </template>
          <n-data-table :columns="credColumns" :data="credentials" size="small" />
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Registry Modal -->
    <n-modal v-model:show="showRegistryModal" preset="card" title="添加仓库" style="width: 450px">
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
    <n-modal v-model:show="showCredModal" preset="card" title="添加凭据" style="width: 450px">
      <n-form :model="credForm" label-placement="left" label-width="100">
        <n-form-item label="名称">
          <n-input v-model:value="credForm.name" placeholder="例如: my-docker-hub-login" />
        </n-form-item>
        <n-form-item label="用户名">
          <n-input v-model:value="credForm.username" />
        </n-form-item>
        <n-form-item label="密码/Token">
          <n-input v-model:value="credForm.password" type="password" show-password-on="click" />
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
  NInput, NSelect, NSwitch, NSpace, useMessage 
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()

const registries = ref([])
const credentials = ref([])
const showRegistryModal = ref(false)
const showCredModal = ref(false)

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
      return h(NButton, { size: 'small', type: 'error', ghost: true, onClick: () => deleteRegistry(row.id) }, { default: () => '删除' })
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
      return h(NButton, { size: 'small', type: 'error', ghost: true, onClick: () => deleteCredential(row.id) }, { default: () => '删除' })
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

const saveRegistry = async () => {
  try {
    await axios.post('/api/image-builder/registries', registryForm.value)
    message.success('已保存')
    showRegistryModal.value = false
    fetchData()
  } catch (e) {
    message.error('保存失败')
  }
}

const saveCredential = async () => {
  try {
    await axios.post('/api/image-builder/credentials', credForm.value)
    message.success('已保存')
    showCredModal.value = false
    fetchData()
  } catch (e) {
    message.error('保存失败')
  }
}

const deleteRegistry = async (id: string) => {
  try {
    await axios.delete(`/api/image-builder/registries/${id}`)
    fetchData()
  } catch (e) {}
}

const deleteCredential = async (id: string) => {
  try {
    await axios.delete(`/api/image-builder/credentials/${id}`)
    fetchData()
  } catch (e) {}
}

onMounted(fetchData)
</script>
