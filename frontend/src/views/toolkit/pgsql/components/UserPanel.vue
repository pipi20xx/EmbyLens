<template>
  <n-space vertical>
    <n-space justify="space-between" align="center">
      <n-button type="primary" @click="showCreateModal = true">创建用户</n-button>
      <n-button @click="fetchUsers" :loading="loading">刷新列表</n-button>
    </n-space>
    <n-data-table :columns="columns" :data="userList" :loading="loading" />

    <!-- 创建模态框 -->
    <n-modal v-model:show="showCreateModal" preset="card" title="创建数据库用户/角色" style="width: 550px">
      <n-form label-placement="left" label-width="120">
        <n-form-item label="用户名/角色名">
          <n-input v-model:value="form.username" placeholder="请输入名称" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="form.password" type="password" placeholder="请输入密码" />
        </n-form-item>
        <n-form-item label="连接限制">
          <n-input-number v-model:value="form.connection_limit" :min="-1" style="width: 100%" />
          <template #feedback>输入 -1 表示无限制</template>
        </n-form-item>
        <n-divider title-placement="left">权限设置</n-divider>
        <n-grid :cols="2" :x-gap="12">
          <n-gi><n-checkbox v-model:checked="form.can_login">允许登录 (LOGIN)</n-checkbox></n-gi>
          <n-gi><n-checkbox v-model:checked="form.is_superuser">超级用户 (SUPERUSER)</n-checkbox></n-gi>
          <n-gi><n-checkbox v-model:checked="form.can_create_db">创建数据库 (CREATEDB)</n-checkbox></n-gi>
          <n-gi><n-checkbox v-model:checked="form.can_create_role">创建角色 (CREATEROLE)</n-checkbox></n-gi>
          <n-gi><n-checkbox v-model:checked="form.inherit">继承权限 (INHERIT)</n-checkbox></n-gi>
          <n-gi><n-checkbox v-model:checked="form.replication">流复制 (REPLICATION)</n-checkbox></n-gi>
          <n-gi :span="2"><n-checkbox v-model:checked="form.bypass_rls">绕过 RLS (BYPASSRLS)</n-checkbox></n-gi>
        </n-grid>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="handleCreate" :loading="creating">创建角色</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 编辑模态框 -->
    <n-modal v-model:show="showEditModal" preset="card" :title="`修改角色属性: ${editingUser?.username}`" style="width: 550px">
      <n-form label-placement="left" label-width="120">
        <n-form-item label="重置密码">
          <n-input v-model:value="editForm.password" type="password" placeholder="留空则不修改" />
        </n-form-item>
        <n-form-item label="到期时间">
          <n-date-picker v-model:formatted-value="editForm.valid_until" value-format="yyyy-MM-dd HH:mm:ss" type="datetime" clearable style="width: 100%" />
        </n-form-item>
        <n-form-item label="连接限制">
          <n-input-number v-model:value="editForm.connection_limit" :min="-1" style="width: 100%" />
        </n-form-item>
        <n-divider title-placement="left">权限设置</n-divider>
        <n-grid :cols="2" :x-gap="12">
          <n-gi><n-checkbox v-model:checked="editForm.can_login">允许登录 (LOGIN)</n-checkbox></n-gi>
          <n-gi><n-checkbox v-model:checked="editForm.is_superuser">超级用户 (SUPERUSER)</n-checkbox></n-gi>
          <n-gi><n-checkbox v-model:checked="editForm.can_create_db">创建数据库 (CREATEDB)</n-checkbox></n-gi>
          <n-gi><n-checkbox v-model:checked="editForm.can_create_role">创建角色 (CREATEROLE)</n-checkbox></n-gi>
          <n-gi><n-checkbox v-model:checked="editForm.inherit">继承权限 (INHERIT)</n-checkbox></n-gi>
          <n-gi><n-checkbox v-model:checked="editForm.replication">流复制 (REPLICATION)</n-checkbox></n-gi>
          <n-gi :span="2"><n-checkbox v-model:checked="editForm.bypass_rls">绕过 RLS (BYPASSRLS)</n-checkbox></n-gi>
        </n-grid>
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
import { ref, watch, reactive, h } from 'vue'
import { NSpace, NButton, NDataTable, NModal, NForm, NFormItem, NInput, NCheckbox, NIcon, NDatePicker, NInputNumber, NGrid, NGi, NDivider, useMessage, useDialog } from 'naive-ui'
import { CheckCircleOutlined as SuccessIcon } from '@vicons/material'
import axios from 'axios'

