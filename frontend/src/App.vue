<script setup lang="ts">
import { ref, computed, h, Component, watch, onMounted } from 'vue'
import { 
  NConfigProvider, 
  NDialogProvider, 
  NMessageProvider, 
  NLayout, 
  NLayoutSider, 
  NLayoutContent, 
  NMenu, 
  NScrollbar,
  NButton,
  NDropdown,
  darkTheme,
  GlobalThemeOverrides,
  NIcon,
  NGlobalStyle,
  NSelect,
  NSpace,
  NModal
} from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import {
  DashboardOutlined as DashboardIcon,
  AutoDeleteOutlined as DedupeIcon,
  SettingsOutlined as SettingIcon,
  TerminalOutlined as ConsoleIcon,
  PaletteOutlined as ThemeIcon,
  CategoryOutlined as CategoryIcon,
  LayersOutlined as CleanupIcon,
  LockOpenOutlined as LockIcon,
  CameraOutlined as LensIcon,
  SearchOutlined as SearchIcon,
  MyLocationOutlined as TargetIcon,
  YoutubeSearchedForOutlined as DeepSearchIcon,
  ScienceOutlined as LabIcon,
  ContactPageOutlined as ActorLabIcon,
  PeopleAltOutlined as ActorIcon,
  SyncAltOutlined as WebhookIcon,
  StorageOutlined as PostgresIcon
} from '@vicons/material'

// Views
import DashboardView from './views/Dashboard.vue'
import SettingsView from './views/Settings.vue'
import TypeManagerView from './views/toolkit/TypeManager.vue'
import CleanupToolsView from './views/toolkit/CleanupTools.vue'
import LockManagerView from './views/toolkit/LockManager.vue'
import EmbyItemQueryView from './views/toolkit/EmbyItemQuery.vue'
import TmdbReverseLookupView from './views/toolkit/TmdbReverseLookup.vue'
import TmdbIdSearchView from './views/toolkit/TmdbIdSearch.vue'
import TmdbLabView from './views/toolkit/TmdbLab.vue'
import ActorLabView from './views/toolkit/ActorLab.vue'
import ActorManagerView from './views/toolkit/ActorManager.vue'
import WebhookReceiverView from './views/toolkit/WebhookReceiver.vue'
import DedupeView from './views/Dedupe.vue'
import AutoTagsView from './views/toolkit/autotags/AutoTagsManager.vue'
import DockerManagerView from './views/toolkit/DockerManager.vue'
import PostgresManagerView from './views/toolkit/PostgresManager.vue'

import LogConsole from './components/LogConsole.vue'
import { currentViewKey, isLogConsoleOpen } from './store/navigationStore'

// 自定义 Docker 图标组件
const DockerIcon = {
  render() {
    return h('svg', { viewBox: '0 0 24 24', fill: 'currentColor' }, [
      h('path', { d: 'M13.983 11.078h2.119c.102 0 .186-.085.186-.188V8.771c0-.103-.084-.188-.186-.188h-2.119c-.103 0-.188.085-.188.188v2.119c0 .103.085.188.188.188zM11.266 11.078h2.119c.102 0 .187-.085.187-.188V8.771c0-.103-.085-.188-.187-.188h-2.119c-.103 0-.188.085-.188.188v2.119c0 .103.085.188.188.188zM13.983 8.199h2.119c.102 0 .186-.084.186-.187V5.892c0-.103-.084-.188-.186-.188h-2.119c-.103 0-.188.085-.188.188v2.119c0 .103.085.187.188.187zM11.266 8.199h2.119c.102 0 .187-.084.187-.187V5.892c0-.103-.085-.188-.187-.188h-2.119c-.103 0-.188.085-.188.188v2.119c0 .103.085.187.188.187zM8.547 11.078h2.119c.103 0 .188-.085.188-.188V8.771c0-.103-.085-.188-.188-.188H8.547c-.103 0-.188.085-.188.188v2.119c0 .103.085.188.188.188zM11.266 5.321h2.119c.102 0 .187-.085.187-.188V3.014c0-.103-.085-.188-.187-.188h-2.119c-.103 0-.188.085-.188.188v2.119c0 .103.085.188.188.188zM8.547 8.199h2.119c.103 0 .188-.084.188-.187V5.892c0-.103-.085-.188-.188-.188H8.547c-.103 0-.188.085-.188.188v2.119c0 .103.085.187.188.187zM5.829 11.078h2.119c.103 0 .188-.085.188-.188V8.771c0-.103-.085-.188-.188-.188H5.829c-.103 0-.188.085-.188.188v2.119c0 .103.085.188.188.188zM16.7 8.199h2.119c.103 0 .188-.084.188-.187V5.892c0-.103-.085-.188-.188-.188H16.7c-.103 0-.188.085-.188.188v2.119c0 .103.085.187.188.187zM22.447 8.059c-1.022 0-2.564.399-3.441 1.435-.19.228-.338.478-.44.733H.683c-.047 0-.083.012-.11.037-.033.025-.05.062-.05.111v.592c0 .19.156.344.349.344l.181.011c.113.666.437 1.298.93 1.802 1.64 1.677 4.531 1.677 6.173 0 1.282-1.313 1.605-3.011 1.314-4.381h1.02c.02.011.039.024.058.042l.023.025a5.75 5.75 0 0 0 .773 1.106c.901.927 2.121 1.391 3.341 1.391 1.22 0 2.441-.464 3.341-1.391.431-.444.748-.96.953-1.523h4.089c.196 0 .355-.158.355-.354v-.711c0-.196-.159-.354-.355-.354z' })
    ])
  }
}

