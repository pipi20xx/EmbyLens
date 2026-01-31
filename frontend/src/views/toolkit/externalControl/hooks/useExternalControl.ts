import { ref, reactive } from 'vue'
import { useMessage } from 'naive-ui'
import { systemApi } from '@/api/system'
import { copyText } from '@/utils/clipboard'

export function useExternalControl() {
  const message = useMessage()
  const loadingLogs = ref(false)
  const auditLogs = ref([])
  const showLogDetail = ref(false)
  const currentPayload = ref('')
  const activeTab = ref('api_key')

  const pagination = reactive({
    page: 1,
    pageSize: 15,
    itemCount: 0,
    showSizePicker: true,
    pageSizes: [15, 30, 50],
  })

  const config = reactive({ api_token: '', auth_enabled: false, audit_enabled: true })

  const loadConfig = async () => {
    try {
      const res = await systemApi.getConfig()
      config.api_token = res.data.api_token || ''
      config.auth_enabled = res.data.ui_auth_enabled === 'true' || res.data.ui_auth_enabled === true
      config.audit_enabled = res.data.audit_enabled !== 'false' && res.data.audit_enabled !== false
    } catch (err) { message.error('加载配置失败') }
  }

  const saveSettings = async () => {
    try {
      await systemApi.saveConfig([
        { key: 'ui_auth_enabled', value: String(config.auth_enabled) },
        { key: 'audit_enabled', value: String(config.audit_enabled) }
      ])
      message.success('设置已保存')
    } catch (err) { message.error('保存设置失败') }
  }

  const generateNewToken = async () => {
    try {
      const res = await systemApi.generateToken()
      const newToken = res.data.token
      await systemApi.saveConfig([{ key: 'api_token', value: newToken }])
      config.api_token = newToken
      message.success('新 Token 已生成')
    } catch (err) { message.error('生成 Token 失败') }
  }

  const copyToken = async () => {
    if (await copyText(config.api_token)) {
      message.info('Token 已复制到剪贴板')
    } else {
      message.error('复制失败，请手动复制')
    }
  }

  const fetchLogs = async () => {
    loadingLogs.value = true
    try {
      const res = await systemApi.getAuditLogs({ page: pagination.page, page_size: pagination.pageSize })
      auditLogs.value = res.data.items
      pagination.itemCount = res.data.total
    } catch (err) { message.error('加载审计日志失败') }
    finally { loadingLogs.value = false }
  }

  const handlePageChange = (page: number) => { pagination.page = page; fetchLogs() }
  const handlePageSizeChange = (pageSize: number) => { pagination.pageSize = pageSize; pagination.page = 1; fetchLogs() }

  return {
    config, auditLogs, loadingLogs, pagination, showLogDetail, currentPayload, activeTab,
    loadConfig, saveSettings, generateNewToken, copyToken, fetchLogs, handlePageChange, handlePageSizeChange
  }
}
