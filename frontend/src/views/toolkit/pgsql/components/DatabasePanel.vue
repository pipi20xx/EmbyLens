<template>
  <n-space vertical>
    <n-space justify="space-between" align="center">
      <n-button type="primary" @click="showCreateModal = true">创建数据库</n-button>
      <n-button @click="fetchDatabases" :loading="loading">刷新列表</n-button>
    </n-space>
    <n-data-table :columns="columns" :data="dbList" :loading="loading" />

    <n-modal v-model:show="showCreateModal" preset="card" title="创建数据库" style="width: 400px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="数据库名称">
          <n-input v-model:value="newDbName" placeholder="请输入库名" />
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
import { ref, watch, h } from 'vue'
import { NSpace, NButton, NDataTable, NModal, NForm, NFormItem, NInput, useMessage, useDialog } from 'naive-ui'
import axios from 'axios'

const props = defineProps<{ host: any }>()
const message = useMessage()
const dialog = useDialog()

const dbList = ref<any[]>([])
const loading = ref(false)
const showCreateModal = ref(false)
const newDbName = ref('')
const creating = ref(false)

const columns = [
  { title: '数据库名称', key: 'name' },
  {
    title: '操作',
    key: 'actions',
    render: (row: any) => h(
      NButton,
      {
        size: 'small',
        type: 'error',
        ghost: true,
        onClick: () => handleDrop(row.name)
      },
      { default: () => '删除' }
    )
  }
]

const fetchDatabases = async () => {
  if (!props.host) return
  loading.value = true
  try {
    const res = await axios.post('/api/pgsql/databases', props.host)
    dbList.value = res.data.map((name: string) => ({ name }))
  } catch (e) {}
  finally { loading.value = false }
}

const handleCreate = async () => {
  if (!newDbName.value) return
  creating.value = true
  try {
    await axios.post('/api/pgsql/databases/create', {
      config: props.host,
      req: { dbname: newDbName.value }
    })
    message.success('创建成功')
    showCreateModal.value = false
    newDbName.value = ''
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
