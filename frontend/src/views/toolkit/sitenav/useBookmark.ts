import { ref } from 'vue'

export interface Bookmark {
  id: string
  title: string
  type: 'file' | 'folder'
  url?: string
  icon?: string
  parent_id?: string
  order: number
  children?: Bookmark[]
}

export function useBookmark() {
  const bookmarks = ref<Bookmark[]>([])
  const loading = ref(false)

  const fetchBookmarks = async (asTree = true) => {
    loading.value = true
    try {
      const response = await fetch(`/api/bookmarks/?as_tree=${asTree}`)
      if (!response.ok) throw new Error('Fetch failed')
      bookmarks.value = await response.json()
    } catch (err) {
      console.error('Failed to fetch bookmarks:', err)
      bookmarks.value = []
    } finally {
      loading.value = false
    }
  }

  const addBookmark = async (data: Partial<Bookmark>) => {
    try {
      const response = await fetch('/api/bookmarks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      await fetchBookmarks()
      return await response.json()
    } catch (err) {
      console.error('Failed to create bookmark:', err)
    }
  }

  const updateBookmark = async (id: string, data: Partial<Bookmark>) => {
    try {
      await fetch(`/api/bookmarks/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      await fetchBookmarks()
    } catch (err) {
      console.error('Failed to update bookmark:', err)
    }
  }

  const deleteBookmark = async (id: string) => {
    try {
      await fetch(`/api/bookmarks/${id}`, { method: 'DELETE' })
      await fetchBookmarks()
    } catch (err) {
      console.error('Failed to delete bookmark:', err)
    }
  }

  const clearBookmarks = async () => {
    try {
      await fetch('/api/bookmarks/', { method: 'DELETE' })
      await fetchBookmarks()
    } catch (err) {
      console.error('Failed to clear bookmarks:', err)
    }
  }

  const exportBookmarks = () => {
    const link = document.createElement('a')
    link.href = '/api/bookmarks/export'
    link.setAttribute('download', '')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const reorderBookmarks = async (ordered_ids: string[], parent_id: string | null = "KEEP_EXISTING") => {
    try {
      await fetch('/api/bookmarks/reorder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ordered_ids, parent_id })
      })
      await fetchBookmarks()
    } catch (err) {
      console.error('Failed to reorder bookmarks:', err)
    }
  }

  const importHtml = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    try {
      const response = await fetch('/api/bookmarks/import-html', {
        method: 'POST',
        body: formData
      })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || '导入失败')
      await fetchBookmarks()
      return result
    } catch (err) {
      console.error('Failed to import bookmarks:', err)
      throw err
    }
  }

  const fetchIcon = async (url: string) => {
    try {
      const response = await fetch(`/api/navigation/fetch-icon?url=${encodeURIComponent(url)}`)
      const data = await response.json()
      return data.icon
    } catch (err) {
      return null
    }
  }

  const findDuplicates = async () => {
    try {
      const response = await fetch('/api/bookmarks/duplicates')
      return await response.json()
    } catch (err) {
      console.error('Failed to check duplicates:', err)
      return []
    }
  }

  const checkHealth = async (urls: string[]) => {
    const response = await fetch('/api/bookmarks/check-health', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ urls })
    })
    return await response.json()
  }

  const aiAnalyze = async () => {
    const response = await fetch('/api/bookmarks/ai-analyze', { method: 'POST' })
    return await response.json()
  }

  const aiApply = async (suggestions: any) => {
    const response = await fetch('/api/bookmarks/ai-apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(suggestions)
    })
    return await response.json()
  }

  return {
    bookmarks,
    loading,
    fetchBookmarks,
    addBookmark,
    updateBookmark,
    deleteBookmark,
    clearBookmarks,
    exportBookmarks,
    reorderBookmarks,
    importHtml,
    findDuplicates,
    checkHealth,
    aiAnalyze,
    aiApply,
    fetchIcon
  }
}