<template>
  <div class="dedupe-view">
    <n-space vertical size="large">
      <!-- 头部控制栏 -->
      <n-card embedded :bordered="false" size="small">
        <n-space justify="space-between" align="center">
          <n-space align="center" :size="24">
            <n-h2 style="margin: 0"><n-text type="primary">Emby 媒体管理与去重</n-text></n-h2>
            <n-input-group>
              <n-input v-model:value="searchName" placeholder="搜索名称..." @keypress.enter="loadItems" style="width: 200px" />
              <n-button type="primary" ghost @click="loadItems">
                <template #icon><n-icon><SearchIcon /></n-icon></template>
              </n-button>
            </n-input-group>
            <n-checkbox v-model:checked="showOnlyDuplicates" @update:checked="toggleDuplicateMode">
              仅显示重复项
            </n-checkbox>
          </n-space>
          
          <n-space>
            <n-button type="primary" secondary :loading="syncing" @click="syncMedia">
              <template #icon><n-icon><SyncIcon /></n-icon></template>
              从 Emby 全量同步
            </n-button>
            <n-button v-if="selectedIds.length > 0" type="error" @click="confirmDelete">
              <template #icon><n-icon><DeleteIcon /></n-icon></template>
              删除选中 ({{ selectedIds.length }})
            </n-button>
            <n-button v-if="showOnlyDuplicates" type="warning" ghost @click="autoSelect">
              <template #icon><n-icon><AutoIcon /></n-icon></template>
              智能选中副本
            </n-button>
          </n-space>
        </n-space>
      </n-card>

      <!-- 媒体列表主体 -->
      <n-card :bordered="false" content-style="padding: 0">
        <n-data-table
          remote
          ref="tableRef"
          :columns="columns"
          :data="displayData"
          :loading="loading"
          :row-key="row => row.id"
          @update:checked-row-keys="handleCheck"
          :pagination="false"
          size="small"
          max-height="calc(100vh - 280px)"
          virtual-scroll
        />
      </n-card>

      <div v-if="syncing" class="sync-footer">
        <n-alert type="info" size="small">正在全量同步媒体库数据，请稍候...</n-alert>
      </div>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { 
  NCard, NSpace, NButton, NIcon, NInput, NInputGroup, NCheckbox, NDataTable, 
  NH2, NText, NTag, NAlert, useMessage, useDialog 
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import {
  SearchOutlined as SearchIcon,
  SyncAltOutlined as SyncIcon,
  DeleteForeverOutlined as DeleteIcon,
  AutoFixHighOutlined as AutoIcon
} from '@vicons/material'
import axios from 'axios'

const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const syncing = ref(false)
const searchName = ref('')
const showOnlyDuplicates = ref(false)
const rawItems = ref<any[]>([])
const duplicateGroups = ref<any[]>([])
const selectedIds = ref<string[]>([])

// --- 表格列定义 ---
const columns: DataTableColumns<any> = [
  { type: 'selection' },
  {
    title: '名称',
    key: 'name',
    width: 250,
    render(row) {
      return h('div', [
        h(NText, { strong: true, depth: row.is_duplicate ? 1 : 2 }, { default: () => row.name }),
        h('div', { style: 'font-size: 10px; opacity: 0.5; font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;' }, row.path)
      ])
    }
  },
  {
    title: '类型',
    key: 'type',
    width: 80,
    render(row) {
      const typeMap: any = { 'Movie': '电影', 'Series': '剧集', 'Season': '季', 'Episode': '集' }
      return h(NTag, { size: 'small', bordered: false, type: row.type === 'Movie' ? 'success' : 'info' }, { default: () => typeMap[row.type] || row.type })
    }
  },
  {
    title: '年份',
    key: 'year',
    width: 70
  },
  {
    title: '媒体规格',
    key: 'display_title',
    width: 150,
    render(row) {
      return h(NTag, { size: 'small', bordered: false, type: 'warning' }, { default: () => row.display_title || 'N/A' })
    }
  },
  {
    title: '编码',
    key: 'video_codec',
    width: 100
  },
  {
    title: '动态范围',
    key: 'video_range',
    width: 100,
    render(row) {
      return row.video_range && row.video_range !== 'SDR' 
        ? h(NTag, { size: 'small', type: 'error', ghost: true }, { default: () => row.video_range })
        : h(NText, { depth: 3 }, { default: () => 'SDR' })
    }
  },
  {
    title: 'TMDB ID',
    key: 'tmdb_id',
    width: 100
  }
]

// --- 数据加载逻辑 ---
const loadItems = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/dedupe/items', { params: { query_text: searchName.value } })
    rawItems.value = res.data.map((i: any) => ({
      ...i,
      type: i.item_type,
      is_duplicate: false
    }))
  } catch (error) {
    message.error('加载列表失败')
  } finally {
    loading.value = false
  }
}

const toggleDuplicateMode = async (val: boolean) => {
  if (val) {
    loading.value = true
    try {
      const res = await axios.get('/api/dedupe/duplicates')
      duplicateGroups.value = res.data
      // 展平显示，但标记为重复项
      const flattened: any[] = []
      res.data.forEach((group: any) => {
        group.items.forEach((item: any) => {
          flattened.push({ ...item, is_duplicate: true })
        })
      })
      rawItems.value = flattened
    } catch (error) {
      message.error('加载重复项失败')
    } finally {
      loading.value = false
    }
  } else {
    loadItems()
  }
}

const displayData = computed(() => rawItems.value)

const syncMedia = async () => {
  syncing.value = true
  try {
    await axios.post('/api/dedupe/sync')
    message.success('同步完成')
    showOnlyDuplicates.value ? toggleDuplicateMode(true) : loadItems()
  } catch (error) {
    message.error('同步失败')
  } finally {
    syncing.value = false
  }
}

const handleCheck = (keys: string[]) => {
  selectedIds.value = keys
}

const autoSelect = async () => {
  if (!showOnlyDuplicates.value) {
    message.warning('请先进入“仅显示重复项”模式')
    return
  }
  try {
    const res = await axios.post('/api/dedupe/smart-select', { items: rawItems.value })
    selectedIds.value = res.data.to_delete
    message.success(`智能选中了 ${selectedIds.value.length} 个建议删除的项目`)
  } catch (error) {
    message.error('自动选中失败')
  }
}

const confirmDelete = () => {
  dialog.error({
    title: '危险操作：永久删除',
    content: `确定要永久删除选中的 ${selectedIds.value.length} 个项目吗？文件将从磁盘移除。`,
    positiveText: '确定删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const res = await axios.delete('/api/dedupe/items', { data: { item_ids: selectedIds.value } })
        message.success(`已删除 ${res.data.success} 个项目`)
        selectedIds.value = []
        showOnlyDuplicates.value ? toggleDuplicateMode(true) : loadItems()
      } catch (error) {
        message.error('删除操作失败')
      }
    }
  })
}

onMounted(() => {
  loadItems()
})
</script>

<style scoped>
.dedupe-view {
  padding: 0;
}
.sync-footer {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 300px;
  z-index: 100;
}
:deep(.n-data-table-td) {
  padding: 8px 12px;
}
</style>
