<script setup lang="ts">
import { 
  NConfigProvider, 
  NDialogProvider, 
  NMessageProvider, 
  NLayout, 
  NLayoutContent, 
  NLayoutHeader,
  darkTheme,
  NGlobalStyle,
  NModal,
  NCard,
  NSpace,
  NButton,
  NIcon,
  NDropdown,
  NTooltip,
  NAvatar,
  NText,
  NScrollbar,
  NTag
} from 'naive-ui'

import AppLogo from './components/AppLogo.vue'
import LogConsole from './components/LogConsole.vue'
import MenuManagerModal from './components/MenuManagerModal.vue'
import LoginView from './views/Login.vue'
import {
  currentViewKey, 
  activeGroupKey,
  isLogConsoleOpen, 
  isLoggedIn, 
  uiAuthEnabled,
  isHomeEntry,
  menuLayout,
  username,
  logout,
  initMenuSettingsFromBackend,
  isHeaderSticky
} from './store/navigationStore'
import { useTheme } from './hooks/useTheme'
import { viewMap } from './config/views'
import { allMenuItems, SettingIcon, ConsoleIcon, ThemeIcon } from './config/menu'
import { 
  ExitToAppOutlined as LogoutIcon,
  DnsOutlined as ServerIcon,
  DragHandleOutlined as MenuManageIcon,
  PersonOutlined as UserIcon,
  LockOpenOutlined as UnlockedIcon
} from '@vicons/material'
import { servers, activeServerId, fetchServers, activateServer } from './store/serverStore'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { watch, computed, onMounted, ref, h } from 'vue'

// --- Theme System ---
const { currentThemeType, themeOverrides, themeOptions } = useTheme()
const router = useRouter()
const showMenuManager = ref(false)

// --- UI Layout State ---
const shouldHideNav = computed(() => {
  return currentViewKey.value === 'SiteNavView' && isHomeEntry.value
})

// 计算当前激活分组下的可见子项
const currentSubMenuItems = computed(() => {
  if (!isLoggedIn.value) return []
  const activeGroup = menuLayout.value.find(g => g.key === activeGroupKey.value)
  if (!activeGroup || !activeGroup.items) return []
  
  return activeGroup.items.map(itemKey => {
    return allMenuItems.find(m => m.key === itemKey)
  }).filter(Boolean) as any[]
})

// 过滤后的主分类
const visibleGroups = computed(() => {
  return menuLayout.value.filter(g => g.visible)
})

// 处理主分类点击
const handleGroupClick = (group: any) => {
  activeGroupKey.value = group.key
  localStorage.setItem('lens_active_group', group.key)
  
  if (group.type === 'item') {
    currentViewKey.value = group.key
  } else if (group.items && group.items.length > 0) {
    currentViewKey.value = group.items[0]
  }
}

// 监听 currentViewKey 变化
watch(currentViewKey, (newKey) => {
  for (const group of menuLayout.value) {
    if (group.type === 'group' && group.items.includes(newKey as string)) {
      if (activeGroupKey.value !== group.key) {
        activeGroupKey.value = group.key
        localStorage.setItem('lens_active_group', group.key)
      }
      break
    }
    if (group.type === 'item' && group.key === newKey) {
      if (activeGroupKey.value !== group.key) {
        activeGroupKey.value = group.key
        localStorage.setItem('lens_active_group', group.key)
      }
      break
    }
  }
}, { immediate: true })

// 用户下拉菜单
const userDropdownOptions = computed(() => [
  { label: '个人中心', key: 'AccountManagerView', icon: () => h(NIcon, null, { default: () => h(UserIcon) }) },
  { type: 'divider', key: 'd1' },
  { label: '退出登录', key: 'logout', icon: () => h(NIcon, null, { default: () => h(LogoutIcon) }) }
])

const handleUserSelect = (key: string) => {
  if (key === 'logout') {
    handleLogout()
  } else {
    currentViewKey.value = key
  }
}

// 服务器选择
const serverOptions = computed(() => {
  return servers.value.map(s => ({
    label: s.name,
    key: s.id,
    icon: () => h(NIcon, null, { default: () => h(ServerIcon) })
  }))
})

const activeServerName = computed(() => {
  const active = servers.value.find(s => s.id === activeServerId.value)
  return active ? active.name : '未选择服务器'
})

const handleServerSelect = async (serverId: string) => {
  const success = await activateServer(serverId)
  if (success) {
    window.location.reload()
  }
}

