import { ref } from 'vue'
import { useMessage, createDiscreteApi, darkTheme } from 'naive-ui'

export interface Category {
  id: number
  name: string
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

// --- 全局状态积木 (单例模式) ---
const sites = ref<SiteNav[]>([])
const categories = ref<Category[]>([])
const loading = ref(false)

export function useSiteNav() {
  // 使用离散 API 保证在任何地方都能弹出消息
  const { message } = createDiscreteApi(['message'], {
    configProviderProps: { theme: darkTheme }
  })

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

  const addCategory = async (name: string) => {
    try {
      await fetch('/api/navigation/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, order: categories.value.length })
      })
      await fetchCategories()
    } catch (e) {
      message.error('添加分类失败')
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

  return {
    sites,
    categories,
    loading,
    fetchSites,
    fetchCategories,
    addCategory,
    deleteCategory,
    updateCategoryOrder,
    addSite,
    updateSite,
    deleteSite,
    fetchIconFromUrl,
    updateSiteOrder,
    message
  }
}
