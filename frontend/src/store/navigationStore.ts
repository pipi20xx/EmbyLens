import { ref, watch, computed } from 'vue'

const SAVE_KEY = 'lens_current_view'
const MENU_SETTINGS_KEY = 'lens_menu_settings'
const AUTH_SAVE_KEY = 'lens_access_token'

// 从本地存储恢复上次停留的页面，默认显示仪表盘
export const currentViewKey = ref(localStorage.getItem(SAVE_KEY) || 'DashboardView')
export const activeGroupKey = ref(localStorage.getItem('lens_active_group') || 'group-overview')
export const isLoggedIn = ref(!!localStorage.getItem(AUTH_SAVE_KEY))
export const uiAuthEnabled = ref(true)
export const username = ref(localStorage.getItem('lens_username') || '')

export const isLogConsoleOpen = ref(false)
export const isHomeEntry = ref(false)

// --- History Management (Back/Forward Support) ---
let isPopping = false

if (typeof window !== 'undefined') {
  // Ensure we have an initial state
  const initialKey = localStorage.getItem(SAVE_KEY) || 'DashboardView'
  if (!history.state?.lensView) {
    history.replaceState({ lensView: initialKey }, '', '#' + initialKey)
  }

  window.addEventListener('popstate', (event) => {
    // Handle history navigation (Back/Forward buttons)
    if (event.state && event.state.lensView) {
      isPopping = true
      currentViewKey.value = event.state.lensView
      Promise.resolve().then(() => { isPopping = false })
    } 
    // Handle manual hash change or hash navigation without state
    else if (window.location.hash) {
      const hashKey = window.location.hash.slice(1)
      if (hashKey && hashKey !== currentViewKey.value) {
        isPopping = true
        currentViewKey.value = hashKey
        Promise.resolve().then(() => { isPopping = false })
      }
    }
  })
}

// 菜单布局设置：支持自定义分组和子项归属
export interface MenuGroup {
  key: string
  label: string
  visible: boolean
  items: string[] // 存储子菜单项的 key
}

const MENU_LAYOUT_KEY = 'lens_menu_layout_v2'

const defaultLayout: MenuGroup[] = [
  {
    key: 'group-overview',
    label: '概览控制',
    visible: true,
    items: ['DashboardView', 'SiteNavView']
  },
  {
    key: 'group-media',
    label: '媒体工具',
    visible: true,
    items: ['DedupeView', 'TypeManagerView', 'CleanupToolsView', 'LockManagerView', 'AutoTagsView']
  },
  {
    key: 'group-search',
    label: '查询探索',
    visible: true,
    items: ['EmbyItemQueryView', 'TmdbReverseLookupView', 'TmdbIdSearchView']
  },
  {
    key: 'group-labs',
    label: '实验室',
    visible: true,
    items: ['TmdbLabView', 'BangumiLabView', 'ActorLabView', 'ActorManagerView']
  },
  {
    key: 'group-system',
    label: '系统维护',
    visible: true,
    items: ['TerminalManagerView', 'DockerManagerView', 'ImageBuilderView', 'PostgresManagerView', 'BackupManagerView']
  },
  {
    key: 'group-config',
    label: '配置中心',
    visible: true,
    items: ['WebhookReceiverView', 'NotificationManagerView', 'AccountManagerView', 'ExternalControlView']
  }
]

const loadMenuLayout = (): MenuGroup[] => {
  const saved = localStorage.getItem(MENU_LAYOUT_KEY)
  if (!saved) return JSON.parse(JSON.stringify(defaultLayout))
  
  try {
    const parsed: MenuGroup[] = JSON.parse(saved)
    // 这里可以添加逻辑：如果新增了功能项但在配置中找不到，可以归入一个“未分类”组
    return parsed
  } catch {
    return JSON.parse(JSON.stringify(defaultLayout))
  }
}

export const menuLayout = ref<MenuGroup[]>(loadMenuLayout())

// 兼容旧的 menuSettings（如果其他地方还在用）
export const menuSettings = computed(() => {
  const flat: { key: string, visible: boolean }[] = []
  menuLayout.value.forEach(group => {
    group.items.forEach(itemKey => {
      flat.push({ key: itemKey, visible: group.visible })
    })
  })
  return flat
})

// 保存设置到后端
const saveMenuLayoutToBackend = async (layout: MenuGroup[]) => {
  try {
    const axios = (await import('axios')).default
    await axios.post('/api/system/config', {
      configs: [
        {
          key: 'menu_layout_v2',
          value: JSON.stringify(layout),
          description: '导航菜单自定义布局'
        }
      ]
    })
  } catch (err) { }
}

// 从后端初始化
export const initMenuSettingsFromBackend = async () => {
  try {
    const axios = (await import('axios')).default
    const res = await axios.get('/api/system/config')
    const saved = res.data.menu_layout_v2
    if (saved) {
      menuLayout.value = JSON.parse(saved)
    }
  } catch (err) { }
}

watch(menuLayout, (val) => {
  localStorage.setItem(MENU_LAYOUT_KEY, JSON.stringify(val))
  if (isLoggedIn.value) {
    saveMenuLayoutToBackend(val)
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
