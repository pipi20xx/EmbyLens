import { ref, watch, computed } from 'vue'

const SAVE_KEY = 'lens_current_view'
const MENU_SETTINGS_KEY = 'lens_menu_settings'
const AUTH_SAVE_KEY = 'lens_access_token'
const ACTIVE_GROUP_KEY = 'lens_active_group'

// 1. 初始化状态逻辑
const initialView = localStorage.getItem(SAVE_KEY) || 'DashboardView'
const initialGroup = localStorage.getItem(ACTIVE_GROUP_KEY) || 'DashboardView'

export const currentViewKey = ref(initialView)
export const activeGroupKey = ref(initialGroup)
export const isLoggedIn = ref(!!localStorage.getItem(AUTH_SAVE_KEY))
export const uiAuthEnabled = ref(true)
export const username = ref(localStorage.getItem('lens_username') || '')

export const isLogConsoleOpen = ref(false)
export const isHomeEntry = ref(false)

// --- 2. History Management (支持鼠标侧键 & 浏览器后退) ---
let isPopping = false

if (typeof window !== 'undefined') {
  // 初始状态注入
  if (!history.state?.lensView) {
    history.replaceState({ lensView: currentViewKey.value }, '', '#' + currentViewKey.value)
  }

  window.addEventListener('popstate', (event) => {
    if (event.state && event.state.lensView) {
      isPopping = true
      currentViewKey.value = event.state.lensView
      // 在当前宏任务结束后重置标志，确保 watch 不会重复 pushState
      setTimeout(() => { isPopping = false }, 0)
    }
  })
}

// 监听视图变化：持久化到 LocalStorage 并 同步到浏览器 History
watch(currentViewKey, (newVal) => {
  localStorage.setItem(SAVE_KEY, newVal)
  
  if (!isPopping) {
    history.pushState({ lensView: newVal }, '', '#' + newVal)
  }
})

// 监听分组变化：持久化
watch(activeGroupKey, (newVal) => {
  localStorage.setItem(ACTIVE_GROUP_KEY, newVal)
})

// --- 3. 菜单布局逻辑 ---
export interface MenuGroup {
  key: string
  label: string
  visible: boolean
  type: 'group' | 'item'
  items: string[]
}

const MENU_LAYOUT_KEY = 'lens_menu_layout_v2'
const STICKY_HEADER_KEY = 'lens_sticky_header'

export const isHeaderSticky = ref(localStorage.getItem(STICKY_HEADER_KEY) === 'true')

watch(isHeaderSticky, (val) => {
  localStorage.setItem(STICKY_HEADER_KEY, String(val))
})

export const defaultLayout: MenuGroup[] = [
  {
    key: 'DashboardView',
    label: '管理仪表盘',
    visible: true,
    type: 'item',
    items: []
  },
  {
    key: 'SiteNavView',
    label: '站点导航页',
    visible: true,
    type: 'item',
    items: []
  },
  {
    key: 'group-emby',
    label: 'EMBY工具',
    visible: true,
    type: 'group',
    items: [
      'EmbyItemQueryView', 
      'TmdbReverseLookupView', 
      'TmdbIdSearchView',
      'DedupeView', 
      'TypeManagerView', 
      'CleanupToolsView', 
      'LockManagerView', 
      'AutoTagsView'
    ]
  },
  {
    key: 'group-labs',
    label: '实验室',
    visible: true,
    type: 'group',
    items: ['TmdbLabView', 'BangumiLabView', 'ActorLabView', 'ActorManagerView']
  },
  {
    key: 'group-others',
    label: '其他工具',
    visible: true,
    type: 'group',
    items: ['TerminalManagerView', 'BookmarkManagerView', 'DockerManagerView', 'ImageBuilderView', 'PostgresManagerView', 'BackupManagerView']
  },
  {
    key: 'group-config',
    label: '配置中心',
    visible: true,
    type: 'group',
    items: ['WebhookReceiverView', 'NotificationManagerView', 'AccountManagerView', 'ExternalControlView']
  }
]

const loadMenuLayout = (): MenuGroup[] => {
  const saved = localStorage.getItem(MENU_LAYOUT_KEY)
  if (!saved) return JSON.parse(JSON.stringify(defaultLayout))
  
  try {
    const parsed: MenuGroup[] = JSON.parse(saved)
    return parsed.map(item => ({
      ...item,
      type: item.type || 'group',
      items: item.items || []
    }))
  } catch {
    return JSON.parse(JSON.stringify(defaultLayout))
  }
}

export const menuLayout = ref<MenuGroup[]>(loadMenuLayout())

export const menuSettings = computed(() => {
  const flat: { key: string, visible: boolean }[] = []
  menuLayout.value.forEach(group => {
    if (group.type === 'item') {
      flat.push({ key: group.key, visible: group.visible })
    } else {
      group.items.forEach(itemKey => {
        flat.push({ key: itemKey, visible: group.visible })
      })
    }
  })
  return flat
})

export const saveMenuLayoutToBackend = async (layout: MenuGroup[]) => {
  const axios = (await import('axios')).default
  return await axios.post('/api/system/config', {
    configs: [
      {
        key: 'menu_layout_v2',
        value: JSON.stringify(layout),
        description: '导航菜单自定义布局'
      }
    ]
  })
}

export const initMenuSettingsFromBackend = async () => {
  try {
    const axios = (await import('axios')).default
    const res = await axios.get('/api/system/config')
    const saved = res.data.menu_layout_v2
    if (saved) {
      const parsed: MenuGroup[] = JSON.parse(saved)
      menuLayout.value = parsed.map(item => ({
        ...item,
        type: item.type || 'group',
        items: item.items || []
      }))
    }
  } catch (err) { }
}

watch(menuLayout, (val) => {
  localStorage.setItem(MENU_LAYOUT_KEY, JSON.stringify(val))
  if (isLoggedIn.value) {
    saveMenuLayoutToBackend(val).catch(() => {})
  }
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
