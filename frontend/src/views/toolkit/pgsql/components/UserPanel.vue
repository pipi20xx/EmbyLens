<template>
  <n-space vertical>
    <n-space justify="space-between" align="center">
      <n-button type="primary" @click="showCreateModal = true">创建用户</n-button>
      <n-button @click="fetchUsers" :loading="loading">刷新列表</n-button>
    </n-space>
    <n-data-table :columns="columns" :data="userList" :loading="loading" />

    <n-modal v-model:show="showCreateModal" preset="card" title="创建数据库用户" style="width: 400px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="用户名">
          <n-input v-model:value="form.username" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="form.password" type="password" />
        </n-form-item>
        <n-form-item label="超级用户">
          <n-checkbox v-model:checked="form.is_superuser">SUPERUSER</n-checkbox>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="handleCreate" :loading="creating">创建</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, watch, reactive, h } from 'vue'
import { NSpace, NButton, NDataTable, NModal, NForm, NFormItem, NInput, NCheckbox, NIcon, useMessage, useDialog } from 'naive-ui'
import { CheckCircleOutlined as SuccessIcon } from '@vicons/material'
import axios from 'axios'

const props = defineProps<{ host: any }>()
const message = useMessage()
const dialog = useDialog()

const userList = ref<any[]>([])
const loading = ref(false)
const creating = ref(false)
const showCreateModal = ref(false)

const form = reactive({
  username: '',
  password: '',
  is_superuser: false
})

const columns = [
  { title: '用户名', key: 'username' },
  { 
    title: '超级用户', 
    key: 'is_superuser', 
    render: (row: any) => row.is_superuser ? h(NIcon, { color: '#18a058' }, { default: () => h(SuccessIcon) }) : '否' 
  },
  { title: '建库权限', key: 'can_create_db', render: (row: any) => row.can_create_db ? '是' : '否' },
  {
    title: '操作',
    key: 'actions',
    render: (row: any) => h(
      NButton,
      {
        size: 'small',
        type: 'error',
        ghost: true,
        onClick: () => handleDrop(row.username)
      },
      { default: () => '删除' }
    )
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

const handleCreate = async () => {
  if (!form.username) return
  creating.value = true
  try {
    await axios.post('/api/pgsql/users/create', {
      config: props.host,
      req: form
    })
    message.success('创建成功')
    showCreateModal.value = false
    Object.assign(form, { username: '', password: '', is_superuser: false })
    fetchUsers()
  } catch (e: any) {
    message.error('失败: ' + (e.response?.data?.detail || e.message))
  } finally { creating.value = false }
}

const handleDrop = (username: string) => {
  dialog.warning({
    title: '删除用户',
    content: `确定要删除用户 "${username}" 吗？`,
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
