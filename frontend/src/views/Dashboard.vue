<template>
  <div class="dashboard-page">
    <n-space vertical size="large">
      <n-grid :x-gap="12" :y-gap="12" :cols="4" item-responsive responsive="screen">
        <n-gi span="4 m:2 l:1">
          <n-card bordered size="small">
            <n-statistic label="电影总数" :value="stats.movies">
              <template #prefix><n-icon><MovieIcon /></n-icon></template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi span="4 m:2 l:1">
          <n-card bordered size="small">
            <n-statistic label="剧集总数" :value="stats.series">
              <template #prefix><n-icon><SeriesIcon /></n-icon></template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi span="4 m:2 l:1">
          <n-card bordered size="small">
            <n-statistic label="重复组" :value="stats.duplicates">
              <template #prefix><n-icon><DedupeIcon /></n-icon></template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi span="4 m:2 l:1">
          <n-card bordered size="small">
            <n-statistic label="库状态" :value="stats.status === 'connected' ? '就绪' : '待同步'">
              <template #prefix>
                <n-icon :color="stats.status === 'connected' ? 'var(--primary-color)' : '#f0a020'">
                  <StatusIcon />
                </n-icon>
              </template>
            </n-statistic>
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
import { ref, onMounted } from 'vue'
import { NSpace, NGrid, NGi, NCard, NStatistic, NIcon, NText } from 'naive-ui'
import axios from 'axios'
import {
  MovieRound as MovieIcon,
  LiveTvRound as SeriesIcon,
  AutoDeleteRound as DedupeIcon,
  SensorsRound as StatusIcon
} from '@vicons/material'

const stats = ref({
  movies: 0,
  series: 0,
  duplicates: 0,
  status: 'idle'
})

const fetchStats = async () => {
  try {
    const res = await axios.get('/api/stats/summary')
    stats.value = res.data
  } catch (e) {}
}

onMounted(() => {
  fetchStats()
  setInterval(fetchStats, 10000)
})
</script>