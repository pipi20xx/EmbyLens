<template>
  <n-space vertical>
    <n-space justify="space-between" align="center">
      <n-button type="primary" @click="showCreateModal = true">创建数据库</n-button>
      <n-button @click="fetchDatabases" :loading="loading">刷新列表</n-button>
    </n-space>
    <n-data-table :columns="columns" :data="dbList" :loading="loading" />

    <!-- 创建模态框 -->
    <n-modal v-model:show="showCreateModal" preset="card" title="创建数据库" style="width: 450px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="数据库名称">
          <n-input v-model:value="newDbName" placeholder="请输入库名" />
        </n-form-item>
        <n-form-item label="所有者">
          <n-select v-model:value="newDbOwner" :options="userOptions" placeholder="选择所有者 (可选)" clearable />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="handleCreate" :loading="creating">创建</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 编辑模态框 -->
    <n-modal v-model:show="showEditModal" preset="card" :title="`管理数据库: ${editingDb?.name}`" style="width: 500px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="所有者">
          <n-select v-model:value="editForm.owner" :options="userOptions" placeholder="选择新所有者" />
        </n-form-item>
        <n-form-item label="备注/描述">
          <n-input
            v-model:value="editForm.description"
            type="textarea"
            placeholder="为数据库添加描述信息..."
            :autosize="{ minRows: 3 }"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" @click="handleUpdate" :loading="updating">保存修改</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, watch, reactive, h, computed } from 'vue'
import { NSpace, NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSelect, useMessage, useDialog } from 'naive-ui'
import axios from 'axios'

const props = defineProps<{ host: any }>()
const message = useMessage()
const dialog = useDialog()

const dbList = ref<any[]>([])
const userList = ref<any[]>([])
const loading = ref(false)

// 创建逻辑
const showCreateModal = ref(false)
const newDbName = ref('')
const newDbOwner = ref<string | null>(null)
const creating = ref(false)

// 监听创建弹窗打开，刷新用户列表
watch(showCreateModal, (val) => {
  if (val) fetchUsers()
})

// 编辑逻辑
const showEditModal = ref(false)
const updating = ref(false)
const editingDb = ref<any>(null)
const editForm = reactive({
  owner: '',
  description: ''
})

const userOptions = computed(() => userList.value.map(u => ({ label: u.username, value: u.username })))

const columns = [
  { title: '数据库名称', key: 'name', width: 150 },
  { title: '所有者', key: 'owner', width: 120 },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    render: (row: any) => h(NSpace, {}, {
      default: () => [
        h(NButton, {
          size: 'small',
          secondary: true,
          type: 'info',
          onClick: () => openEditModal(row)
        }, { default: () => '属性' }),
        h(NButton, {
          size: 'small',
          type: 'error',
          ghost: true,
          onClick: () => handleDrop(row.name)
        }, { default: () => '删除' })
      ]
    })
  }
]

const fetchDatabases = async () => {
  if (!props.host) return
  loading.value = true
  try {
    const res = await axios.post('/api/pgsql/databases', props.host)
    dbList.value = res.data
  } catch (e) {}
  finally { loading.value = false }
}

const fetchUsers = async () => {
  if (!props.host) return
  try {
    const res = await axios.post('/api/pgsql/users', props.host)
    userList.value = res.data
  } catch (e) {}
}

const openEditModal = (row: any) => {
  editingDb.value = row
  editForm.owner = row.owner
  editForm.description = row.description || ''
  showEditModal.value = true
  fetchUsers() // 弹出时同步刷新用户列表以供选择
}

const handleUpdate = async () => {
  if (!editingDb.value) return
  updating.value = true
  try {
    await axios({
      method: 'patch',
      url: `/api/pgsql/databases/${editingDb.value.name}`,
      data: {
        config: props.host,
        req: { owner: editForm.owner, description: editForm.description }
      }
    })
    message.success('更新成功')
    showEditModal.value = false
    fetchDatabases()
  } catch (e: any) {
    message.error('更新失败: ' + (e.response?.data?.detail || e.message))
  } finally { updating.value = false }
}

const handleCreate = async () => {
  if (!newDbName.value) return
  creating.value = true
  try {
    await axios.post('/api/pgsql/databases/create', {
      config: props.host,
      req: { 
        dbname: newDbName.value,
        owner: newDbOwner.value
      }
    })
    message.success('创建成功')
    showCreateModal.value = false
    newDbName.value = ''
    newDbOwner.value = null
    fetchDatabases()
  } catch (e: any) {
    message.error('失败: ' + (e.response?.data?.detail || e.message))
  } finally { creating.value = false }
}

const handleDrop = (name: string) => {
  dialog.error({
    title: '危险操作',
    content: `确定要永久删除数据库 "${name}" 吗？系统将强制终止活跃连接。`,
    positiveText: '确认删除',
    onPositiveClick: async () => {
      try {
        await axios.delete(`/api/pgsql/databases/${name}`, { data: props.host })
        message.success('已删除')
        fetchDatabases()
      } catch (e: any) {
        message.error('删除失败')
      }
    }
  })
}

watch(() => props.host, fetchDatabases, { immediate: true })
defineExpose({ refresh: fetchDatabases })
</script>