import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { dockerApi } from '@/api/docker'
import { AutoUpdateSettings } from '@/types/docker'

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
    const data = await dockerApi.getAutoUpdateSettings()
    autoUpdateSettings.value = data
    
    if (autoUpdateSettings.value.type === 'interval') {
      const totalMin = parseInt(autoUpdateSettings.value.value) || 0
      intervalParts.value.d = Math.floor(totalMin / 1440)
      intervalParts.value.h = Math.floor((totalMin % 1440) / 60)
      intervalParts.value.m = totalMin % 60
    }
    
    showAutoUpdateModal.value = true
  }

  const saveAutoUpdateSettings = async () => {
    if (autoUpdateSettings.value.type === 'interval') {
      const totalMin = (intervalParts.value.d * 1440) + (intervalParts.value.h * 60) + intervalParts.value.m
      if (totalMin <= 0) {
        message.warning('执行间隔不能为 0')
        return
      }
      autoUpdateSettings.value.value = String(totalMin)
    }

    savingAutoUpdate.value = true
    try {
      await dockerApi.saveAutoUpdateSettings(autoUpdateSettings.value)
      message.success('设置已保存，调度器已重载')
      showAutoUpdateModal.value = false
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