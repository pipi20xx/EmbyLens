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
        <!-- EMBY 核心功能区 -->
        <n-gi span="24 m:16">
          <n-space vertical size="large">
            <n-card title="EMBY 功能快捷入口" segmented size="small">
              <n-grid :x-gap="8" :y-gap="8" :cols="2" item-responsive>
                <n-gi v-for="tool in embyTools" :key="tool.key">
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

            <n-card title="网站元数据查询" segmented size="small">
              <n-grid :x-gap="8" :y-gap="8" :cols="2" item-responsive>
                <n-gi v-for="tool in metadataTools" :key="tool.key">
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

            <n-card title="其他工具快捷入口" segmented size="small">
              <n-grid :x-gap="8" :y-gap="8" :cols="2" item-responsive>
                <n-gi v-for="tool in otherTools" :key="tool.key">
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
          </n-space>
        </n-gi>

        <!-- 系统信息区 -->
        <n-gi span="24 m:8">
          <n-card title="系统状态" segmented size="small">
            <n-list size="small">
              <n-list-item>
                <n-space justify="space-between">
                  <n-text depth="3">当前版本</n-text>
                  <n-space :size="4" align="center">
                    <n-tag size="small" type="primary" quaternary>{{ versionInfo.current }}</n-tag>
                    <n-tag v-if="!versionInfo.has_update" size="small" type="success" quaternary>最新</n-tag>
                    <n-tag v-else size="small" type="error" quaternary>有更新</n-tag>
                  </n-space>
                </n-space>
              </n-list-item>
              <n-list-item>
                <n-space justify="space-between" align="center">
                  <n-text depth="3">远端镜像 (DockerHub)</n-text>
                  <n-space :size="8" align="center">
                    <n-text style="font-size: 13px; font-family: monospace">{{ versionInfo.latest }}</n-text>
                    <n-button 
                      v-if="versionInfo.docker_hub"
                      text 
                      tag="a" 
                      :href="versionInfo.docker_hub" 
                      target="_blank" 
                      type="primary"
                    >
                      <n-icon size="16"><DockerIcon /></n-icon>
                    </n-button>
                  </n-space>
                </n-space>
              </n-list-item>
              <n-list-item>
                <n-space justify="space-between">
                  <n-text depth="3">后端连接</n-text>
                  <n-text style="font-family: monospace" :type="stats.status === 'connected' ? 'success' : 'error'">
                    {{ stats.status === 'connected' ? '正常' : '异常' }}
                  </n-text>
                </n-space>
              </n-list-item>
              <n-list-item>
                <n-space justify="space-between">
                  <n-text depth="3">项目源码</n-text>
                  <n-button 
                    text 
                    tag="a" 
                    href="https://github.com/pipi20xx/EmbyLens" 
                    target="_blank" 
                    type="primary"
                    style="font-size: 13px"
                  >
                    GitHub 仓库
                  </n-button>
                </n-space>
              </n-list-item>
              <n-list-item>
                <n-space justify="space-between">
                  <n-text depth="3">运行环境</n-text>
                  <n-tag size="small" type="info" quaternary>Production</n-tag>
                </n-space>
              </n-list-item>
            </n-list>
            <template #footer>
              <n-button block size="small" tertiary type="primary" @click="navigateTo('SettingsView')">
                进入配置中心
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
  NH2, NList, NListItem, NTag, NButton, NTooltip, NBadge
} from 'naive-ui'
import axios from 'axios'
import {
  MovieRound as MovieIcon,
  LiveTvRound as SeriesIcon,
  AutoDeleteRound as DedupeIcon,
  SensorsRound as StatusIcon,
  CategoryRound as CategoryIcon,
  LayersRound as CleanupIcon,
  LockOpenRound as LockIcon,
  SearchRound as QueryIcon,
  MyLocationRound as TargetIcon,
  YoutubeSearchedForRound as DeepSearchIcon,
  ScienceRound as LabIcon,
  ContactPageRound as ActorLabIcon,
  PeopleAltRound as ActorIcon,
  SyncAltRound as WebhookIcon,
  StorageRound as PostgresIcon,
  CameraRound as LensIcon,
  DnsRound as DockerIcon
} from '@vicons/material'
import { currentViewKey } from '../store/navigationStore'