function renderIcon(icon: Component) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const collapsed = ref(localStorage.getItem('embylens_sidebar_collapsed') === 'true')

// --- Theme System ---
type ThemeType = 'modern' | 'purple'
const currentThemeType = ref<ThemeType>((localStorage.getItem('embylens_theme_type') as ThemeType) || 'purple')
const showLogConsole = isLogConsoleOpen

watch(currentThemeType, (val) => localStorage.setItem('embylens_theme_type', val))
watch(collapsed, (val) => localStorage.setItem('embylens_sidebar_collapsed', String(val)))

// --- 配色方案 ---
const purpleOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#bb86fc',
    primaryColorHover: '#d1a8ff',
    primaryColorPressed: '#995df0',
    borderRadius: '10px',
    cardColor: '#120818',
    modalColor: '#180a20',
    bodyColor: '#0b040f',
    textColorBase: '#e0e0e0'
  },
  Card: { borderRadius: '14px' },
  Button: { borderRadiusMedium: '10px' }
}

const modernOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#705df2',
    primaryColorHover: '#8a7af5',
    primaryColorPressed: '#5946d1',
    borderRadius: '6px',
    cardColor: '#1e1e24',
    bodyColor: '#101014',
    modalColor: '#25252b',
    textColorBase: '#ffffff'
  },
  Card: { borderRadius: '10px' },
  Button: { borderRadiusMedium: '6px' }
}

const themeOverrides = computed(() => {
  const overrides = currentThemeType.value === 'purple' ? purpleOverrides : modernOverrides
  if (typeof document !== 'undefined') { syncThemeVariables(overrides) }
  return overrides
})

const syncThemeVariables = (theme: GlobalThemeOverrides) => {
  const root = document.documentElement
  const common = theme.common!
  root.style.setProperty('--primary-color', common.primaryColor!)
  root.style.setProperty('--primary-hover', common.primaryColorHover!)
  root.style.setProperty('--app-bg-color', common.bodyColor!)
  root.style.setProperty('--card-bg-color', common.cardColor!)
  root.style.setProperty('--modal-bg-color', common.modalColor || common.cardColor!)
  root.style.setProperty('--text-color', common.textColorBase!)
  root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.09)')
  root.style.setProperty('--primary-border-color', `${common.primaryColor}4D`) // 30% opacity
}

onMounted(() => {
  const initialTheme = currentThemeType.value === 'purple' ? purpleOverrides : modernOverrides
  syncThemeVariables(initialTheme)
})

// --- 菜单配置 ---
const menuOptions: MenuOption[] = [
  { label: '管理仪表盘', key: 'DashboardView', icon: renderIcon(DashboardIcon) },
  { label: '重复项清理', key: 'DedupeView', icon: renderIcon(DedupeIcon) },
  { label: '类型映射管理', key: 'TypeManagerView', icon: renderIcon(CategoryIcon) },
  { label: '媒体净化清理', key: 'CleanupToolsView', icon: renderIcon(CleanupIcon) },
  { label: '元数据锁定器', key: 'LockManagerView', icon: renderIcon(LockIcon) },
  { label: '项目元数据查询', key: 'EmbyItemQueryView', icon: renderIcon(SearchIcon) },
  { label: '剧集 TMDB 反查', key: 'TmdbReverseLookupView', icon: renderIcon(TargetIcon) },
  { label: 'TMDB ID 深度搜索', key: 'TmdbIdSearchView', icon: renderIcon(DeepSearchIcon) },
  { label: 'TMDB 实验中心', key: 'TmdbLabView', icon: renderIcon(LabIcon) },
  { label: 'TMDB 演员实验室', key: 'ActorLabView', icon: renderIcon(ActorLabIcon) },
  { label: '演员信息维护', key: 'ActorManagerView', icon: renderIcon(ActorIcon) },
  { label: 'Webhook 接收器', key: 'WebhookReceiverView', icon: renderIcon(WebhookIcon) },
  { label: '自动标签助手', key: 'AutoTagsView', icon: renderIcon(CategoryIcon) },
  { label: 'Docker 容器管理', key: 'DockerManagerView', icon: renderIcon(DockerIcon) },
  { label: 'PostgreSQL 管理', key: 'PostgresManagerView', icon: renderIcon(PostgresIcon) },
]

