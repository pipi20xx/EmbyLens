<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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
import LoginView from './views/Login.vue'
import { 
  currentViewKey, 
  isLogConsoleOpen, 
  isLoggedIn, 
  uiAuthEnabled,
  isHomeEntry,
  initMenuSettingsFromBackend 
} from './store/navigationStore'
import { useTheme } from './hooks/useTheme'
import { viewMap } from './config/views'
import axios from 'axios'

// --- Theme System ---
const { currentThemeType, themeOverrides, themeOptions } = useTheme()

// --- UI Layout State ---
const shouldHideSideBar = computed(() => {
  return currentViewKey.value === 'SiteNavView' && isHomeEntry.value
})

onMounted(async () => {
  // --- 路径入口检测 ---
  if (window.location.pathname === '/home') {
    isHomeEntry.value = true
    currentViewKey.value = 'SiteNavView'
    window.history.replaceState({}, '', '/')
  }

  // --- 认证状态同步 ---
  try {
    const res = await axios.get('/api/auth/status')
    const enabled = res.data.ui_auth_enabled === true || res.data.ui_auth_enabled === 'true'
    uiAuthEnabled.value = enabled
    if (!enabled) {
      isLoggedIn.value = true
    }
  } catch (err) { }

  // --- 初始化菜单设置 ---
  if (isLoggedIn.value) {
    initMenuSettingsFromBackend()
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
        <template v-if="isLoggedIn">
          <n-layout has-sider position="absolute">
            <SideBar 
              v-if="!shouldHideSideBar"
              v-model:themeType="currentThemeType" 
              :themeOptions="themeOptions" 
            />

            <n-layout-content :content-style="{
              padding: shouldHideSideBar ? '0' : 'var(--space-lg)',
              minHeight: '100vh',
              display: 'flex',
              flexDirection: 'column',
              backgroundColor: currentViewKey === 'SiteNavView' ? 'transparent' : 'var(--app-bg-color)',
              transition: 'all 0.3s ease'
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
              style="width: 90vw; max-width: 1400px; height: 85vh;"
              content-style="padding: 0; display: flex; flex-direction: column; height: 100%; overflow: hidden;"
              :bordered="false"
              size="small"
            >
              <div style="flex: 1; overflow: hidden; display: flex; flex-direction: column;">
                <LogConsole @close="isLogConsoleOpen = false" />
              </div>
            </n-card>
          </n-modal>
        </template>
        
        <LoginView v-else />

      </n-message-provider>
    </n-dialog-provider>
  </n-config-provider>
</template>

<style scoped>
.view-wrapper { flex: 1; width: 100%; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>