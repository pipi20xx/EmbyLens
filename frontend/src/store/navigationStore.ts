import { ref, watch } from 'vue'

const SAVE_KEY = 'embylens_current_view'
const MENU_SETTINGS_KEY = 'embylens_menu_settings'

// 从本地存储恢复上次停留的页面，默认显示仪表盘
export const currentViewKey = ref(localStorage.getItem(SAVE_KEY) || 'DashboardView')

export const isLogConsoleOpen = ref(false)

// 菜单设置：包含排序和显示隐藏
export interface MenuSetting {
  key: string
  visible: boolean
}

const defaultSettings: MenuSetting[] = [
  { key: 'DashboardView', visible: true },
  { key: 'DedupeView', visible: true },
  { key: 'TypeManagerView', visible: true },
  { key: 'CleanupToolsView', visible: true },
  { key: 'LockManagerView', visible: true },
  { key: 'EmbyItemQueryView', visible: true },
  { key: 'TmdbReverseLookupView', visible: true },
  { key: 'TmdbIdSearchView', visible: true },
  { key: 'TmdbLabView', visible: true },
  { key: 'BangumiLabView', visible: true },
  { key: 'ActorLabView', visible: true },
  { key: 'ActorManagerView', visible: true },
  { key: 'WebhookReceiverView', visible: true },
  { key: 'AutoTagsView', visible: true },
  { key: 'DockerManagerView', visible: true },
  { key: 'PostgresManagerView', visible: true },
  { key: 'SiteNavView', visible: true }
]

const savedSettings = localStorage.getItem(MENU_SETTINGS_KEY)
export const menuSettings = ref<MenuSetting[]>(savedSettings ? JSON.parse(savedSettings) : defaultSettings)

// 监听变化并自动持久化
watch(currentViewKey, (val) => {
  localStorage.setItem(SAVE_KEY, val)
})

watch(menuSettings, (val) => {
  localStorage.setItem(MENU_SETTINGS_KEY, JSON.stringify(val))
}, { deep: true })