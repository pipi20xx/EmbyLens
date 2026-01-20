<script setup lang="ts">
import { ref, watch } from 'vue'
import { 
  NLayoutSider, 
  NMenu, 
  NScrollbar,
  NButton,
  NDropdown,
  NIcon,
  NSpace
} from 'naive-ui'
import { menuOptions, SettingIcon, ConsoleIcon, ThemeIcon } from '../config/menu'
import AppLogo from './AppLogo.vue'
import { currentViewKey, isLogConsoleOpen } from '../store/navigationStore'
import { ThemeType } from '../hooks/useTheme'

const props = defineProps<{
  themeType: ThemeType
  themeOptions: { label: string, key: string }[]
}>()

const emit = defineEmits(['update:themeType'])

const collapsed = ref(localStorage.getItem('embylens_sidebar_collapsed') === 'true')

watch(collapsed, (val) => {
  localStorage.setItem('embylens_sidebar_collapsed', String(val))
})

const handleThemeSelect = (val: string) => {
  emit('update:themeType', val)
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
        <div v-if="!collapsed" class="logo-info">
          <div class="logo-text">EmbyLens</div>
          <div class="version-tag">v1.0.7</div>
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
      </n-space>
    </div>
  </n-layout-sider>
</template>

<style scoped>
.main-sider { background-color: var(--sidebar-bg-color); border-right: 1px solid rgba(255, 255, 255, 0.06) !important; transition: background-color 0.3s; }
.main-sider.transparent-sider { background-color: rgba(15, 15, 20, 0.6) !important; backdrop-filter: blur(10px); }
.logo-container { display: flex; align-items: center; padding: 12px 16px; height: 50px; }
.logo-info { display: flex; flex-direction: column; justify-content: center; }
.logo-text { font-weight: 800; font-size: 14px; color: #eee; line-height: 1.2; }
.version-tag { font-size: 10px; color: rgba(255, 255, 255, 0.4); font-family: monospace; margin-top: -2px; }
.sidebar-footer { padding: 8px; border-top: 1px solid rgba(255, 255, 255, 0.06); }
</style>
