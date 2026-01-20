import { ref, computed, watch, onMounted } from 'vue'
import { GlobalThemeOverrides } from 'naive-ui'

export type ThemeType = 'modern' | 'purple'

const purpleOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#bb86fc',
    primaryColorHover: '#d1a8ff',
    primaryColorPressed: '#995df0',
    borderRadius: '10px',
    cardColor: '#120818',
    modalColor: '#180a20',
    bodyColor: '#0b040f',
    textColorBase: '#e0e0e0'
  },
  Card: { borderRadius: '14px' },
  Button: { borderRadiusMedium: '10px' }
}

const modernOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#705df2',
    primaryColorHover: '#8a7af5',
    primaryColorPressed: '#5946d1',
    borderRadius: '6px',
    cardColor: '#1e1e24',
    bodyColor: '#101014',
    modalColor: '#25252b',
    textColorBase: '#ffffff'
  },
  Card: { borderRadius: '10px' },
  Button: { borderRadiusMedium: '6px' }
}

export function useTheme() {
  const currentThemeType = ref<ThemeType>((localStorage.getItem('embylens_theme_type') as ThemeType) || 'purple')

  watch(currentThemeType, (val) => localStorage.setItem('embylens_theme_type', val))

  const syncThemeVariables = (theme: GlobalThemeOverrides) => {
    const root = document.documentElement
    const common = theme.common!
    root.style.setProperty('--primary-color', common.primaryColor!)
    root.style.setProperty('--primary-hover', common.primaryColorHover!)
    root.style.setProperty('--app-bg-color', common.bodyColor!)
    root.style.setProperty('--card-bg-color', common.cardColor!)
    root.style.setProperty('--modal-bg-color', common.modalColor || common.cardColor!)
    root.style.setProperty('--text-color', common.textColorBase!)
    root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.09)')
    root.style.setProperty('--primary-border-color', `${common.primaryColor}4D`) // 30% opacity
  }

  const themeOverrides = computed(() => {
    const overrides = currentThemeType.value === 'purple' ? purpleOverrides : modernOverrides
    if (typeof document !== 'undefined') { syncThemeVariables(overrides) }
    return overrides
  })

  onMounted(() => {
    const initialTheme = currentThemeType.value === 'purple' ? purpleOverrides : modernOverrides
    syncThemeVariables(initialTheme)
  })

  return {
    currentThemeType,
    themeOverrides,
    themeOptions: [
      { label: '暗夜紫韵 (Purple)', key: 'purple' },
      { label: '现代极客 (Modern)', key: 'modern' }
    ]
  }
}
