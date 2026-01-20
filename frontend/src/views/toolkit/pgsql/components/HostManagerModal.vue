<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)" preset="card" title="管理 PostgreSQL 主机" style="width: 650px">
    <n-space vertical size="large">
      <n-space justify="space-between">
        <n-button type="primary" @click="showAdd = true">添加新主机</n-button>
        <n-button @click="fetchHosts">刷新</n-button>
      </n-space>
      
      <n-data-table :columns="columns" :data="hosts" />
    </n-space>

    <!-- 嵌套添加主机模态框 -->
    <n-modal v-model:show="showAdd" preset="card" title="配置数据库主机" style="width: 500px">
      <n-form :model="form" label-placement="left" label-width="100">
        <n-form-item label="显示名称">
          <n-input v-model:value="form.name" placeholder="例如: 生产环境库" />
        </n-form-item>
        <n-grid :cols="2" :x-gap="12">
          <n-gi :span="1">
            <n-form-item label="主机">
              <n-input v-model:value="form.host" placeholder="localhost" />
            </n-form-item>
          </n-gi>
          <n-gi :span="1">
            <n-form-item label="端口">
              <n-input-number v-model:value="form.port" :show-button="false" style="width: 100%" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="用户名">
          <n-input v-model:value="form.username" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="form.password" type="password" />
        </n-form-item>
        <n-form-item label="默认数据库">
          <n-input v-model:value="form.database" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAdd = false">取消</n-button>
          <n-button type="warning" @click="handleTest" :loading="testing">测试连接</n-button>
          <n-button type="primary" @click="handleSave">保存主机</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, reactive, h, onMounted } from 'vue'
import { NModal, NSpace, NButton, NDataTable, NForm, NFormItem, NInput, NInputNumber, NGrid, NGi, useMessage, useDialog } from 'naive-ui'
import axios from 'axios'

defineProps<{ show: boolean }>()
const emit = defineEmits(['update:show', 'refresh'])

const message = useMessage()
const dialog = useDialog()

const hosts = ref<any[]>([])
const showAdd = ref(false)
const testing = ref(false)

const form = reactive({
  name: '',
  host: 'localhost',
  port: 5432,
  username: 'postgres',
  password: '',
  database: 'postgres'
})

const columns = [
  { title: '名称', key: 'name' },
  { title: '地址', key: 'host', render: (row: any) => `${row.host}:${row.port}` },
  { 
    title: '操作', 
    key: 'actions', 
    render: (row: any) => h(
      NButton, 
      { size: 'small', type: 'error', ghost: true, onClick: () => handleDelete(row.id) }, 
      { default: () => '移除' }
    ) 
  }
]

const fetchHosts = async () => {
  const res = await axios.get('/api/pgsql/hosts')
  hosts.value = res.data
}

const handleTest = async () => {
  testing.value = true
  try {
    const res = await axios.post('/api/pgsql/test', form)
    if (res.data.success) message.success('测试成功: ' + res.data.version)
    else message.error('失败: ' + res.data.message)
  } catch (e: any) { message.error('请求出错') }
  finally { testing.value = false }
}

const handleSave = async () => {
  if (!form.name) return message.warning('请输入名称')
  try {
    await axios.post('/api/pgsql/hosts', form, { params: { name: form.name } })
    message.success('已添加')
    showAdd.value = false
    fetchHosts()
    emit('refresh')
  } catch (e) {}
}

const handleDelete = (id: string) => {
  dialog.warning({
    title: '确认移除',
    content: '确定要移除该数据库主机配置吗？',
    onPositiveClick: async () => {
      await axios.delete(`/api/pgsql/hosts/${id}`)
      fetchHosts()
      emit('refresh')
    }
  })
}

onMounted(fetchHosts)
</script>
