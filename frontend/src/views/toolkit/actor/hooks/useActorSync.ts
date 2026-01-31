import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { actorsApi } from '@/api/actors'

export function useActorSync(onSuccess?: () => void) {
  const message = useMessage()
  const nameLoading = ref(false)
  const syncLoading = ref(false)

  const handleUpdateName = async (selectedEmby: any, editName: string) => {
    if (!selectedEmby || !editName) return
    nameLoading.value = true
    try {
      await actorsApi.updateName(selectedEmby.Id, editName)
      message.success('姓名已更新')
      selectedEmby.Name = editName
      return true
    } catch (e) { 
      message.error('更新失败') 
      return false
    } finally { 
      nameLoading.value = false 
    }
  }

  const handleSync = async (selectedEmby: any, selectedTmdb: any, editName: string) => {
    if (!selectedEmby || !selectedTmdb) return
    syncLoading.value = true
    try {
      await actorsApi.syncActor(selectedEmby.Id, {
        Name: editName,
        ProviderIds: { 
          ...selectedEmby.ProviderIds, 
          Tmdb: selectedTmdb.id.toString() 
        }
      })
      message.success('同步成功')
      if (onSuccess) onSuccess()
      return true
    } catch (e) { 
      message.error('同步失败') 
      return false
    } finally { 
      syncLoading.value = false 
    }
  }

  return {
    nameLoading, syncLoading, handleUpdateName, handleSync
  }
}
