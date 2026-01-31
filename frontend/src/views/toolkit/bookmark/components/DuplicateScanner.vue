<template>
  <div class="scanner-container">
    <div class="scanner-header">
      <div class="flex flex-col">
        <span class="scanner-title">重复书签扫描</span>
        <span class="scanner-subtitle">
          共发现 <span class="highlight">{{ duplicates.length }}</span> 组重复项
        </span>
      </div>
      <n-space>
        <n-button 
          v-if="duplicates.length > 0"
          type="warning"
          size="small"
          @click="$emit('mergeAllDuplicates')"
          secondary
          round
        >
          <template #icon><n-icon><MergeIcon /></n-icon></template>
          一键合并所有
        </n-button>
        
        <n-button 
          type="primary" 
          size="small" 
          @click="$emit('scanDuplicates')" 
          :loading="loadingDuplicates"
          secondary
          round
        >
          <template #icon><n-icon><RefreshIcon /></n-icon></template>
          重新扫描
        </n-button>
      </n-space>
    </div>
    
    <n-scrollbar class="scanner-content">
      <div v-if="duplicates.length > 0" class="duplicate-list">
        <div v-for="group in duplicates" :key="group.url" class="duplicate-group">
          <div class="group-header">
            <div class="group-info">
              <div class="group-title">{{ group.items[0]?.title || '无标题' }}</div>
              <a :href="group.url" target="_blank" class="group-url" @click.stop>{{ group.url }}</a>
            </div>
            <n-tag type="warning" round size="small" :bordered="false" class="group-tag">
              {{ group.count }} 处重复
            </n-tag>
          </div>

          <div class="item-list">
            <div v-for="item in group.items" :key="item.id" class="duplicate-item">
              <div class="item-main">
                <div class="path-box">
                  <n-icon color="var(--primary-color)" size="16"><FolderIcon /></n-icon>
                  <span class="path-text">{{ resolvePath(item.parent_id) }}</span>
                </div>
                <div class="item-id">ID: {{ item.id }}</div>
              </div>
              <n-button size="tiny" type="primary" secondary @click="$emit('mergeDuplicate', group, item.id)" round>
                保留此项
              </n-button>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <n-empty description="暂无重复书签" />
      </div>
    </n-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { 
  RefreshOutlined as RefreshIcon, 
  FolderOutlined as FolderIcon,
  LayersOutlined as MergeIcon
} from '@vicons/material'

const props = defineProps<{
  duplicates: any[]
  loadingDuplicates: boolean
  bookmarks: any[]
}>()

defineEmits(['scanDuplicates', 'mergeDuplicate', 'mergeAllDuplicates'])

const resolvePath = (parentId: string | null): string => {
  if (!parentId || parentId === 'root') return '根目录'
  
  const findPath = (items: any[], targetId: string, currentPath: string[]): string[] | null => {
    for (const item of items) {
      if (item.id === targetId) return [...currentPath, item.title]
      if (item.children) {
        const result = findPath(item.children, targetId, [...currentPath, item.title])
        if (result) return result
      }
    }
    return null
  }
  
  const path = findPath(props.bookmarks, parentId, [])
  return path ? path.join(' / ') : '未知文件夹'
}
</script>

<style scoped>
.scanner-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: transparent;
}

.scanner-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.scanner-title {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.scanner-subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 2px;
}

.highlight {
  color: var(--primary-color);
  font-weight: 700;
  margin: 0 2px;
}

.scanner-content {
  flex: 1;
}

.duplicate-list {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.duplicate-group {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.duplicate-group:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}

.group-header {
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.02);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.group-info {
  flex: 1;
  min-width: 0;
}

.group-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.group-url {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
  text-decoration: none;
  display: block;
  transition: color 0.2s;
}

.group-url:hover {
  color: var(--primary-color);
  text-decoration: underline;
}

.group-tag {
  flex-shrink: 0;
}

.item-list {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.duplicate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.duplicate-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.item-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.path-box {
  display: flex;
  align-items: center;
  gap: 6px;
}

.path-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
}

.item-id {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.2);
  margin-left: 22px;
}

.empty-state {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.5;
}
</style>