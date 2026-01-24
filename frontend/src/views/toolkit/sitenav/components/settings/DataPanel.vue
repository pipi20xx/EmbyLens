<script setup lang="ts">
import { 
  NSpace, NButton, NIcon, NText, NUpload, NCard
} from 'naive-ui'
import { 
  CloudDownloadOutlined as ExportIcon,
  CloudUploadOutlined as ImportIcon
} from '@vicons/material'

const emit = defineEmits(['export', 'import'])

const handleImport = (options: { file: { file: File } }) => {
  emit('import', options.file.file)
}
</script>

<template>
  <div class="tab-content">
    <div class="backup-section">
      <n-text depth="3" style="font-size: 12px; margin-bottom: 16px; display: block;">配置备份与恢复 (包含分类、站点及本地图标文件)</n-text>
      <n-space vertical size="large">
        <n-card embedded :bordered="false" size="small">
          <template #header>导出配置</template>
          <n-space vertical>
            <n-text depth="3">将当前所有导航数据导出为 .zip 压缩包，方便迁移到其他服务器。</n-text>
            <n-button secondary @click="emit('export')">
              <template #icon><n-icon><ExportIcon /></n-icon></template>
              生成并下载全量备份
            </n-button>
          </n-space>
        </n-card>

        <n-card embedded :bordered="false" size="small">
          <template #header>导入配置</template>
          <n-space vertical>
            <n-text depth="3" type="warning">注意：导入备份将覆盖当前所有导航设置，请谨慎操作。</n-text>
            <n-upload :show-file-list="false" @change="handleImport" accept=".zip">
              <n-button secondary type="info">
                <template #icon><n-icon><ImportIcon /></n-icon></template>
                上传备份文件恢复
              </n-button>
            </n-upload>
          </n-space>
        </n-card>
      </n-space>
    </div>
  </div>
</template>

<style scoped>
.tab-content { padding: 12px 4px; min-height: 300px; }
</style>