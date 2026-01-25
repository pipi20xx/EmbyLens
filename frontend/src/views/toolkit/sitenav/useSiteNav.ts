import { ref } from 'vue'
import { useMessage, createDiscreteApi, darkTheme } from 'naive-ui'

export interface Category {
  id: number
  name: string
  icon?: string
  order: number
}

export interface SiteNav {
  id: number
  title: string
  url: string
  icon?: string
  description?: string
  category_id?: number
  category: string
  order: number
}

// --- 全局状态积木 ---
const sites = ref<SiteNav[]>([])
const categories = ref<Category[]>([])

const DEFAULT_SETTINGS = {
  background_url: '',
  background_opacity: 0.7,
  background_blur: 0,
  background_size: 'cover',
  background_color: '#1e1e22',
  card_background: 'rgba(255, 255, 255, 0.12)',
  card_blur: 16,
  card_border_color: 'rgba(255, 255, 255, 0.15)',
  card_style: 'glass',
  text_color: '#ffffff',
  text_description_color: 'rgba(255, 255, 255, 0.7)',
  category_title_color: '#ffffff',
  show_category_line: true,
  content_max_width: 90,
  page_title: '站点导航',
  page_subtitle: '个性化您的导航面板',
  wallpaper_mode: 'custom', // 'custom', 'bing', 'unsplash'
  wallpaper_type: 'anime', // 'scenery', 'anime', 'minimalist', 'random'
  wallpaper_keyword: '',
  wallpaper_resolution: '1920x1080',
  show_hitokoto: false,
  show_clock: false,
  bing_mkt: 'zh-CN',
  bing_index: 0,
  bing_resolution: '1920x1080',
  show_wallpaper_info: false,
  header_alignment: 'left',
  category_alignment: 'left',
  header_item_spacing: 12,
  header_margin_top: 20,
  header_margin_bottom: 30
}

const navSettings = ref({ ...DEFAULT_SETTINGS })
const loading = ref(false)
const hitokoto = ref({ text: '', from: '' })
const bingInfo = ref({ url: '', title: '', copyright: '' })
const wallpaperSeed = ref(Date.now())
const wallpaperLoading = ref(false)
const resolvedWallpaperUrl = ref('')

