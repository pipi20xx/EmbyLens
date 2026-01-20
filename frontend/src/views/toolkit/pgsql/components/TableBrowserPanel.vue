<template>
  <n-layout has-sider style="height: calc(100vh - 300px); min-height: 500px;" bordered>
    <n-layout-sider bordered collapse-mode="width" :collapsed-width="48" :width="240" show-trigger>
      <div style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.09)">
        <n-space vertical size="small">
          <n-select
            v-model:value="currentDb"
            :options="dbOptions"
            placeholder="切换数据库"
            size="small"
            @update:value="handleDbChange"
          />
          <n-button block size="tiny" ghost icon-placement="right" @click="fetchTables">
            刷新表列表
            <template #icon><n-icon><RefreshIcon /></n-icon></template>
          </n-button>
        </n-space>
      </div>
      <n-menu
        v-model:value="selectedTable"
        :options="tableMenuOptions"
        :indent="18"
        @update:value="handleTableChange"
      />
    </n-layout-sider>
    <n-layout-content content-style="padding: 16px; display: flex; flex-direction: column;">
      <div v-if="!selectedTable" class="empty-state">
        <n-empty :description="currentDb ? '该库下没有发现公有表，或请从左侧选择' : '请先在上方选择一个数据库'" />
      </div>
      <div v-else style="flex: 1; display: flex; flex-direction: column;">
        <n-space justify="space-between" align="center" style="margin-bottom: 12px">
          <n-space align="center">
            <n-icon size="20"><TableIcon /></n-icon>
            <n-text strong style="font-size: 16px">{{ selectedTable }}</n-text>
            <n-tag size="small" type="info">{{ pagination.itemCount }} 条记录</n-tag>
          </n-space>
          <n-button size="small" @click="fetchTableData" :loading="loading">刷新数据</n-button>
        </n-space>
        <n-data-table
          flex-height remote
          :columns="columns"
          :data="tableData"
          :loading="loading"
          :pagination="pagination"
          :scroll-x="1200"
          style="flex: 1"
        />
      </div>
    </n-layout-content>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, h } from 'vue'
import { NLayout, NLayoutSider, NLayoutContent, NMenu, NDataTable, NEmpty, NSpace, NIcon, NText, NTag, NButton, NSelect, useMessage } from 'naive-ui'
import { TableChartOutlined as TableIcon, RefreshOutlined as RefreshIcon } from '@vicons/material'
import axios from 'axios'

const props = defineProps<{ host: any }>()
const message = useMessage()

const dbList = ref<string[]>([])
const currentDb = ref<string | null>(null)
const selectedTable = ref<string | null>(null)
const tableList = ref<string[]>([])
const tableData = ref<any[]>([])
const columns = ref<any[]>([])
const loading = ref(false)

// 计算属性：将主机配置与当前选中的库合并
const activeConfig = computed(() => {
  if (!props.host || !currentDb.value) return null
  return { ...props.host, database: currentDb.value }
})

const dbOptions = computed(() => dbList.value.map(db => ({ label: db, value: db })))

const pagination = reactive({
  page: 1,
  pageSize: 50,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [20, 50, 100],
  onChange: (page: number) => {
    pagination.page = page
    fetchTableData()
  }
})

const tableMenuOptions = computed(() => {
  return tableList.value.map(t => ({
    label: t,
    key: t,
    icon: () => h(NIcon, null, { default: () => h(TableIcon) })
  }))
})

// 1. 获取该实例下的所有数据库
const fetchDatabases = async () => {
  if (!props.host) return
  try {
    const res = await axios.post('/api/pgsql/databases', props.host)
    // 后端返回的是对象数组
    dbList.value = res.data.map((db: any) => db.name)
    
    // 初始化数据库选中
    if (!currentDb.value && dbList.value.length > 0) {
      if (dbList.value.includes(props.host.database)) {
        currentDb.value = props.host.database
      } else {
        currentDb.value = dbList.value[0]
      }
      fetchTables()
    }
  } catch (e: any) {
    message.error('加载数据库列表失败')
  }
}

// 2. 获取选中库下的表
const fetchTables = async () => {
  if (!activeConfig.value) return
  try {
    const res = await axios.post('/api/pgsql/tables', activeConfig.value)
    tableList.value = res.data.tables
    if (tableList.value.length === 0) {
      message.info('该库下未发现公有表')
    }
  } catch (e: any) {
    message.error('加载表列表失败: ' + (e.response?.data?.detail || e.message))
  }
}

const fetchTableData = async () => {
  if (!selectedTable.value || !activeConfig.value) return
  loading.value = true
  try {
    const res = await axios.post('/api/pgsql/data', {
      config: activeConfig.value,
      params: {
        table_name: selectedTable.value,
        page: pagination.page,
        page_size: pagination.pageSize
      }
    })
    columns.value = res.data.columns.map((col: any) => ({
      title: col.name,
      key: col.name,
      width: 150,
      ellipsis: { tooltip: true }
    }))
    tableData.value = res.data.rows
    pagination.itemCount = res.data.total
  } catch (e: any) {
    message.error('加载数据失败')
  }
  finally { loading.value = false }
}

const handleDbChange = () => {
  selectedTable.value = null
  tableList.value = []
  tableData.value = []
  fetchTables()
}

const handleTableChange = (val: string) => {
  selectedTable.value = val
  pagination.page = 1
  fetchTableData()
}

watch(() => props.host, () => {
  currentDb.value = null
  selectedTable.value = null
  dbList.value = []
  tableList.value = []
  fetchDatabases()
}, { immediate: true })

defineExpose({ refresh: fetchDatabases })
</script>

<style scoped>
.empty-state { height: 100%; display: flex; align-items: center; justify-content: center; }
</style>