const currentView = computed(() => {
  const views: Record<string, any> = {
    DashboardView, DedupeView, AutoTagsView, TypeManagerView, CleanupToolsView, LockManagerView, EmbyItemQueryView, TmdbReverseLookupView, TmdbIdSearchView, TmdbLabView, ActorLabView, ActorManagerView, WebhookReceiverView, SettingsView, DockerManagerView, PostgresManagerView
  }
  return views[currentViewKey.value] || DashboardView
})

const themeOptions = [
  { label: '暗夜紫韵 (Purple)', key: 'purple' },
  { label: '现代极客 (Modern)', key: 'modern' }
]
</script>

<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-global-style />
    <n-dialog-provider>
      <n-message-provider>
        <n-layout has-sider position="absolute">
          <n-layout-sider
            bordered
            collapse-mode="width"
            :collapsed-width="56"
            :width="210"
            :min-width="150"
            :max-width="400"
            resizable
            show-trigger="arrow-circle"
            content-style="padding: 8px 0; display: flex; flex-direction: column; height: 100%;"
            v-model:collapsed="collapsed"
            class="main-sider"
          >
            <div class="logo-container">
              <n-space align="center" :size="10">
                <n-icon size="24" :color="currentThemeType === 'purple' ? '#bb86fc' : '#705df2'"><LensIcon /></n-icon>
                <div v-if="!collapsed" class="logo-info">
                  <div class="logo-text">EmbyLens</div>
                  <div class="version-tag">v1.0.5</div>
                </div>
              </n-space>
            </div>
            
            <n-scrollbar style="flex-grow: 1;">
              <n-menu
                v-model:value="currentViewKey"
                :collapsed-width="56"
                :collapsed-icon-size="18"
                :options="menuOptions"
                :indent="14"
              />
            </n-scrollbar>

            <div class="sidebar-footer">
              <n-space :vertical="collapsed" justify="space-around" align="center" :size="[4, 8]">
                <n-dropdown trigger="click" :options="themeOptions" @select="val => currentThemeType = val">
                  <n-button circle secondary size="small" :type="currentThemeType === 'purple' ? 'primary' : 'info'">
                    <template #icon><n-icon><ThemeIcon /></n-icon></template>
                  </n-button>
                </n-dropdown>
                <n-button circle secondary size="small" :type="currentViewKey === 'SettingsView' ? 'primary' : 'default'" @click="currentViewKey = 'SettingsView'">
                  <template #icon><n-icon><SettingIcon /></n-icon></template>
                </n-button>
                <n-button circle secondary size="small" type="info" @click="isLogConsoleOpen = true">
                  <template #icon><n-icon><ConsoleIcon /></n-icon></template>
                </n-button>
              </n-space>
            </div>
          </n-layout-sider>

          <n-layout-content content-style="padding: 16px; min-height: 100vh; display: flex; flex-direction: column; background-color: var(--app-bg-color);">
            <div class="view-wrapper">
              <component :is="currentView" :key="currentViewKey" />
            </div>
          </n-layout-content>
        </n-layout>

        <n-modal v-model:show="isLogConsoleOpen" transform-origin="center">
          <n-card
            style="width: 96vw; height: 96vh; display: flex; flex-direction: column;"
            content-style="padding: 0; display: flex; flex-direction: column; height: 100%; overflow: hidden;"
            :bordered="false"
            size="small"
          >
            <LogConsole />
          </n-card>
        </n-modal>

      </n-message-provider>
    </n-dialog-provider>
  </n-config-provider>
</template>

<style scoped>
.main-sider { background-color: var(--sidebar-bg-color); border-right: 1px solid rgba(255, 255, 255, 0.06) !important; }
.logo-container { display: flex; align-items: center; padding: 12px 16px; height: 50px; }
.logo-info { display: flex; flex-direction: column; justify-content: center; }
.logo-text { font-weight: 800; font-size: 14px; color: #eee; line-height: 1.2; }
.version-tag { font-size: 10px; color: rgba(255, 255, 255, 0.4); font-family: monospace; margin-top: -2px; }
.sidebar-footer { padding: 8px; border-top: 1px solid rgba(255, 255, 255, 0.06); }
.view-wrapper { flex: 1; width: 100%; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