export function useSiteNav() {
  const { message } = createDiscreteApi(['message'], {
    configProviderProps: { theme: darkTheme }
  })

  const refreshWallpaper = async (apiUrl?: string, forceRefresh = false) => {
    if (!apiUrl) {
      resolvedWallpaperUrl.value = ''
      return
    }

    // 处理随机种子，如果没有提供种子则使用当前时间戳
    const seed = Date.now()
    const finalUrl = apiUrl.includes('?') 
      ? `${apiUrl}&_seed=${seed}` 
      : `${apiUrl}?_seed=${seed}`

    // 缓存逻辑：如果不是强制刷新，尝试从 localStorage 读取
    const cacheKey = `lens_wallpaper_cache_${apiUrl}`
    if (!forceRefresh) {
      const cached = localStorage.getItem(cacheKey)
      if (cached) {
        try {
          const { url, expiry } = JSON.parse(cached)
          if (expiry > Date.now()) {
            resolvedWallpaperUrl.value = url
            return
          }
        } catch (e) {
          localStorage.removeItem(cacheKey)
        }
      }
    }

    wallpaperLoading.value = true
    wallpaperSeed.value = seed
    
    try {
      // 预先请求一次获取最终重定向地址
      const res = await fetch(finalUrl, { method: 'GET' })
      if (res.url) {
        resolvedWallpaperUrl.value = res.url
        // 写入缓存，默认缓存 1 小时
        localStorage.setItem(cacheKey, JSON.stringify({
          url: res.url,
          expiry: Date.now() + 3600 * 1000
        }))
      }
    } catch (e) {
      resolvedWallpaperUrl.value = '' // 出错则回退
    }

    wallpaperLoading.value = false
  }

  const saveCurrentWallpaper = async (url: string) => {
    if (!url) return
    try {
      wallpaperLoading.value = true
      
      const res = await fetch('/api/navigation/save-remote-bg', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }) // 这里的 url 已经是解析后的静态地址了
      })
      const data = await res.json()
      if (res.ok) {
        navSettings.value.background_url = data.url
        navSettings.value.wallpaper_mode = 'custom'
        resolvedWallpaperUrl.value = '' // 保存后清空临时解析地址
        message.success('已成功保存当前壁纸')
      } else {
        message.error(data.detail || '保存失败')
      }
    } catch (e) {
      message.error('保存请求失败')
    } finally {
      wallpaperLoading.value = false
    }
  }

  const fetchHitokoto = async () => {
    try {
      const res = await fetch('https://v1.hitokoto.cn')
      const data = await res.json()
      hitokoto.value = { text: data.hitokoto, from: data.from }
    } catch (e) {
      hitokoto.value = { text: '心之所向，素履以往。', from: '七堇年' }
    }
  }

  const fetchBingWallpaper = async () => {
    try {
      const { bing_index, bing_mkt, bing_resolution } = navSettings.value
      const res = await fetch(`/api/navigation/bing-wallpaper?index=${bing_index}&mkt=${bing_mkt}&resolution=${bing_resolution}`)
      const data = await res.json()
      if (data.url) bingInfo.value = data
    } catch (e) {}
  }

  const fetchSettings = async () => {
    try {
      const response = await fetch('/api/navigation/settings')
      const data = await response.json()
      navSettings.value = { ...DEFAULT_SETTINGS, ...data }
      if (navSettings.value.wallpaper_mode === 'bing') fetchBingWallpaper()
    } catch (e) {}
  }

  const resetNavSettings = async () => {
    try {
      // 排除掉背景图 URL，只重置样式相关的
      const { background_url, ...styleSettings } = DEFAULT_SETTINGS
      await updateNavSettings(styleSettings)
      message.success('已恢复默认样式')
    } catch (e) {
      message.error('重置失败')
    }
  }

  const updateNavSettings = async (settings: any) => {
    try {
      await fetch('/api/navigation/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      })
      navSettings.value = { ...navSettings.value, ...settings }
      
      // 切换模式、类型、分辨率或更新关键词时，刷新随机种子
      const refreshKeys = ['wallpaper_mode', 'wallpaper_type', 'wallpaper_keyword', 'wallpaper_resolution']
      if (Object.keys(settings).some(k => refreshKeys.includes(k))) {
        // 注意：这里需要从外部传入最新的 baseRandomApiUrl.value，或者在此处重新计算
        // 为了解耦，我们在 SiteNav.vue 的 watch 中处理大部分逻辑
      }

      // 如果必应相关参数改变，重新抓取
      const bingKeys = ['wallpaper_mode', 'bing_mkt', 'bing_index', 'bing_resolution']
      if (Object.keys(settings).some(k => bingKeys.includes(k))) {
        if (navSettings.value.wallpaper_mode === 'bing') fetchBingWallpaper()
      }
    } catch (e) {
      message.error('保存设置失败')
    }
  }

  const uploadBackground = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch('/api/navigation/upload-bg', {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (res.ok) {
        navSettings.value.background_url = data.url
        message.success('背景上传成功')
      } else {
        message.error(data.detail || '背景上传失败')
      }
    } catch (e) {
      message.error('背景上传失败')
    }
  }

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/navigation/categories')
      const data = await response.json()
      // 按照 order 排序
      categories.value = data.sort((a: any, b: any) => a.order - b.order)
    } catch (e) {
      console.error('Fetch categories failed', e)
    }
  }

  const fetchSites = async () => {
    loading.value = true
    try {
      const response = await fetch('/api/navigation/')
      const data = await response.json()
      // 按照 order 排序
      sites.value = data.sort((a: any, b: any) => a.order - b.order)
    } catch (e) {
      message.error('获取站点列表失败')
    } finally {
      loading.value = false
    }
  }

  const addCategory = async (name: string, icon: string = '') => {
    try {
      await fetch('/api/navigation/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, icon, order: categories.value.length })
      })
      await fetchCategories()
    } catch (e) {
      message.error('添加分类失败')
    }
  }

  const updateCategory = async (id: number, name: string, icon: string = '') => {
    // 1. 立即更新本地状态 (乐观更新)
    const cat = categories.value.find(c => c.id === id)
    if (cat) {
      cat.name = name
      cat.icon = icon
    }
    
    try {
      const response = await fetch(`/api/navigation/categories/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, icon })
      })
      if (!response.ok) throw new Error('Update failed')
      
      // 2. 后台刷新确认
      await fetchCategories()
      await fetchSites() 
    } catch (e) {
      message.error('更新分类失败')
      await fetchCategories() // 出错时回滚
    }
  }

  const deleteCategory = async (id: number) => {
    try {
      await fetch(`/api/navigation/categories/${id}`, { method: 'DELETE' })
      await fetchCategories()
      await fetchSites()
    } catch (e) {
      message.error('删除分类失败')
    }
  }

  const updateCategoryOrder = async (ids: number[]) => {
    try {
      await fetch('/api/navigation/categories/reorder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ids)
      })
      // 本地立即排序以防闪烁
      const newCats = [...categories.value]
      newCats.sort((a, b) => ids.indexOf(a.id) - ids.indexOf(b.id))
      categories.value = newCats
    } catch (e) {
      message.error('保存分类排序失败')
    }
  }

  const fetchIconFromUrl = async (url: string) => {
    if (!url) return null
    try {
      const response = await fetch(`/api/navigation/fetch-icon?url=${encodeURIComponent(url)}`)
      const data = await response.json()
      return data.icon
    } catch (e) {
      return null
    }
  }

  const addSite = async (site: Partial<SiteNav>) => {
    try {
      const response = await fetch('/api/navigation/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(site)
      })
      if (!response.ok) throw new Error('Failed')
      await fetchSites()
      message.success('添加成功')
      return true
    } catch (e) {
      message.error('添加失败')
      return false
    }
  }

  const updateSite = async (id: number, site: Partial<SiteNav>) => {
    try {
      const response = await fetch(`/api/navigation/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(site)
      })
      if (!response.ok) throw new Error('Failed')
      await fetchSites()
      message.success('更新成功')
      return true
    } catch (e) {
      message.error('更新失败')
      return false
    }
  }

  const deleteSite = async (id: number) => {
    try {
      await fetch(`/api/navigation/${id}`, { method: 'DELETE' })
      await fetchSites()
      message.success('删除成功')
    } catch (e) {
      message.error('删除失败')
    }
  }

  const updateSiteOrder = async (ids: number[]) => {
    try {
      await fetch('/api/navigation/reorder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ids)
      })
    } catch (e) {
      message.error('保存排序失败')
    }
  }

  const exportConfig = () => {
    window.open('/api/navigation/export', '_blank')
  }

  const importConfig = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch('/api/navigation/import', {
        method: 'POST',
        body: formData
      })
      if (!res.ok) throw new Error('Import failed')
      message.success('配置导入成功')
      await fetchCategories()
      await fetchSites()
      return true
    } catch (e) {
      message.error('导入失败，请检查文件格式')
      return false
    }
  }

  return {
    sites,
    categories,
    navSettings,
    loading,
    hitokoto,
    bingInfo,
    fetchHitokoto,
    fetchBingWallpaper,
    fetchSites,
    fetchCategories,
    fetchSettings,
    addCategory,
    updateCategory,
    deleteCategory,
    updateCategoryOrder,
    updateNavSettings,
    resetNavSettings,
    uploadBackground,
    addSite,
    updateSite,
    deleteSite,
    fetchIconFromUrl,
    updateSiteOrder,
    exportConfig,
    importConfig,
    message,
    wallpaperSeed,
    wallpaperLoading,
    resolvedWallpaperUrl,
    refreshWallpaper,
    saveCurrentWallpaper
  }
}
