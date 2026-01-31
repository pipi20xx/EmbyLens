import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { notificationApi } from '@/api/notification'

export function useNotificationManager() {
  const message = useMessage()
  const settings = ref<any>({ enabled: false, bots: [] })
  const showEditModal = ref(false)
  const showTestModal = ref(false)
  const saving = ref(false)
  const testMessage = ref('这是一条来自 Lens 的测试消息')
  const currentBotId = ref('')

  const editingBot = ref<any>({
    id: '',
    name: '',
    type: 'telegram',
    token: '',
    chat_id: '',
    enabled: true,
    subscribed_events: ['backup.success', 'backup.failed'],
    is_interactive: false,
    allowed_user_ids: []
  })

  const fetchSettings = async () => {
    const data: any = await notificationApi.getSettings()
    settings.value = data
  }

  const saveSettings = async () => {
    await notificationApi.saveSettings(settings.value)
    message.success('设置已更新')
  }

  const handleAddBot = () => {
    editingBot.value = {
      id: '',
      name: '',
      type: 'telegram',
      token: '',
      chat_id: '',
      enabled: true,
      subscribed_events: ['backup.success', 'backup.failed'],
      is_interactive: false,
      allowed_user_ids: []
    }
    showEditModal.value = true
  }

  const handleEditBot = (bot: any) => {
    editingBot.value = JSON.parse(JSON.stringify(bot))
    if (!editingBot.value.allowed_user_ids) editingBot.value.allowed_user_ids = []
    showEditModal.value = true
  }

  const handleSaveBot = async () => {
    if (!editingBot.value.name || !editingBot.value.token || !editingBot.value.chat_id) {
      message.warning('请填写完整信息')
      return
    }

    saving.value = true
    try {
      if (editingBot.value.id) {
        await notificationApi.updateBot(editingBot.value.id, editingBot.value)
      } else {
        await notificationApi.addBot(editingBot.value)
      }
      message.success('保存成功')
      showEditModal.value = false
      fetchSettings()
    } finally {
      saving.value = false
    }
  }

  const handleDeleteBot = async (id: string) => {
    await notificationApi.deleteBot(id)
    message.success('已删除')
    fetchSettings()
  }

  const handleTestBot = (id: string) => {
    currentBotId.value = id
    showTestModal.value = true
  }

  const sendTestMessage = async () => {
    try {
      await notificationApi.testBot({
        bot_id: currentBotId.value,
        message: testMessage.value
      })
      message.success('消息已发送，请在 Telegram 中查看')
    } catch (err: any) { }
  }

  return {
    settings, showEditModal, showTestModal, saving, testMessage, editingBot,
    fetchSettings, saveSettings, handleAddBot, handleEditBot, handleSaveBot, handleDeleteBot, handleTestBot, sendTestMessage
  }
}