const stats = ref({
  movies: 0,
  series: 0,
  duplicates: 0,
  status: 'idle'
})

const versionInfo = ref({
  current: 'v2.0.0',
  latest: 'v2.0.0',
  has_update: false,
  docker_hub: ''
})

const embyTools = [
  { 
    label: '类型映射管理', 
    key: 'TypeManagerView', 
    icon: markRaw(CategoryIcon), 
    desc: '配置媒体库类型与分类规则' 
  },
  { 
    label: '重复项清理', 
    key: 'DedupeView', 
    icon: markRaw(DedupeIcon), 
    desc: '扫描并合并库中的重复视频' 
  },
  { 
    label: '媒体净化清理', 
    key: 'CleanupToolsView', 
    icon: markRaw(CleanupIcon), 
    desc: '清空演职员与修复剧集类型' 
  },
  { 
    label: '元数据锁定器', 
    key: 'LockManagerView', 
    icon: markRaw(LockIcon), 
    desc: '批量锁定或解锁元数据字段' 
  },
  { 
    label: '项目元数据查询', 
    key: 'EmbyItemQueryView', 
    icon: markRaw(QueryIcon), 
    desc: '深入查看 Emby 原始元数据' 
  },
  { 
    label: '剧集 TMDB 反查', 
    key: 'TmdbReverseLookupView', 
    icon: markRaw(TargetIcon), 
    desc: '根据文件名反查 TMDB 编号' 
  },
  { 
    label: 'TMDB ID 深度搜索', 
    key: 'TmdbIdSearchView', 
    icon: markRaw(DeepSearchIcon), 
    desc: '通过 ID 精确抓取媒体信息' 
  },
  { 
    label: '演员信息维护', 
    key: 'ActorManagerView', 
    icon: markRaw(ActorIcon), 
    desc: '同步与修复演员头像和资料' 
  },
  { 
    label: '自动标签助手', 
    key: 'AutoTagsView', 
    icon: markRaw(CategoryIcon), 
    desc: '根据规则自动匹配媒体标签' 
  }
]

const metadataTools = [
  { 
    label: 'TMDB 实验中心', 
    key: 'TmdbLabView', 
    icon: markRaw(LabIcon), 
    desc: 'TMDB 数据抓取与结构化预览' 
  },
  { 
    label: 'Bangumi 实验室', 
    key: 'BangumiLabView', 
    icon: markRaw(LabIcon), 
    desc: '番剧元数据查询与分拣参考' 
  },
  { 
    label: 'TMDB 演员实验室', 
    key: 'ActorLabView', 
    icon: markRaw(ActorLabIcon), 
    desc: '演员资料深度抓取与探针' 
  }
]

const otherTools = [
  { 
    label: 'Docker 容器管理', 
    key: 'DockerManagerView', 
    icon: markRaw(DockerIcon), 
    desc: '本地与远程 Docker 容器运维' 
  },
  { 
    label: 'PostgreSQL 管理', 
    key: 'PostgresManagerView', 
    icon: markRaw(PostgresIcon), 
    desc: '数据库实例、备份与还原管理' 
  },
  { 
    label: '站点导航页', 
    key: 'SiteNavView', 
    icon: markRaw(LensIcon), 
    desc: '私有化沉浸式聚合导航首页' 
  },
  { 
    label: 'Webhook 接收器', 
    key: 'WebhookReceiverView', 
    icon: markRaw(WebhookIcon), 
    desc: 'Webhook 事件接收与测试工具' 
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

const fetchVersion = async () => {
  try {
    const res = await axios.get('/api/system/version')
    if (res.data) {
      versionInfo.value = res.data
    }
  } catch (e) {
    console.error('Failed to fetch version:', e)
  }
}

onMounted(() => {
  fetchStats()
  fetchVersion()
  setInterval(fetchStats, 10000)
})
</script>