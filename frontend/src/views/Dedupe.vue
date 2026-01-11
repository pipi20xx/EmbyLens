<template>
  <div class="dedupe-layout">
    <n-space vertical size="large">
      <n-card embedded :bordered="false" size="small">
        <n-space justify="space-between" align="center">
          <n-space align="center" :size="20">
            <n-h2 style="margin: 0"><n-text type="primary">Emby 媒体管理与去重</n-text></n-h2>
            <n-input-group>
              <n-input v-model:value="searchName" placeholder="高级搜索: 名称:xxx / ID..." style="width: 280px" @keypress.enter="loadItems" />
              <n-button type="primary" @click="loadItems">
                <template #icon><n-icon><SearchIcon /></n-icon></template>
              </n-button>
            </n-input-group>
            <n-checkbox v-model:checked="showOnlyDuplicates" @update:checked="toggleDuplicateMode">
              仅显示重复项
            </n-checkbox>
          </n-space>
          
          <n-space>
            <!-- 智能选中按钮现在总是显示 -->
            <n-button type="warning" secondary @click="handleAutoSelect">
              <template #icon><n-icon><AutoIcon /></n-icon></template>
              ✨ 智能分析清理
            </n-button>
            <n-button ghost @click="showConfig = true">
              <template #icon><n-icon><SettingsIcon /></n-icon></template>
              规则设置
            </n-button>
            <n-button type="primary" secondary :loading="syncing" @click="syncMedia">
              从 Emby 同步
            </n-button>
            <n-button v-if="selectedIds.length > 0" type="error" @click="showConfirm = true">
              手动删除选中 ({{ selectedIds.length }})
            </n-button>
          </n-space>
        </n-space>
      </n-card>

      <n-card :bordered="false" content-style="padding: 0">
        <n-data-table
          remote :columns="columns" :data="items" :loading="loading" :row-key="row => row.id"
          v-model:checked-row-keys="selectedIds" :pagination="false" size="small"
          max-height="calc(100vh - 220px)" virtual-scroll :cascade="false" @load="onLoadChildren"
        />
      </n-card>
    </n-space>

    <DedupeConfigModal v-model:show="showConfig" :config="dedupeConfig" @save="handleConfigSave" />

    <!-- 弹窗清单现在显示 suggestedItems -->
    <DedupeConfirmModal
      v-model:show="showConfirm"
      :items="confirmItems"
      @confirm="handleBulkDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { NCard, NSpace, NButton, NIcon, NInput, NInputGroup, NCheckbox, NDataTable, NH2, NText, useMessage } from 'naive-ui'
import { SearchOutlined as SearchIcon, SettingsOutlined as SettingsIcon, AutoFixHighOutlined as AutoIcon } from '@vicons/material'

import { getColumns } from './toolkit/dedupe/columns'
import { useDedupe } from './toolkit/dedupe/useDedupe'
import DedupeConfigModal from './toolkit/dedupe/DedupeConfigModal.vue'
import DedupeConfirmModal from './toolkit/dedupe/DedupeConfirmModal.vue'

const message = useMessage()
const {
  loading, syncing, searchName, showOnlyDuplicates, items, selectedIds, suggestedItems, dedupeConfig,
  loadItems, onLoadChildren, toggleDuplicateMode, syncMedia, autoSelect, deleteItems, loadConfig, saveDedupeConfig
} = useDedupe()

const columns = getColumns()
const showConfig = ref(false)
const showConfirm = ref(false)

// 如果是智能分析出来的，显示 suggestedItems，否则显示手动勾选的
const confirmItems = computed(() => {
  if (suggestedItems.value.length > 0 && selectedIds.value.length === suggestedItems.value.length) {
    return suggestedItems.value
  }
  // 手动勾选时，从当前页面列表找对象
  return items.value.filter(i => selectedIds.value.includes(i.id))
})

onMounted(async () => {
  await loadConfig()
  loadItems()
})

const handleAutoSelect = async () => {
  const res = await autoSelect()
  if (res.length > 0) {
    showConfirm.value = true
  }
}

const handleConfigSave = async (newConfig: any) => {
  dedupeConfig.value = newConfig
  if (await saveDedupeConfig()) showConfig.value = false
}

const handleBulkDelete = () => {
  const count = selectedIds.value.length
  // 1. 立即给用户反馈
  const msgInstance = message.loading(`正在启动后台清理任务，共 ${count} 个项目...`, { duration: 3000 })
  
  // 2. 立即关闭弹窗并重置状态，释放 UI
  showConfirm.value = false
  const idsToDelete = [...selectedIds.value] // 备份 ID 列表
  selectedIds.value = []
  suggestedItems.value = []

  // 3. 静默执行请求
  deleteItems(idsToDelete).then(success => {
    msgInstance.destroy()
    if (success) {
      message.success('后台清理指令已全部下发，请检查日志查看最终结果')
    }
  })
}
</script>

<style scoped>
.dedupe-layout { 
  width: 100%;
}
:deep(.n-h2 .n-text--primary-type) {
  color: var(--primary-color);
}
:deep(.n-data-table-tr--with-children) { 
  background-color: rgba(255, 255, 255, 0.02); 
}
:deep(.n-data-table .n-data-table-td--selection) {
  color: var(--primary-color);
}
</style>
