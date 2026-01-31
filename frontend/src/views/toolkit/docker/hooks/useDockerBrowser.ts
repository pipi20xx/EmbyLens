import { ref, Ref } from 'vue'
import { useMessage } from 'naive-ui'

export function useDockerBrowser(
  selectedHostId: Ref<string | null>,
  onSelect: (path: string) => void
) {
  const message = useMessage()
  const showBrowserModal = ref(false)
  const browserInitialPath = ref('/')
  const isPickingForNewProject = ref(false)
  const pickedPathForNewProject = ref('')

  const browseRemotePath = async (path: string = '/') => {
    if (!selectedHostId.value) {
      message.warning('请先选择一个 Docker 主机'); return
    }
    isPickingForNewProject.value = false
    browserInitialPath.value = path
    showBrowserModal.value = true
  }

  const handleRequestPickPath = (currentPath: string) => {
    isPickingForNewProject.value = true
    browserInitialPath.value = currentPath || '/'
    showBrowserModal.value = true
  }

  const handleFileSelect = (path: string) => {
    if (isPickingForNewProject.value) {
      pickedPathForNewProject.value = path
      // 触发更新后清空，防止下次干扰
      setTimeout(() => { pickedPathForNewProject.value = '' }, 500)
      showBrowserModal.value = false
    } else {
      onSelect(path)
    }
  }

  return {
    showBrowserModal,
    browserInitialPath,
    pickedPathForNewProject,
    browseRemotePath,
    handleRequestPickPath,
    handleFileSelect
  }
}
