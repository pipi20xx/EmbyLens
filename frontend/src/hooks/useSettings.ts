import { ref, reactive } from 'vue'
import { useMessage } from 'naive-ui'
import { serverApi } from '@/api/server'
import { configApi } from '@/api/config'
import { fetchServers, activateServer } from '@/store/serverStore'

export function useSettings() {
  const message = useMessage()
  const savingGlobal = ref(false)
  const showServerModal = ref(false)
  const editingServer = ref(null)
  const fileInputRef = ref<HTMLInputElement | null>(null)

  const globalConfig = reactive({
    tmdb_api_key: '',
    bangumi_api_token: '',
    proxy: {
      enabled: false,
      url: '',
      exclude_emby: true
    }
  })

  const handleExportConfig = () => {
    window.open('/api/system/config/export', '_blank')
  }

  const triggerImportConfig = () => {
    fileInputRef.value?.click()
  }

  const handleImportConfig = async (event: Event) => {
    const input = event.target as HTMLInputElement
    if (!input.files || input.files.length === 0) return
    
    const file = input.files[0]
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      await configApi.importConfig(formData)
      message.success('配置导入成功，页面将刷新以应用更改')
      setTimeout(() => location.reload(), 1500)
    } catch (e: any) {
      message.error('导入失败: ' + (e.response?.data?.detail || '未知错误'))
    } finally {
      input.value = '' 
    }
  }

  const fetchCurrent = async () => {
    await fetchServers()
    try {
      const res = await serverApi.getCurrent()
      const data = res.data
      if (data) {
        globalConfig.tmdb_api_key = data.tmdb_api_key || ''
        globalConfig.bangumi_api_token = data.bangumi_api_token || ''
        if (data.proxy) {
          globalConfig.proxy.enabled = !!data.proxy.enabled
          globalConfig.proxy.url = data.proxy.url || ''
          globalConfig.proxy.exclude_emby = data.proxy.exclude_emby !== false
        }
      }
    } catch (e) {
      console.error('Failed to load global config:', e)
    }
  }

  const handleActivate = async (serverId: string) => {
    const success = await activateServer(serverId)
    if (success) {
      message.success('已切换当前激活服务器')
      await fetchCurrent()
    } else {
      message.error('切换失败')
    }
  }

  const handleDelete = async (serverId: string) => {
    try {
      await serverApi.deleteServer(serverId)
      message.success('服务器已删除')
      await fetchCurrent()
    } catch (e) {
      message.error('删除失败')
    }
  }

  const handleSaveGlobal = async () => {
    savingGlobal.value = true
    try {
      await serverApi.saveGlobal(globalConfig)
      message.success('全局配置已保存')
      await fetchCurrent()
    } catch (e: any) {
      message.error('保存失败')
    } finally {
      savingGlobal.value = false
    }
  }

  return {
    globalConfig, savingGlobal, showServerModal, editingServer, fileInputRef,
    handleExportConfig, triggerImportConfig, handleImportConfig, fetchCurrent, 
    handleActivate, handleDelete, handleSaveGlobal
  }
}
