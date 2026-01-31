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
      const response = await fetch(`/api/bookmarks?as_tree=${asTree}`)
      bookmarks.value = await response.json()
    } catch (err) {
      console.error('Failed to fetch bookmarks:', err)
    } finally {
      loading.value = false
    }
  }

  const createBookmark = async (data: Partial<Bookmark>) => {
    try {
      const response = await fetch('/api/bookmarks', {
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

  const clearAllBookmarks = async () => {
    try {
      await fetch('/api/bookmarks', { method: 'DELETE' })
      await fetchBookmarks()
    } catch (err) {
      console.error('Failed to clear bookmarks:', err)
    }
  }

  const exportBookmarks = () => {
    window.open('/api/bookmarks/export', '_blank')
  }

  const reorderBookmarks = async (ordered_ids: string[], parent_id?: string) => {
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

  const importBookmarksHtml = async (file: File) => {
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

  return {
    bookmarks,
    loading,
    fetchBookmarks,
    createBookmark,
        updateBookmark,
        deleteBookmark,
        clearAllBookmarks,
        exportBookmarks,
        reorderBookmarks,
        importBookmarksHtml,
        fetchIcon
      }
    }
    