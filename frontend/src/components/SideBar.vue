<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { 
  NLayoutSider, 
  NMenu, 
  NScrollbar,
  NButton,
  NDropdown,
  NIcon,
  NSpace,
  NTooltip
} from 'naive-ui'
import { menuOptions as originalOptions, SettingIcon, ConsoleIcon, ThemeIcon } from '../config/menu'
import AppLogo from './AppLogo.vue'
import MenuManagerModal from './MenuManagerModal.vue'
import { currentViewKey, isLogConsoleOpen, menuSettings, isLoggedIn, logout, uiAuthEnabled } from '../store/navigationStore'
import { ThemeType } from '../hooks/useTheme'
import { 
  DragHandleOutlined as MenuManageIcon,
  ExitToAppOutlined as LogoutIcon,
  DnsOutlined as ServerIcon
} from '@vicons/material'
import { useRouter } from 'vue-router'
import { servers, activeServerId, fetchServers, activateServer } from '../store/serverStore'
import { onMounted, h } from 'vue'
import { useMessage } from 'naive-ui'

const props = defineProps<{
  themeType: ThemeType
  themeOptions: { label: string, key: string }[]
}>()

const emit = defineEmits(['update:themeType'])
const router = useRouter()
const message = useMessage()

const collapsed = ref(localStorage.getItem('lens_sidebar_collapsed') === 'true')
const showMenuManager = ref(false)

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
    message.success(`已切换至服务器: ${activeServerName.value}`)
    // 强制刷新页面以应用新服务器配置，或者在各自组件中监听
    window.location.reload()
  }
}

onMounted(() => {
  fetchServers()
})

const handleLogout = () => {
  logout()
  router.push('/login')
}

// 根据设置动态计算菜单项
const filteredMenuOptions = computed(() => {
  const visibleKeys = menuSettings.value.filter(s => s.visible).map(s => s.key)
  const sortedOptions = [...menuSettings.value]
    .map(setting => originalOptions.find(opt => opt.key === setting.key))
    .filter(opt => opt && visibleKeys.includes(opt.key as string))
  
  return sortedOptions as any[]
})

watch(collapsed, (val) => {
  localStorage.setItem('lens_sidebar_collapsed', String(val))
})

const handleThemeSelect = (val: string) => {
  emit('update:themeType', val as ThemeType)
}
</script>

<template>
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
    :class="{ 'main-sider': true, 'transparent-sider': currentViewKey === 'SiteNavView' }"
  >
    <div class="logo-container">
      <n-space align="center" :size="10">
        <app-logo :size="28" :theme="themeType" />
      <div class="sidebar-footer" v-if="!collapsed">
        <div class="version-tag">v2.1.6</div>
      </div>
      </n-space>
    </div>

    <div class="server-switcher" v-if="servers.length > 0">
      <n-dropdown trigger="click" :options="serverOptions" @select="handleServerSelect">
        <n-button quaternary block size="small" :style="{ padding: collapsed ? '0' : '0 12px', justifyContent: 'flex-start' }">
          <template #icon>
            <n-icon color="var(--primary-color)"><ServerIcon /></n-icon>
          </template>
          <span v-if="!collapsed" class="server-name-text">{{ activeServerName }}</span>
        </n-button>
      </n-dropdown>
    </div>
    
    <n-scrollbar style="flex-grow: 1;">
      <n-menu
        v-model:value="currentViewKey"
        :collapsed-width="56"
        :collapsed-icon-size="18"
        :options="filteredMenuOptions"
        :indent="14"
      />
    </n-scrollbar>

    <div class="sidebar-footer">
      <n-space :vertical="collapsed" justify="space-around" align="center" :size="[4, 8]">
        <n-tooltip placement="right" v-if="collapsed">
          <template #trigger>
            <n-button circle secondary size="small" @click="showMenuManager = true">
              <template #icon><n-icon><MenuManageIcon /></n-icon></template>
            </n-button>
          </template>
          菜单排序
        </n-tooltip>
        <n-button v-else circle secondary size="small" @click="showMenuManager = true">
          <template #icon><n-icon><MenuManageIcon /></n-icon></template>
        </n-button>

        <n-dropdown trigger="click" :options="themeOptions" @select="handleThemeSelect">
          <n-button circle secondary size="small" :type="themeType === 'purple' ? 'primary' : 'info'">
            <template #icon><n-icon><ThemeIcon /></n-icon></template>
          </n-button>
        </n-dropdown>
        <n-button circle secondary size="small" :type="currentViewKey === 'SettingsView' ? 'primary' : 'default'" @click="currentViewKey = 'SettingsView'">
          <template #icon><n-icon><SettingIcon /></n-icon></template>
        </n-button>
        <n-button circle secondary size="small" type="info" @click="isLogConsoleOpen = true">
          <template #icon><n-icon><ConsoleIcon /></n-icon></template>
        </n-button>
        <n-button 
          v-if="isLoggedIn && uiAuthEnabled"
          circle 
          secondary 
          size="small" 
          type="error" 
          @click="handleLogout"
        >
          <template #icon><n-icon><LogoutIcon /></n-icon></template>
        </n-button>
      </n-space>
    </div>

    <MenuManagerModal v-model:show="showMenuManager" />
  </n-layout-sider>
</template>

<style scoped>
.main-sider { background-color: var(--sidebar-bg-color); border-right: 1px solid rgba(255, 255, 255, 0.06) !important; transition: background-color 0.3s; }
.main-sider.transparent-sider { background-color: rgba(15, 15, 20, 0.6) !important; backdrop-filter: blur(10px); }
.logo-container { display: flex; align-items: center; padding: 12px 16px; height: 60px; }
.logo-info { display: flex; flex-direction: column; justify-content: center; }
.logo-text { font-weight: 800; font-size: 1.1rem; color: var(--primary-color); line-height: 1.2; letter-spacing: 0.5px; }
.version-tag { font-size: 0.7rem; color: var(--text-color); opacity: 0.5; font-family: var(--font-mono); margin-top: 0px; }
.server-switcher { padding: 4px 8px 12px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
.server-name-text { font-size: 0.85rem; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 120px; }
.sidebar-footer { padding: 12px 8px; border-top: 1px solid var(--border-color); }
</style>