<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { 
  NConfigProvider, 
  NDialogProvider, 
  NMessageProvider, 
  NLayout, 
  NLayoutContent, 
  darkTheme,
  NGlobalStyle,
  NModal,
  NCard
} from 'naive-ui'

import SideBar from './components/SideBar.vue'
import LogConsole from './components/LogConsole.vue'
import { currentViewKey, isLogConsoleOpen } from './store/navigationStore'
import { useTheme } from './hooks/useTheme'
import { viewMap } from './config/views'

// --- Theme System ---
const { currentThemeType, themeOverrides, themeOptions } = useTheme()

onMounted(() => {
  // --- 路径入口检测 ---
  // 如果访问路径是 /home，强制进入站点导航页，忽略记忆
  if (window.location.pathname === '/home') {
    currentViewKey.value = 'SiteNavView'
    window.history.replaceState({}, '', '/')
  }
})

const currentView = computed(() => {
  return viewMap[currentViewKey.value] || viewMap.DashboardView
})
</script>

<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-global-style />
    <n-dialog-provider>
      <n-message-provider>
        <n-layout has-sider position="absolute">
          <SideBar 
            v-model:themeType="currentThemeType" 
            :themeOptions="themeOptions" 
          />

          <n-layout-content :content-style="{
            padding: '16px',
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: currentViewKey === 'SiteNavView' ? 'transparent' : 'var(--app-bg-color)'
          }">
            <div class="view-wrapper">
              <transition name="fade" mode="out-in">
                <component :is="currentView" :key="currentViewKey" />
              </transition>
            </div>
          </n-layout-content>
        </n-layout>

        <n-modal v-model:show="isLogConsoleOpen" transform-origin="center">
          <n-card
            style="width: 96vw; height: 96vh;"
            content-style="padding: 0; display: flex; flex-direction: column; height: 100%; overflow: hidden;"
            :bordered="false"
            size="small"
          >
            <div style="flex: 1; overflow: hidden; display: flex; flex-direction: column;">
              <LogConsole @close="isLogConsoleOpen = false" />
            </div>
          </n-card>
        </n-modal>

      </n-message-provider>
    </n-dialog-provider>
  </n-config-provider>
</template>

<style scoped>
.view-wrapper { flex: 1; width: 100%; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>