import { onMounted } from 'vue'
import { useBookmark } from '../sitenav/useBookmark'
import { useBookmarkState } from './hooks/useBookmarkState'
import { useBookmarkActions } from './hooks/useBookmarkActions'
import { useBookmarkDnd } from './hooks/useBookmarkDnd'
import { useBookmarkHealth } from './hooks/useBookmarkHealth'

export function useBookmarkManager() {
  const bookmarkApi = useBookmark()
  const state = useBookmarkState(bookmarkApi.bookmarks)
  const actions = useBookmarkActions(state, bookmarkApi)
  const dnd = useBookmarkDnd(state, actions, bookmarkApi)
  const health = useBookmarkHealth(bookmarkApi, actions)

  const autoFetchTitle = async () => {
    if (state.form.url && !state.form.title) {
      try {
        state.form.title = new URL(state.form.url).hostname
      } catch (e) {}
    }
  }

  const autoFetchIcon = async () => {
    if (!state.form.url) return
    state.fetchingIcon.value = true
    const icon = await bookmarkApi.fetchIcon(state.form.url)
    if (icon) state.form.icon = icon
    state.fetchingIcon.value = false
  }

  onMounted(() => bookmarkApi.fetchBookmarks(true))

    return {

      ...state,

      ...actions,

      ...dnd,

      ...health,

      autoFetchTitle,

      autoFetchIcon,

      fetchIcon: bookmarkApi.fetchIcon

    }

  }

  