import { computed, Ref } from 'vue'
import { useMessage } from 'naive-ui'
import { dockerApi, DockerHost } from '@/api/docker'

export function useDockerScanPaths(
  selectedHostId: Ref<string | null>, 
  currentHost: Ref<DockerHost | undefined>,
  onRefresh: () => void
) {
  const message = useMessage()

  const currentHostPaths = computed(() => 
    (currentHost.value?.compose_scan_paths || '').split(',').map(p => p.trim()).filter(p => p)
  )

  const addScanPath = async (path: string) => {
    if (!currentHost.value || !selectedHostId.value) return
    const pathList = [...currentHostPaths.value]
    if (!pathList.includes(path)) {
      pathList.push(path)
      const updatedHost = { ...currentHost.value, compose_scan_paths: pathList.join(',') }
      await dockerApi.updateHost(selectedHostId.value, updatedHost)
      message.success('已添加扫描路径')
      onRefresh()
    }
  }

  const removeScanPath = async (path: string) => {
    if (!currentHost.value || !selectedHostId.value) return
    const pathList = currentHostPaths.value.filter(p => p !== path)
    const updatedHost = { ...currentHost.value, compose_scan_paths: pathList.join(',') }
    await dockerApi.updateHost(selectedHostId.value, updatedHost)
    message.info('已移除路径')
    onRefresh()
  }

  return {
    currentHostPaths,
    addScanPath,
    removeScanPath
  }
}
