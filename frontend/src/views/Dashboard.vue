<template>
  <div class="dashboard-page">
    <n-space vertical size="large">
      <!-- 页面标题区 -->
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">管理仪表盘</n-text></n-h2>
        <n-text depth="3">欢迎使用 EmbyLens，在此查看系统概览与执行核心任务。</n-text>
      </div>

      <!-- 核心统计卡片 -->
      <n-grid :x-gap="12" :y-gap="12" :cols="4" item-responsive responsive="screen">
        <n-gi span="4 m:2 l:1">
          <n-card bordered size="small" hoverable>
            <n-statistic label="电影总数" :value="stats.movies">
              <template #prefix><n-icon><MovieIcon /></n-icon></template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi span="4 m:2 l:1">
          <n-card bordered size="small" hoverable>
            <n-statistic label="剧集总数" :value="stats.series">
              <template #prefix><n-icon><SeriesIcon /></n-icon></template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi span="4 m:2 l:1">
          <n-card bordered size="small" hoverable>
            <n-statistic label="重复组" :value="stats.duplicates">
              <template #prefix><n-icon><DedupeIcon /></n-icon></template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi span="4 m:2 l:1">
          <n-card bordered size="small" hoverable>
            <n-statistic label="服务状态" :value="stats.status === 'connected' ? '已连接' : '未就绪'">
              <template #prefix>
                <n-icon :color="stats.status === 'connected' ? 'var(--primary-color)' : '#f0a020'">
                  <StatusIcon />
                </n-icon>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>

      <n-grid :x-gap="12" :y-gap="12" :cols="24" item-responsive responsive="screen">
        <!-- 快捷操作区 -->
        <n-gi span="24 m:16">
          <n-card title="核心功能快捷入口" segmented size="small">
            <n-grid :x-gap="8" :y-gap="8" :cols="2" item-responsive>
              <n-gi v-for="tool in quickTools" :key="tool.key">
                <n-card 
                  embedded 
                  size="small" 
                  hoverable 
                  class="tool-card"
                  @click="navigateTo(tool.key)"
                >
                  <n-space align="center">
                    <n-icon size="24" color="var(--primary-color)">
                      <component :is="tool.icon" />
                    </n-icon>
                    <div>
                      <div style="font-weight: bold; font-size: 0.95rem">{{ tool.label }}</div>
                      <n-text depth="3" style="font-size: 0.8rem">{{ tool.desc }}</n-text>
                    </div>
                  </n-space>
                </n-card>
              </n-gi>
            </n-grid>
          </n-card>
        </n-gi>

        <!-- 系统信息区 -->
        <n-gi span="24 m:8">
          <n-card title="系统状态" segmented size="small">
            <n-list size="small">
              <n-list-item>
                <n-space justify="space-between">
                  <n-text depth="3">前端版本</n-text>
                  <n-tag size="small" type="primary" quaternary>v1.0.7</n-tag>
                </n-space>
              </n-list-item>
              <n-list-item>
                <n-space justify="space-between">
                  <n-text depth="3">后端连接</n-text>
                  <n-text style="font-family: monospace">{{ stats.status === 'connected' ? '正常' : '异常' }}</n-text>
                </n-space>
              </n-list-item>
              <n-list-item>
                <n-space justify="space-between">
                  <n-text depth="3">当前环境</n-text>
                  <n-tag size="small" type="info" quaternary>Production</n-tag>
                </n-space>
              </n-list-item>
            </n-list>
            <template #footer>
              <n-button block size="small" tertiary type="primary" @click="navigateTo('SettingsView')">
                配置中心
              </n-button>
            </template>
          </n-card>
        </n-gi>
      </n-grid>
    </n-space>
  </div>
</template>

<style scoped>
.dashboard-page {
  width: 100%;
}
.tool-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.tool-card:hover {
  transform: translateY(-2px);
  border-color: var(--primary-color);
}
:deep(.n-statistic .n-statistic__label) {
  font-weight: 500;
  color: var(--text-color);
  opacity: 0.8;
}
:deep(.n-statistic .n-statistic-value__content) {
  color: var(--primary-color);
}
</style>

<script setup lang="ts">
import { ref, onMounted, markRaw } from 'vue'
import { 
  NSpace, NGrid, NGi, NCard, NStatistic, NIcon, NText, 
  NH2, NList, NListItem, NTag, NButton 
} from 'naive-ui'
import axios from 'axios'
import {
  MovieRound as MovieIcon,
  LiveTvRound as SeriesIcon,
  AutoDeleteRound as DedupeIcon,
  SensorsRound as StatusIcon,
  CategoryRound as AutoTagIcon,
  LayersRound as CleanupIcon,
  LockOpenRound as LockIcon,
  SearchRound as QueryIcon
} from '@vicons/material'
import { currentViewKey } from '../store/navigationStore'

const stats = ref({
  movies: 0,
  series: 0,
  duplicates: 0,
  status: 'idle'
})

const quickTools = [
  { 
    label: '重复清理', 
    key: 'DedupeView', 
    icon: markRaw(DedupeIcon), 
    desc: '扫描并合并库中的重复视频' 
  },
  { 
    label: '自动标签', 
    key: 'AutoTagsView', 
    icon: markRaw(AutoTagIcon), 
    desc: '根据规则自动匹配媒体标签' 
  },
  { 
    label: '媒体净化', 
    key: 'CleanupToolsView', 
    icon: markRaw(CleanupIcon), 
    desc: '清空演职员与修复剧集类型' 
  },
  { 
    label: '锁定管理', 
    key: 'LockManagerView', 
    icon: markRaw(LockIcon), 
    desc: '批量锁定或解锁元数据字段' 
  }
]

const navigateTo = (key: string) => {
  currentViewKey.value = key
}

const fetchStats = async () => {
  try {
    const res = await axios.get('/api/stats/summary')
    if (res.data && typeof res.data === 'object') {
      stats.value = {
        movies: res.data.movies ?? 0,
        series: res.data.series ?? 0,
        duplicates: res.data.duplicates ?? 0,
        status: res.data.status ?? 'idle'
      }
    }
  } catch (e) {
    console.error('Failed to fetch stats:', e)
  }
}

onMounted(() => {
  fetchStats()
  setInterval(fetchStats, 10000)
})
</script>