<template>
  <n-space vertical>
    <n-space justify="space-between" align="center">
      <n-space>
        <n-button type="primary" @click="openCreateModal" :disabled="!host">创建新备份</n-button>
        <n-button @click="fetchBackups" :loading="loading">刷新列表</n-button>
      </n-space>
      <n-alert type="info" size="small" :show-icon="false">
        备份文件存储在 data/backups/pg 目录下
      </n-alert>
    </n-space>

    <n-data-table :columns="columns" :data="backupList" :loading="loading" />

    <!-- 创建备份模态框 -->
    <n-modal v-model:show="showCreateModal" preset="card" title="创建数据库备份" style="width: 450px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="选择数据库">
          <n-select 
            v-model:value="selectedDbToBackup" 
            :options="dbOptions" 
            placeholder="请选择要备份的数据库" 
          />
        </n-form-item>
        <n-p depth="3">
          提示：备份将使用 pg_dump 生成 .bak 文件（自定义格式），支持高效还原。
        </n-p>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="handleCreateBackup" :loading="actionLoading">开始备份</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 还原备份模态框 -->
    <n-modal v-model:show="showRestoreModal" preset="card" :title="`还原备份: ${selectedBackup?.filename}`" style="width: 450px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="目标数据库">
          <n-select 
            v-model:value="selectedDbToRestore" 
            :options="dbOptions" 
            placeholder="选择要还原到的目标数据库" 
          />
        </n-form-item>
        <n-alert type="warning" title="危险警告">
          还原操作将执行以下步骤：
          1. 强制断开目标数据库的所有连接。
          2. 删除并重新创建该数据库。
          3. 从备份文件恢复数据。
          所有当前数据将被覆盖！
        </n-alert>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showRestoreModal = false">取消</n-button>
          <n-button type="error" @click="handleRestore" :loading="actionLoading">确认还原</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, watch, h, computed } from 'vue'
import { 
  NSpace, NButton, NDataTable, NModal, NForm, NFormItem, NSelect, 
  useMessage, useDialog, NAlert, NP, NText 
} from 'naive-ui'
import axios from 'axios'

const props = defineProps<{ host: any }>()
const message = useMessage()
const dialog = useDialog()

const backupList = ref<any[]>([])
const dbList = ref<any[]>([])
const loading = ref(false)
const actionLoading = ref(false)

// 创建备份逻辑
const showCreateModal = ref(false)
const selectedDbToBackup = ref<string | null>(null)

// 还原备份逻辑
const showRestoreModal = ref(false)
const selectedBackup = ref<any>(null)
const selectedDbToRestore = ref<string | null>(null)

const dbOptions = computed(() => dbList.value.map(db => ({ label: db.name, value: db.name })))

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

const columns = [
  { title: '备份文件', key: 'filename', ellipsis: { tooltip: true } },
  { title: '原数据库', key: 'db_name', width: 120 },
  { 
    title: '大小', 
    key: 'size', 
    width: 100,
    render: (row: any) => formatSize(row.size)
  },
  { 
    title: '创建时间', 
    key: 'created_at', 
    width: 180,
    render: (row: any) => formatDate(row.created_at)
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: any) => h(NSpace, {}, {
      default: () => [
        h(NButton, {
          size: 'small',
          type: 'warning',
          secondary: true,
          onClick: () => openRestoreModal(row)
        }, { default: () => '还原' }),
        h(NButton, {
          size: 'small',
          type: 'error',
          ghost: true,
          onClick: () => handleDelete(row.filename)
        }, { default: () => '删除' })
      ]
    })
  }
]

const fetchBackups = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/pgsql/backups')
    backupList.value = res.data
  } catch (e: any) {
    message.error('获取备份列表失败')
  } finally {
    loading.value = false
  }
}

const fetchDatabases = async () => {
  if (!props.host) return
  try {
    const res = await axios.post('/api/pgsql/databases', props.host)
    dbList.value = res.data
  } catch (e) {}
}

const openCreateModal = () => {
  showCreateModal.value = true
  fetchDatabases()
}

const handleCreateBackup = async () => {
  if (!selectedDbToBackup.value || !props.host) return
  actionLoading.value = true
  try {
    await axios.post('/api/pgsql/backups/create', {
      config: props.host,
      req: { dbname: selectedDbToBackup.value }
    })
    message.success('备份创建成功')
    showCreateModal.value = false
    fetchBackups()
  } catch (e: any) {
    message.error('备份失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    actionLoading.value = false
  }
}

const openRestoreModal = (row: any) => {
  selectedBackup.value = row
  selectedDbToRestore.value = row.db_name !== 'unknown' ? row.db_name : null
  showRestoreModal.value = true
  fetchDatabases()
}

const handleRestore = async () => {
  if (!selectedBackup.value || !selectedDbToRestore.value || !props.host) return
  
  actionLoading.value = true
  try {
    await axios.post(`/api/pgsql/backups/restore/${selectedBackup.value.filename}`, props.host, {
      params: { dbname: selectedDbToRestore.value }
    })
    message.success('数据库还原成功')
    showRestoreModal.value = false
  } catch (e: any) {
    message.error('还原失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    actionLoading.value = false
  }
}

const handleDelete = (filename: string) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除备份文件 ${filename} 吗？此操作不可撤销。`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await axios.delete(`/api/pgsql/backups/${filename}`)
        message.success('已删除备份')
        fetchBackups()
      } catch (e) {
        message.error('删除失败')
      }
    }
  })
}

watch(() => props.host, () => {
  fetchBackups()
}, { immediate: true })

defineExpose({ refresh: fetchBackups })
</script>