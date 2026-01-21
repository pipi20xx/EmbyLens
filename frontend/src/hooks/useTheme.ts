import { ref, computed, watch, onMounted } from 'vue'
import { GlobalThemeOverrides } from 'naive-ui'

export type ThemeType = 'modern' | 'purple' | 'oceanic' | 'crimson'

const purpleOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#a370f7',
    primaryColorHover: '#b794f4',
    primaryColorPressed: '#805ad5',
    borderRadius: '8px',
    cardColor: '#1a1021',
    modalColor: '#241630',
    bodyColor: '#0f0913',
    textColorBase: '#e2e2e9',
    dividerColor: 'rgba(163, 112, 247, 0.15)',
    fontSize: '15px' // 略微增加基础字号以适应 PC
  },
  Card: {
    borderRadius: '12px',
    borderColor: 'rgba(163, 112, 247, 0.2)',
    titleFontSizeMedium: '18px',
    titleFontWeight: '600'
  },
  Button: {
    borderRadiusMedium: '8px',
    fontWeight: '500',
    fontSizeMedium: '14px'
  },
  Input: {
    borderRadius: '8px',
    fontSizeMedium: '14px'
  },
  Menu: {
    fontSize: '15px',
    itemHeight: '42px'
  }
}

const modernOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#6366f1',
    primaryColorHover: '#818cf8',
    primaryColorPressed: '#4f46e5',
    borderRadius: '6px',
    cardColor: '#18181b',
    bodyColor: '#0e0e11',
    modalColor: '#202023',
    textColorBase: '#f4f4f5',
    dividerColor: 'rgba(255, 255, 255, 0.08)',
    fontSize: '15px'
  },
  Card: {
    borderRadius: '10px',
    borderColor: 'rgba(255, 255, 255, 0.08)',
    titleFontSizeMedium: '18px',
    titleFontWeight: '600'
  },
  Button: {
    borderRadiusMedium: '6px',
    fontWeight: '500',
    fontSizeMedium: '14px'
  },
  Menu: {
    fontSize: '15px',
    itemHeight: '42px'
  }
}

const oceanicOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#2dd4bf',
    primaryColorHover: '#5eead4',
    primaryColorPressed: '#14b8a6',
    borderRadius: '8px',
    cardColor: '#0f172a',
    bodyColor: '#020617',
    modalColor: '#1e293b',
    textColorBase: '#f1f5f9',
    dividerColor: 'rgba(45, 212, 191, 0.12)',
    fontSize: '15px'
  },
  Card: {
    borderRadius: '12px',
    borderColor: 'rgba(45, 212, 191, 0.15)',
    titleFontSizeMedium: '18px',
    titleFontWeight: '600'
  },
  Button: {
    borderRadiusMedium: '8px',
    fontSizeMedium: '14px'
  },
  Menu: {
    fontSize: '15px',
    itemHeight: '42px'
  }
}

const crimsonOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#fb7185',
    primaryColorHover: '#fda4af',
    primaryColorPressed: '#f43f5e',
    borderRadius: '8px',
    cardColor: '#181212',
    bodyColor: '#0a0808',
    modalColor: '#1c1616',
    textColorBase: '#fceef0',
    dividerColor: 'rgba(251, 113, 133, 0.12)',
    fontSize: '15px'
  },
  Card: {
    borderRadius: '12px',
    borderColor: 'rgba(251, 113, 133, 0.15)',
    titleFontSizeMedium: '18px',
    titleFontWeight: '600'
  },
  Button: {
    borderRadiusMedium: '8px',
    fontSizeMedium: '14px'
  },
  Menu: {
    fontSize: '15px',
    itemHeight: '42px'
  }
}

export function useTheme() {
  const currentThemeType = ref<ThemeType>((localStorage.getItem('lens_theme_type') as ThemeType) || 'purple')

  watch(currentThemeType, (val) => localStorage.setItem('lens_theme_type', val))

  const syncThemeVariables = (theme: GlobalThemeOverrides) => {
    const root = document.documentElement
    const common = theme.common!
    root.style.setProperty('--primary-color', common.primaryColor!)
    root.style.setProperty('--primary-hover', common.primaryColorHover!)
    root.style.setProperty('--app-bg-color', common.bodyColor!)
    root.style.setProperty('--card-bg-color', common.cardColor!)
    root.style.setProperty('--modal-bg-color', common.modalColor || common.cardColor!)
    root.style.setProperty('--text-color', common.textColorBase!)
    root.style.setProperty('--border-color', common.dividerColor!)
    
    // 动态侧边栏背景
    let sidebarBg = '#121215'
    if (currentThemeType.value === 'purple') sidebarBg = '#140c1a'
    if (currentThemeType.value === 'oceanic') sidebarBg = '#0b1120'
    if (currentThemeType.value === 'crimson') sidebarBg = '#120d0d'
    root.style.setProperty('--sidebar-bg-color', sidebarBg)
    
    root.style.setProperty('--primary-border-color', `${common.primaryColor}33`) // 20% opacity
  }

  const themeOverrides = computed(() => {
    const map = {
      purple: purpleOverrides,
      modern: modernOverrides,
      oceanic: oceanicOverrides,
      crimson: crimsonOverrides
    }
    const overrides = map[currentThemeType.value] || purpleOverrides
    if (typeof document !== 'undefined') { syncThemeVariables(overrides) }
    return overrides
  })

  onMounted(() => {
    const map = {
      purple: purpleOverrides,
      modern: modernOverrides,
      oceanic: oceanicOverrides,
      crimson: crimsonOverrides
    }
    syncThemeVariables(map[currentThemeType.value] || purpleOverrides)
  })

  return {
    currentThemeType,
    themeOverrides,
    themeOptions: [
      { label: '暗夜紫韵 (Purple)', key: 'purple' },
      { label: '现代极客 (Modern)', key: 'modern' },
      { label: '深海翠羽 (Oceanic)', key: 'oceanic' },
      { label: '赤红余烬 (Crimson)', key: 'crimson' }
    ]
  }
}
