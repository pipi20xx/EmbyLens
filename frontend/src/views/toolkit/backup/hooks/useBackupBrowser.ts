import { ref, Ref } from 'vue'

export function useBackupBrowser(editTask: Ref<any>) {
  const showBrowser = ref(false)
  const browserInitialPath = ref('/')
  const browserTargetField = ref('')

  const openBrowser = (field: string) => {
    browserTargetField.value = field
    browserInitialPath.value = (editTask.value as any)[field === 'src' ? 'src_path' : 'dst_path'] || '/'
    showBrowser.value = true
  }

  const handlePathSelect = (path: string) => {
    if (browserTargetField.value === 'src') {
      editTask.value.src_path = path
    } else {
      editTask.value.dst_path = path
    }
  }

  return {
    showBrowser, browserInitialPath, openBrowser, handlePathSelect
  }
}
