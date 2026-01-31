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
      const res = await imageBuilderApi.getProjects()
      projects.value = res.data
      res.data.forEach((p: any) => { if (!projectTags[p.id]) projectTags[p.id] = 'latest' })
    } catch (e) { message.error('获取项目列表失败') } finally { loading.value = false }
  }

  const fetchOptions = async () => {
    try {
      const [regRes, proxRes, hostRes] = await Promise.all([
        imageBuilderApi.getRegistries(), imageBuilderApi.getProxies(), dockerApi.getHosts()
      ])
      registries.value = regRes.data
      registryOptions.value = regRes.data.map((r: any) => ({ label: r.name, value: r.id }))
      proxyOptions.value = proxRes.data.map((p: any) => ({ label: p.name, value: p.id }))
      hostOptions.value = hostRes.data.map((h: any) => ({ label: h.name, value: h.id }))
    } catch (e) {}
  }

  const directBuild = async (row: any) => {
    const tag = projectTags[row.id] || 'latest'
    try {
      await imageBuilderApi.buildProject(row.id, { tag: tag })
      message.success(`任务 [${tag}] 已在后台启动，完成后将通过通知告知`)
    } catch (e) { message.error('启动构建失败') }
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
        } catch (e) {
          message.error('清空失败')
        }
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
        catch (e) { message.error('删除失败') }
      }
    })
  }

  return {
    projects, registries, hostOptions, proxyOptions, registryOptions, loading, projectTags,
    fetchProjects, fetchOptions, directBuild, handleClearAllLogs, deleteProject
  }
}
