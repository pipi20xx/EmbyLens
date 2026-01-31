<template>
  <div class="scanner-container">
    <div class="scanner-header">
      <div class="flex flex-col flex-1">
        <span class="scanner-title">无效链接诊断</span>
        <span class="scanner-subtitle">检测 404 及超时链接，建议分批清理</span>
      </div>
      <n-space>
        <n-button 
          v-if="healthResults.some(h => h.statusCode === 404)"
          type="warning"
          size="small"
          @click="$emit('deleteBatchDead', [404])"
          secondary
          round
        >
          <template #icon><n-icon><DeleteSweepIcon /></n-icon></template>
          一键清理 404
        </n-button>
        
        <n-button 
          v-if="isScanningHealth" 
          type="error" 
          size="small" 
          @click="$emit('stopScan')" 
          secondary 
          round
        >
          <template #icon><n-icon><StopIcon /></n-icon></template>
          停止扫描
        </n-button>
        <n-button 
          v-else 
          type="primary" 
          size="small" 
          @click="$emit('scanHealth')" 
          secondary 
          round
        >
          <template #icon><n-icon><PlayIcon /></n-icon></template>
          开始诊断
        </n-button>
      </n-space>
    </div>

    <div class="progress-wrapper" v-if="isScanningHealth || healthProgress > 0">
      <n-progress 
        type="line" 
        :percentage="healthProgress" 
        :processing="isScanningHealth" 
        :height="4"
        :show-indicator="false"
        class="custom-progress"
      />
      <div class="progress-info">
        <span>诊断进度</span>
        <span>{{ Math.round(healthProgress) }}%</span>
      </div>
    </div>

    <n-scrollbar class="scanner-content">
      <div v-if="healthResults.length > 0" class="dead-link-list">
        <div v-for="item in healthResults" :key="item.id" class="dead-link-item">
          <div class="status-badge">
            <n-tag :type="item.statusCode === 0 ? 'warning' : 'error'" size="small" :bordered="false" round>
              {{ item.statusCode === 0 ? '超时' : item.statusCode }}
            </n-tag>
          </div>
          
          <div class="item-info">
            <div class="item-title">{{ item.title || '无标题' }}</div>
            <div class="item-meta">
              <div class="path-box">
                <n-icon size="14"><FolderIcon /></n-icon>
                <span>{{ resolvePath(item.parent_id) }}</span>
              </div>
              <a :href="item.url" target="_blank" class="url-link" @click.stop>{{ item.url }}</a>
            </div>
          </div>

          <div class="item-actions">
            <n-button circle quaternary type="error" size="small" @click="$emit('deleteDead', item.id)">
              <template #icon><n-icon><DeleteIcon /></n-icon></template>
            </n-button>
          </div>
        </div>
      </div>
      
      <div v-else class="empty-state">
        <template v-if="isScanningHealth">
          <n-spin size="large" />
          <div class="empty-text">正在深度诊断书签健康度...</div>
        </template>
        <n-empty v-else description="暂无异常链接" />
      </div>
    </n-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { 
  DeleteOutlineOutlined as DeleteIcon,
  PlayArrowOutlined as PlayIcon,
  StopOutlined as StopIcon,
  FolderOutlined as FolderIcon,
  DeleteSweepOutlined as DeleteSweepIcon
} from '@vicons/material'

const props = defineProps<{
  healthResults: any[]
  healthProgress: number
  isScanningHealth: boolean
  bookmarks: any[]
}>()

defineEmits(['scanHealth', 'stopScan', 'deleteDead', 'deleteBatchDead'])

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

.progress-wrapper {
  padding: 12px 20px;
  background: rgba(var(--primary-color-rgb), 0.05);
  border-bottom: 1px solid rgba(var(--primary-color-rgb), 0.1);
}

.custom-progress {
  --n-fill-color: var(--primary-color);
  --n-rail-color: rgba(255, 255, 255, 0.06);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 700;
  color: var(--primary-color);
  margin-top: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.scanner-content {
  flex: 1;
}

.dead-link-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dead-link-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.2s ease;
}

.dead-link-item:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  transform: translateX(4px);
}

.status-badge {
  flex-shrink: 0;
  width: 50px;
  display: flex;
  justify-content: center;
}

.item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.path-box {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.url-link {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.25);
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
  text-decoration: none;
  transition: color 0.2s;
}

.url-link:hover {
  color: var(--primary-color);
  text-decoration: underline;
}

.item-actions {
  flex-shrink: 0;
  opacity: 0.3;
  transition: opacity 0.2s;
}

.dead-link-item:hover .item-actions {
  opacity: 1;
}

.empty-state {
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}
</style>