const props = defineProps<{ host: any }>()
const message = useMessage()
const dialog = useDialog()

const userList = ref<any[]>([])
const loading = ref(false)

// 创建逻辑
const creating = ref(false)
const showCreateModal = ref(false)
const form = reactive({
  username: '',
  password: '',
  can_login: true,
  is_superuser: false,
  can_create_db: false,
  can_create_role: false,
  inherit: true,
  replication: false,
  bypass_rls: false,
  connection_limit: -1
})

// 编辑逻辑
const showEditModal = ref(false)
const updating = ref(false)
const editingUser = ref<any>(null)
const editForm = reactive({
  password: '',
  can_login: true,
  is_superuser: false,
  can_create_db: false,
  can_create_role: false,
  inherit: true,
  replication: false,
  bypass_rls: false,
  connection_limit: -1,
  valid_until: null as string | null
})

const columns = [
  { title: '角色名/用户名', key: 'username' },
  { 
    title: '允许登录', 
    key: 'can_login', 
    render: (row: any) => row.can_login ? 'YES' : 'NO' 
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: any) => h(NSpace, {}, {
      default: () => [
        h(NButton, { size: 'small', secondary: true, type: 'info', onClick: () => openEditModal(row) }, { default: () => '属性' }),
        h(NButton, { size: 'small', type: 'error', ghost: true, onClick: () => handleDrop(row.username) }, { default: () => '删除' })
      ]
    })
  }
]

const fetchUsers = async () => {
  if (!props.host) return
  loading.value = true
  try {
    const res = await axios.post('/api/pgsql/users', props.host)
    userList.value = res.data
  } catch (e) {}
  finally { loading.value = false }
}

const openEditModal = (row: any) => {
  editingUser.value = row
  editForm.password = ''
  editForm.can_login = row.can_login
  editForm.is_superuser = row.is_superuser
  editForm.can_create_db = row.can_create_db
  editForm.can_create_role = row.can_create_role
  editForm.inherit = row.inherit
  editForm.replication = row.replication
  editForm.bypass_rls = row.bypass_rls
  editForm.connection_limit = row.connection_limit
  editForm.valid_until = row.valid_until
  showEditModal.value = true
}

const handleUpdate = async () => {
  if (!editingUser.value) return
  updating.value = true
  try {
    await axios({
      method: 'patch',
      url: `/api/pgsql/users/${editingUser.value.username}`,
      data: {
        config: props.host,
        req: { ...editForm, password: editForm.password || null }
      }
    })
    message.success('更新成功')
    showEditModal.value = false
    fetchUsers()
  } catch (e: any) { message.error('更新失败') }
  finally { updating.value = false }
}

const handleCreate = async () => {
  if (!form.username) return
  creating.value = true
  try {
    await axios.post('/api/pgsql/users/create', {
      config: props.host,
      req: form
    })
    message.success('创建角色成功')
    showCreateModal.value = false
    Object.assign(form, { username: '', password: '', can_login: true, is_superuser: false, can_create_db: false, can_create_role: false, inherit: true, replication: false, bypass_rls: false, connection_limit: -1 })
    fetchUsers()
  } catch (e: any) { message.error('失败: ' + (e.response?.data?.detail || e.message)) }
  finally { creating.value = false }
}

const handleDrop = (username: string) => {
  dialog.warning({
    title: '删除角色',
    content: `确定要删除角色 "${username}" 吗？`,
    onPositiveClick: async () => {
      await axios.delete(`/api/pgsql/users/${username}`, { data: props.host })
      message.success('已删除')
      fetchUsers()
    }
  })
}

watch(() => props.host, fetchUsers, { immediate: true })
defineExpose({ refresh: fetchUsers })
</script>
