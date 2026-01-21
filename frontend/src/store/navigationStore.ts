import { ref, watch } from 'vue'

const SAVE_KEY = 'lens_current_view'
const MENU_SETTINGS_KEY = 'lens_menu_settings'
const AUTH_SAVE_KEY = 'lens_access_token'

// 从本地存储恢复上次停留的页面，默认显示仪表盘
export const currentViewKey = ref(localStorage.getItem(SAVE_KEY) || 'DashboardView')
export const isLoggedIn = ref(!!localStorage.getItem(AUTH_SAVE_KEY))
export const uiAuthEnabled = ref(true)
export const username = ref(localStorage.getItem('lens_username') || '')

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
  { key: 'BackupManagerView', visible: true },
  { key: 'SiteNavView', visible: true },
  { key: 'ExternalControlView', visible: true },
  { key: 'AccountManagerView', visible: true }
]

const loadMenuSettings = (): MenuSetting[] => {
  const saved = localStorage.getItem(MENU_SETTINGS_KEY)
  if (!saved) return [...defaultSettings]
  
  try {
    const parsed: MenuSetting[] = JSON.parse(saved)
    // 关键逻辑：将缺失的默认项合并到已保存的设置中
    const missingItems = defaultSettings.filter(
      def => !parsed.some(item => item.key === def.key)
    )
    if (missingItems.length > 0) {
      return [...parsed, ...missingItems]
    }
    return parsed
  } catch {
    return [...defaultSettings]
  }
}

export const menuSettings = ref<MenuSetting[]>(loadMenuSettings())

// 监听变化并自动持久化
watch(currentViewKey, (val) => {
  localStorage.setItem(SAVE_KEY, val)
})

watch(menuSettings, (val) => {
  localStorage.setItem(MENU_SETTINGS_KEY, JSON.stringify(val))
}, { deep: true })

export const loginSuccess = (token: string, user: string) => {
  localStorage.setItem(AUTH_SAVE_KEY, token)
  localStorage.setItem('lens_username', user)
  isLoggedIn.value = true
  username.value = user
}

export const logout = () => {
  localStorage.removeItem(AUTH_SAVE_KEY)
  localStorage.removeItem('lens_username')
  isLoggedIn.value = false
  username.value = ''
}
