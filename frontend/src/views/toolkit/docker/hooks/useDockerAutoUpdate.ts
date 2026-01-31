import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { dockerApi, AutoUpdateSettings } from '@/api/docker'

export function useDockerAutoUpdate() {
  const message = useMessage()
  const showAutoUpdateModal = ref(false)
  const savingAutoUpdate = ref(false)
  const autoUpdateSettings = ref<AutoUpdateSettings>({
    enabled: true,
    type: 'cron',
    value: '03:00'
  })

  const intervalParts = ref({ d: 0, h: 0, m: 0 })

  const openAutoUpdateModal = async () => {
    try {
      const res = await dockerApi.getAutoUpdateSettings()
      autoUpdateSettings.value = res.data
      
      if (autoUpdateSettings.value.type === 'interval') {
        const totalMin = parseInt(autoUpdateSettings.value.value) || 0
        intervalParts.value.d = Math.floor(totalMin / 1440)
        intervalParts.value.h = Math.floor((totalMin % 1440) / 60)
        intervalParts.value.m = totalMin % 60
      }
      
      showAutoUpdateModal.value = true
    } catch (e) {
      message.error('获取设置失败')
    }
  }

  const saveAutoUpdateSettings = async () => {
    savingAutoUpdate.value = true
    try {
      if (autoUpdateSettings.value.type === 'interval') {
        const totalMin = (intervalParts.value.d * 1440) + (intervalParts.value.h * 60) + intervalParts.value.m
        if (totalMin <= 0) {
          message.warning('执行间隔不能为 0')
          savingAutoUpdate.value = false
          return
        }
        autoUpdateSettings.value.value = String(totalMin)
      }

      await dockerApi.saveAutoUpdateSettings(autoUpdateSettings.value)
      message.success('设置已保存，调度器已重载')
      showAutoUpdateModal.value = false
    } catch (e) {
      message.error('保存失败')
    } finally {
      savingAutoUpdate.value = false
    }
  }

  return {
    showAutoUpdateModal,
    savingAutoUpdate,
    autoUpdateSettings,
    intervalParts,
    openAutoUpdateModal,
    saveAutoUpdateSettings
  }
}