const handleLogout = () => {
  logout()
  router.push('/login')
}

const handleThemeSelect = (val: string) => {
  currentThemeType.value = val as any
}

onMounted(async () => {
  if (window.location.pathname === '/home') {
    isHomeEntry.value = true
    currentViewKey.value = 'SiteNavView'
    window.history.replaceState({}, '', '/')
  }

  try {
    const res = await axios.get('/api/auth/status')
    const enabled = res.data.ui_auth_enabled === true || res.data.ui_auth_enabled === 'true'
    uiAuthEnabled.value = enabled
    if (!enabled) { isLoggedIn.value = true }
  } catch (err) { }

  if (isLoggedIn.value) {
    fetchServers()
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
        <n-layout 
          position="absolute" 
          style="display: flex; flex-direction: column;"
          :native-scrollbar="false"
        >
          
          <!-- 头部导航区域 - 包含一级和二级 -->
          <div 
            class="navigation-wrapper" 
            :class="{ 'sticky-nav': isHeaderSticky && !shouldHideNav }"
          >
            <!-- 第一级：主顶部导航栏 -->
            <n-layout-header 
              bordered 
              class="app-header" 
              v-if="!shouldHideNav"
            >
              <div class="header-content">
                <div class="header-left">
                  <div class="logo-box" @click="isLoggedIn && (currentViewKey = 'DashboardView')">
                    <app-logo :size="28" :theme="currentThemeType" />
                    <span class="header-title">LENS</span>
                  </div>
                  
                  <n-dropdown v-if="isLoggedIn" trigger="click" :options="serverOptions" @select="handleServerSelect">
                    <n-button quaternary size="small" class="server-btn">
                      <template #icon><n-icon color="var(--primary-color)"><ServerIcon /></n-icon></template>
                      {{ activeServerName }}
                    </n-button>
                  </n-dropdown>
                </div>
                
                <div class="header-center">
                  <n-space :size="4" v-if="isLoggedIn">
                    <n-button 
                      v-for="group in visibleGroups" 
                      :key="group.key"
                      quaternary
                      :type="activeGroupKey === group.key ? 'primary' : 'default'"
                      class="nav-group-btn"
                      @click="handleGroupClick(group)"
                    >
                      {{ group.label }}
                    </n-button>
                  </n-space>
                </div>

                <div class="header-right">
                  <n-space :size="12" align="center">
                    <template v-if="isLoggedIn">
                      <n-tooltip trigger="hover">
                        <template #trigger>
                          <n-button circle quaternary size="small" @click="showMenuManager = true">
                            <template #icon><n-icon><MenuManageIcon /></n-icon></template>
                          </n-button>
                        </template>
                        菜单管理
                      </n-tooltip>

                      <n-dropdown trigger="click" :options="themeOptions" @select="handleThemeSelect">
                        <n-button circle quaternary size="small">
                          <template #icon><n-icon><ThemeIcon /></n-icon></template>
                        </n-button>
                      </n-dropdown>
                      
                      <n-button circle quaternary size="small" :type="currentViewKey === 'SettingsView' ? 'primary' : 'default'" @click="currentViewKey = 'SettingsView'">
                        <template #icon><n-icon><SettingIcon /></n-icon></template>
                      </n-button>

                      <n-button circle quaternary size="small" @click="isLogConsoleOpen = true">
                        <template #icon><n-icon><ConsoleIcon /></n-icon></template>
                      </n-button>

                      <n-dropdown trigger="click" :options="userDropdownOptions" @select="handleUserSelect">
                        <div class="user-info" :class="{ 'no-auth-mode': !uiAuthEnabled }">
                          <n-avatar 
                            round 
                            size="small" 
                            :style="{ backgroundColor: uiAuthEnabled ? 'var(--primary-color)' : '#4ade80' }"
                          >
                            <n-icon><UserIcon v-if="uiAuthEnabled" /><UnlockedIcon v-else /></n-icon>
                          </n-avatar>
                          <div class="user-text-box">
                            <n-text class="username-text">{{ username || 'Admin' }}</n-text>
                            <n-tag v-if="!uiAuthEnabled" size="mini" type="success" :bordered="false" round class="auth-tag">
                              免密
                            </n-tag>
                          </div>
                        </div>
                      </n-dropdown>
                    </template>
                  </n-space>
                </div>
              </div>
            </n-layout-header>

            <!-- 第二级：副导航栏 (子功能 Tab) -->
            <div 
              v-if="isLoggedIn && !shouldHideNav && currentSubMenuItems.length > 0" 
              class="sub-header"
            >
              <n-scrollbar x-scrollable content-style="padding: 0 16px;">
                <div class="sub-nav-tabs">
                  <div 
                    v-for="item in currentSubMenuItems" 
                    :key="item.key"
                    class="sub-nav-item"
                    :class="{ 'active': currentViewKey === item.key }"
                    @click="currentViewKey = item.key"
                  >
                    <n-icon v-if="item.icon" class="sub-nav-icon"><component :is="item.icon" /></n-icon>
                    <span class="sub-nav-label">{{ item.label }}</span>
                  </div>
                </div>
              </n-scrollbar>
            </div>
          </div>

          <!-- 内容区域 -->
          <n-layout-content 
            :content-style="{
              padding: shouldHideNav ? '0' : 'var(--space-md)',
              minHeight: '100%',
              display: 'flex',
              flexDirection: 'column',
              backgroundColor: (isLoggedIn && currentViewKey === 'SiteNavView') ? 'transparent' : 'var(--app-bg-color)',
              transition: 'all 0.3s ease'
            }"
          >
            <div class="view-wrapper">
              <template v-if="isLoggedIn">
                <transition name="fade" mode="out-in">
                  <component :is="currentView" :key="currentViewKey" />
                </transition>
              </template>
              <template v-else>
                <div class="login-container"><LoginView /></div>
              </template>
            </div>
          </n-layout-content>
        </n-layout>

        <MenuManagerModal v-model:show="showMenuManager" />
        
        <n-modal v-model:show="isLogConsoleOpen" transform-origin="center">
          <n-card
            style="width: 90vw; max-width: 1400px; height: 85vh;"
            content-style="padding: 0; display: flex; flex-direction: column; height: 100%; overflow: hidden;"
            :bordered="false"
            size="small"
          >
            <LogConsole @close="isLogConsoleOpen = false" />
          </n-card>
        </n-modal>
      </n-message-provider>
    </n-dialog-provider>
  </n-config-provider>
</template>

<style scoped>
.navigation-wrapper {
  z-index: 100;
  width: 100%;
  background-color: var(--sidebar-bg-color);
}

.sticky-nav {
  position: sticky;
  top: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.app-header {
  height: 56px;
  background-color: transparent;
  backdrop-filter: blur(10px);
}

.header-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  gap: 20px;
}

.header-left { display: flex; align-items: center; gap: 16px; flex-shrink: 0; }
.logo-box { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.header-title { font-size: 1.2rem; font-weight: 900; letter-spacing: 1px; color: var(--primary-color); }
.server-btn { font-weight: 600; max-width: 150px; }
.header-center { flex: 1; display: flex; justify-content: center; }

.nav-group-btn {
  font-weight: 700;
  font-size: 0.95rem;
  padding: 0 16px;
  height: 38px;
  border-radius: 8px;
}

.sub-header {
  height: 48px;
  background-color: var(--sub-nav-bg-color);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
}

.sub-nav-tabs { display: flex; align-items: center; height: 100%; gap: 4px; }
.sub-nav-item {
  display: flex; align-items: center; gap: 8px; padding: 0 16px; height: 34px;
  cursor: pointer; border-radius: 6px; transition: all 0.2s; color: var(--text-color);
  opacity: 0.7; white-space: nowrap;
}
.sub-nav-item:hover { background-color: rgba(255, 255, 255, 0.05); opacity: 1; }
.sub-nav-item.active { background-color: var(--primary-color-suppl); color: var(--primary-color); opacity: 1; font-weight: 600; }

.header-right { flex-shrink: 0; }
.user-info { display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 4px 12px; border-radius: 20px; transition: all 0.3s; border: 1px solid transparent; }
.user-info:hover { background-color: rgba(255, 255, 255, 0.05); border-color: rgba(255, 255, 255, 0.1); }
.no-auth-mode:hover { background-color: rgba(74, 222, 128, 0.05); border-color: rgba(74, 222, 128, 0.2); }

.user-text-box { display: flex; align-items: center; gap: 6px; }
.username-text { font-size: 0.9rem; font-weight: 600; }
.auth-tag { font-size: 10px; height: 18px; padding: 0 6px; font-weight: 800; }

.view-wrapper { flex: 1; width: 100%; display: flex; flex-direction: column; }
.login-container { flex: 1; display: flex; align-items: center; justify-content: center; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>