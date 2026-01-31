import { ref, reactive, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { serverApi } from '@/api/server'
import { toolkitApi } from '@/api/toolkit'

export function useCleanupTools() {
  const message = useMessage()
  const loading = ref(false)
  const libOptions = ref([])

  const savedCommon = localStorage.getItem('lens_cleanup_common')
  const common = reactive(savedCommon ? JSON.parse(savedCommon) : {
    lib_names: [],
    dry_run: true
  })

  watch(common, (val) => {
    localStorage.setItem('lens_cleanup_common', JSON.stringify(val))
  }, { deep: true })

  const fetchLibraries = async () => {
    try {
      const res = await serverApi.getLibraries()
      libOptions.value = res.data
    } catch (e) {}
  }

  const peopleItemTypes = ref(['Movie', 'Series'])
  const lastAction = ref('people_remover')

  const debugPayload = computed(() => {
    const body: any = {
      lib_names: common.lib_names,
      dry_run: common.dry_run
    }
    if (lastAction.value === 'people_remover') {
      body.item_types = peopleItemTypes.value
    }
    return JSON.stringify({
      endpoint: `/api/toolkit/${lastAction.value}`,
      body
    }, null, 2)
  })

  const handleAction = async (endpoint: string) => {
    lastAction.value = endpoint
    if (common.lib_names.length === 0) {
      message.warning('请至少指定一个媒体库')
      return
    }
    loading.value = true
    try {
      const payload: any = {
        lib_names: common.lib_names,
        dry_run: common.dry_run
      }
      if (endpoint === 'people_remover') payload.item_types = peopleItemTypes.value

      const res = await toolkitApi.executeAction(endpoint, payload)
      message.success(`任务完成：处理项目数 ${res.data.processed_count} [${common.dry_run ? '预览' : '实调'}]`)
    } catch (e) {
      message.error('请求失败')
    } finally {
      loading.value = false
    }
  }

  return {
    loading, libOptions, common, peopleItemTypes, lastAction, debugPayload,
    fetchLibraries, handleAction
  }
}
