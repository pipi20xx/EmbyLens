<template>
  <n-modal
    :show="show"
    @update:show="$emit('update:show', $event)"
    preset="card"
    title="待清理媒体清单"
    style="width: 900px"
    :bordered="false"
    size="huge"
  >
    <template #header-extra>
      <n-text depth="3">共选中 {{ items.length }} 个项目</n-text>
    </template>

    <n-alert type="warning" style="margin-bottom: 16px">
      请仔细核对以下列表。点击下方的“确认并永久删除”后，这些文件将从磁盘中彻底移除。
    </n-alert>

    <div class="confirm-list-wrapper">
      <n-table :bordered="false" :single-line="false" size="small">
        <thead>
          <tr>
            <th>媒体名称 / 编号</th>
            <th>规格</th>
            <th>物理路径</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td width="300">
              <n-space vertical :size="2">
                <n-text strong>{{ item.name }}</n-text>
                <n-tag v-if="item.item_type === 'Episode'" size="tiny" :bordered="false" type="info">
                  {{ formatEpisode(item) }}
                </n-tag>
                <n-tag v-else-if="item.item_type === 'Series'" size="tiny" :bordered="false" type="warning">
                  剧集本体
                </n-tag>
              </n-space>
            </td>
            <td width="120">
              <n-space vertical :size="2">
                <n-tag size="tiny" ghost type="primary">{{ item.display_title }}</n-tag>
                <n-text depth="3" style="font-size: 10px">{{ item.video_codec }}</n-text>
              </n-space>
            </td>
            <td>
              <div class="confirm-path-text" :title="item.path">{{ item.path }}</div>
            </td>
          </tr>
        </tbody>
      </n-table>
    </div>

    <template #footer>
      <n-space justify="end">
        <n-button @click="$emit('update:show', false)">点错了，返回</n-button>
        <n-button 
          type="error" 
          :loading="loading" 
          @click="$emit('confirm')"
        >
          确认并永久删除 ({{ items.length }} 项)
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { NModal, NTable, NText, NTag, NSpace, NButton, NAlert } from 'naive-ui'

defineProps<{
  show: boolean
  items: any[]
  loading?: boolean
}>()

defineEmits(['update:show', 'confirm'])

const formatEpisode = (item: any) => {
  const raw = item.raw_data || {}
  const s = raw.ParentIndexNumber
  const e = raw.IndexNumber
  if (s !== undefined && e !== undefined) {
    return `S${String(s).padStart(2, '0')}E${String(e).padStart(2, '0')}`
  }
  return '未知编号'
}
</script>

<style scoped>
.confirm-list-wrapper {
  max-height: 500px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}
.confirm-path-text {
  font-size: 10px;
  opacity: 0.5;
  font-family: monospace;
  word-break: break-all;
  line-height: 1.2;
}
</style>
