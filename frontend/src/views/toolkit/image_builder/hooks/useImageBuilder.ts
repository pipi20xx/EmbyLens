import { ref, reactive } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { imageBuilderApi } from '@/api/imageBuilder'
import { dockerApi } from '@/api/docker'

export function useImageBuilder() {
  const message = useMessage()
  const dialog = useDialog()

  const projects = ref([])
  const registries = ref<any[]>([])
  const hostOptions = ref([])
  const proxyOptions = ref([])
  const registryOptions = ref([])
  const loading = ref(false)
  
  const projectTags = reactive<Record<string, string>>({})

  const fetchProjects = async () => {
    loading.value = true
    try {
      const data: any = await imageBuilderApi.getProjects()
      projects.value = data
      data.forEach((p: any) => { if (!projectTags[p.id]) projectTags[p.id] = 'latest' })
    } finally { loading.value = false }
  }

  const fetchOptions = async () => {
    try {
      const [regData, proxData, hostData]: any = await Promise.all([
        imageBuilderApi.getRegistries(), imageBuilderApi.getProxies(), dockerApi.getHosts()
      ])
      registries.value = regData
      registryOptions.value = regData.map((r: any) => ({ label: r.name, value: r.id }))
      proxyOptions.value = proxData.map((p: any) => ({ label: p.name, value: p.id }))
      hostOptions.value = hostData.map((h: any) => ({ label: h.name, value: h.id }))
    } catch (e) {}
  }

  const directBuild = async (row: any) => {
    const tag = projectTags[row.id] || 'latest'
    try {
      await imageBuilderApi.buildProject(row.id, { tag: tag })
      message.success(`任务 [${tag}] 已在后台启动，完成后将通过通知告知`)
    } catch (e) { }
  }

  const handleClearAllLogs = () => {
    dialog.error({
      title: '确认清空',
      content: '该操作将彻底删除所有项目的构建历史及物理日志文件，且不可恢复。是否继续？',
      positiveText: '确定清空',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await imageBuilderApi.clearAllTasks()
          message.success('历史记录已全部清空')
        } catch (e) { }
      }
    })
  }

  const deleteProject = (row: any, onSuccess: () => void) => {
    dialog.warning({
      title: '确认删除', content: `确定要删除项目 "${row.name}" 吗？`, positiveText: '确定', negativeText: '取消',
      onPositiveClick: async () => {
        try { 
          await imageBuilderApi.deleteProject(row.id)
          onSuccess()
        }
        catch (e) { }
      }
    })
  }

  return {
    projects, registries, hostOptions, proxyOptions, registryOptions, loading, projectTags,
    fetchProjects, fetchOptions, directBuild, handleClearAllLogs, deleteProject
  }
}