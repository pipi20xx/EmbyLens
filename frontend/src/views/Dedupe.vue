<template>
  <div class="dedupe-layout">
    <n-space vertical size="large">
      <!-- 1. 顶部操作栏 -->
      <n-card embedded :bordered="false" size="small">
        <n-space justify="space-between" align="center">
          <n-space align="center" :size="20">
            <n-h2 style="margin: 0"><n-text type="primary">Emby 媒体管理与去重</n-text></n-h2>
            <n-input-group>
              <n-input 
                v-model:value="searchName" 
                placeholder="搜索名称:铃芽 / 路径:Anime / ID..." 
                style="width: 280px" 
                @keypress.enter="loadItems"
              />
              <n-button type="primary" @click="loadItems">
                <template #icon><n-icon><SearchIcon /></n-icon></template>
              </n-button>
            </n-input-group>
            <n-checkbox v-model:checked="showOnlyDuplicates" @update:checked="toggleDuplicateMode">
              仅显示重复项
            </n-checkbox>
          </n-space>
          
          <n-space>
            <n-button ghost @click="showConfig = true">
              <template #icon><n-icon><SettingsIcon /></n-icon></template>
              规则设置
            </n-button>
            <n-button type="primary" secondary :loading="syncing" @click="syncMedia">
              从 Emby 同步
            </n-button>
            <n-button v-if="selectedIds.length > 0" type="error" @click="confirmDelete">
              永久删除 ({{ selectedIds.length }})
            </n-button>
            <n-button v-if="showOnlyDuplicates" type="warning" @click="autoSelect">
              ✨ 智能选中
            </n-button>
          </n-space>
        </n-space>
      </n-card>

      <!-- 2. 媒体数据表格 -->
      <n-card :bordered="false" content-style="padding: 0">
        <n-data-table
          remote
          :columns="columns"
          :data="items"
          :loading="loading"
          :row-key="row => row.id"
          @update:checked-row-keys="val => selectedIds = val"
          :pagination="false"
          size="small"
          max-height="calc(100vh - 220px)"
          virtual-scroll
          :cascade="false"
          @load="onLoadChildren"
        />
      </n-card>
    </n-space>

    <!-- 3. 拆分出的配置弹窗组件 -->
    <DedupeConfigModal
      v-model:show="showConfig"
      :config="dedupeConfig"
      @save="handleConfigSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NSpace, NButton, NIcon, NInput, NInputGroup, NCheckbox, NDataTable, NH2, NText } from 'naive-ui'
import { SearchOutlined as SearchIcon, SettingsOutlined as SettingsIcon } from '@vicons/material'

// 导入拆分出的各个模块
import { getColumns } from './toolkit/dedupe/columns'
import { useDedupe } from './toolkit/dedupe/useDedupe'
import DedupeConfigModal from './toolkit/dedupe/DedupeConfigModal.vue'

const {
  loading, syncing, searchName, showOnlyDuplicates, items, selectedIds, dedupeConfig,
  loadItems, onLoadChildren, toggleDuplicateMode, syncMedia, autoSelect, confirmDelete, loadConfig, saveDedupeConfig
} = useDedupe()

const columns = getColumns()
const showConfig = ref(false)

onMounted(async () => {
  await loadConfig()
  loadItems()
})

const handleConfigSave = async (newConfig: any) => {
  // 更新 Hook 里的状态
  dedupeConfig.value = newConfig
  // 调用 Hook 里的保存方法
  const success = await saveDedupeConfig()
  if (success) {
    showConfig.value = false
  }
}
</script>

<style scoped>
.dedupe-layout { padding: 0; }
:deep(.n-data-table-tr--with-children) { background-color: rgba(255, 255, 255, 0.02); }
:deep(.n-data-table-tr:hover) { background-color: rgba(112, 93, 242, 0.08) !important; }
</style>
