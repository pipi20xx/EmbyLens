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
  MyLocationOutlined as TargetIcon
} from '@vicons/material'

// Views
import DashboardView from './views/Dashboard.vue'
import SettingsView from './views/Settings.vue'
import TypeManagerView from './views/toolkit/TypeManager.vue'
import CleanupToolsView from './views/toolkit/CleanupTools.vue'
import LockManagerView from './views/toolkit/LockManager.vue'
import EmbyItemQueryView from './views/toolkit/EmbyItemQuery.vue'
import TmdbReverseLookupView from './views/toolkit/TmdbReverseLookup.vue'

import LogConsole from './components/LogConsole.vue'
import { currentViewKey, isLogConsoleOpen } from './store/navigationStore'

function renderIcon(icon: Component) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const collapsed = ref(localStorage.getItem('embylens_sidebar_collapsed') === 'true')

// --- Theme System (1:1 align with Anime-Manager) ---
type ThemeType = 'modern' | 'purple'
const currentThemeType = ref<ThemeType>((localStorage.getItem('embylens_theme_type') as ThemeType) || 'purple')
const showLogConsole = isLogConsoleOpen

watch(currentThemeType, (val) => localStorage.setItem('embylens_theme_type', val))
watch(collapsed, (val) => localStorage.setItem('embylens_sidebar_collapsed', String(val)))

const themeOptions = [
  { label: '暗夜紫韵 (Purple)', key: 'purple' },
  { label: '现代极客 (Modern)', key: 'modern' }
]

// 1. 现代极客
const modernOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#705df2',
    primaryColorHover: '#8a7af5',
    primaryColorPressed: '#5946d1',
    borderRadius: '6px',
    cardColor: '#1e1e24',
    bodyColor: '#101014',
    textColorBase: '#ffffff'
  },
  Card: { borderRadius: '10px' },
  Button: { borderRadiusMedium: '6px' }
}

// 2. 暗夜紫韵
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

const themeOverrides = computed(() => {
  const current = currentThemeType.value
  const theme = current === 'purple' ? purpleOverrides : modernOverrides
  
  if (typeof document !== 'undefined') {
    syncThemeVariables(theme)
  }
  
  return theme
})

const syncThemeVariables = (theme: GlobalThemeOverrides) => {
  const root = document.documentElement
  const common = theme.common!
  root.style.setProperty('--app-bg-color', common.bodyColor!)
  root.style.setProperty('--sidebar-bg-color', common.cardColor!)
  root.style.setProperty('--n-primary-color', common.primaryColor!)
}

onMounted(() => {
  // 初始同步一次 CSS 变量
  const initialTheme = currentThemeType.value === 'purple' ? purpleOverrides : modernOverrides
  syncThemeVariables(initialTheme)
})

// --- 菜单配置 ---
const menuOptions: MenuOption[] = [
  { label: '管理仪表盘', key: 'DashboardView', icon: renderIcon(DashboardIcon) },
  { label: '类型映射管理', key: 'TypeManagerView', icon: renderIcon(CategoryIcon) },
  { label: '媒体净化清理', key: 'CleanupToolsView', icon: renderIcon(CleanupIcon) },
  { label: '元数据锁定器', key: 'LockManagerView', icon: renderIcon(LockIcon) },
  { label: '项目元数据查询', key: 'EmbyItemQueryView', icon: renderIcon(SearchIcon) },
  { label: '剧集 TMDB 反查', key: 'TmdbReverseLookupView', icon: renderIcon(TargetIcon) },
]

const currentView = computed(() => {
  const views: Record<string, any> = {
    DashboardView, TypeManagerView, CleanupToolsView, LockManagerView, EmbyItemQueryView, TmdbReverseLookupView, SettingsView
  }
  return views[currentViewKey.value] || DashboardView
})
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
            :width="170"
            show-trigger="arrow-circle"
            content-style="padding: 8px 0; display: flex; flex-direction: column; height: 100%;"
            v-model:collapsed="collapsed"
            class="main-sider"
          >
            <div class="logo-container">
              <n-space align="center" :size="10">
                <n-icon size="24" :color="currentThemeType === 'purple' ? '#bb86fc' : '#705df2'"><LensIcon /></n-icon>
                <div v-if="!collapsed" class="logo-text">EmbyLens</div>
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
                <!-- 主题选择 -->
                <n-dropdown 
                  trigger="click" 
                  :options="themeOptions" 
                  @select="val => currentThemeType = val"
                >
                  <n-button circle secondary size="small" :type="currentThemeType === 'purple' ? 'primary' : 'info'">
                    <template #icon><n-icon><ThemeIcon /></n-icon></template>
                  </n-button>
                </n-dropdown>

                <!-- 设置入口 -->
                <n-button 
                  circle 
                  secondary 
                  size="small"
                  :type="currentViewKey === 'SettingsView' ? 'primary' : 'default'"
                  @click="currentViewKey = 'SettingsView'"
                >
                  <template #icon><n-icon><SettingIcon /></n-icon></template>
                </n-button>

                <!-- 实时日志 -->
                <n-button 
                  circle 
                  secondary 
                  size="small"
                  type="info" 
                  @click="showLogConsole = true"
                >
                  <template #icon><n-icon><ConsoleIcon /></n-icon></template>
                </n-button>
              </n-space>
            </div>
          </n-layout-sider>

          <n-layout-content content-style="padding: 16px; min-height: 100vh; display: flex; flex-direction: column; background-color: var(--app-bg-color);">
            <div class="view-wrapper">
              <transition name="fade" mode="out-in">
                <component :is="currentView" />
              </transition>
            </div>
          </n-layout-content>
        </n-layout>

        <n-modal v-model:show="showLogConsole" transform-origin="center">
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
.main-sider {
  background-color: var(--sidebar-bg-color);
  border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
}

.logo-container {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  height: 50px;
}

.logo-text {
  font-weight: 800;
  font-size: 14px;
  color: #eee;
}

.sidebar-footer {
  padding: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.view-wrapper {
  flex: 1;
  width: 100%;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>