<template>
  <div class="toolkit-container">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">媒体净化清理</n-text></n-h2>
        <n-text depth="3">支持指定媒体库与媒体类型，执行演职员移除或剧集类型重置。</n-text>
      </div>

      <!-- 1. 全局配置 (lib_names & dry_run) -->
      <n-card title="通用执行参数" size="small" segmented>
        <n-form label-placement="left" label-width="120">
          <n-form-item label="目标媒体库">
            <n-select 
              v-model:value="common.lib_names" 
              multiple 
              filterable 
              :options="libOptions"
              placeholder="自动拉取媒体库列表中..." 
            />
          </n-form-item>
          <n-form-item label="执行模式">
            <n-switch v-model:value="common.dry_run">
              <template #checked>预览模式</template>
              <template #unchecked>实调模式</template>
            </n-switch>
          </n-form-item>
        </n-form>
      </n-card>

      <!-- 2. 原子工具卡片 -->
      <n-grid :cols="2" :x-gap="12">
        <n-gi>
          <n-card title="演职员信息清空" size="small">
            <n-space vertical>
              <n-text depth="3" style="font-size: 12px">操作媒体类型：</n-text>
              <n-checkbox-group v-model:value="peopleItemTypes">
                <n-space>
                  <n-checkbox value="Movie">电影</n-checkbox>
                  <n-checkbox value="Series">剧集</n-checkbox>
                </n-space>
              </n-checkbox-group>
              <n-divider style="margin: 8px 0" />
              <n-button block type="error" secondary @click="handleAction('people_remover')" :loading="loading">
                执行清空演职员
              </n-button>
            </n-space>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="集类型(Episode)重置" size="small">
            <n-p depth="3" style="font-size: 12px">
              扫描指定媒体库中的所有剧集，清除“集”层级的 Genres 标签。
            </n-p>
            <n-divider style="margin: 8px 0" />
            <n-button block type="primary" quaternary @click="handleAction('episode_deleter')" :loading="loading">
              修复集类型标记
            </n-button>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 3. 调试：接口快照 -->
      <n-card title="调试：原版接口请求快照" embedded :bordered="false">
        <n-code :code="debugPayload" language="json" word-wrap />
      </n-card>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { 
  NSpace, NH2, NText, NCard, NP, NButton, NGrid, NGi, 
  NCode, NCheckboxGroup, NCheckbox, NSwitch, NForm, NFormItem, NSelect, NDivider 
} from 'naive-ui'

// 导入提取的逻辑
import { useCleanupTools } from './cleanup/hooks/useCleanupTools'

const { 
  loading, libOptions, common, peopleItemTypes, debugPayload,
  fetchLibraries, handleAction 
} = useCleanupTools()

onMounted(fetchLibraries)
</script>

<style scoped>
.toolkit-container { 
  width: 100%; 
}
:deep(.n-h2 .n-text--error-type),
:deep(.n-h2 .n-text--primary-type) {
  color: var(--primary-color);
}
</style>
