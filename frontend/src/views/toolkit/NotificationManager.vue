<template>
  <div class="notification-manager">
    <n-space vertical size="large">
      <n-card title="通知中心设置" subtitle="配置多个 Telegram Bot 或其他推送通道，实现高度自定义的消息通知">
        <template #header-extra>
          <n-space align="center">
            <span>启用通知系统</span>
            <n-switch v-model:value="settings.enabled" @update:value="saveSettings" />
          </n-space>
        </template>
        <div class="settings-content">
          <n-alert type="info" bordered>
            你可以添加多个机器人，并为每个机器人分配不同的订阅事件。例如：一个机器人专门接收备份通知，另一个接收系统告警。
          </n-alert>
        </div>
      </n-card>

      <n-card title="机器人列表">
        <template #header-extra>
          <n-button type="primary" size="small" @click="handleAddBot">
            <template #icon>
              <n-icon><add-icon /></n-icon>
            </template>
            添加机器人
          </n-button>
        </template>

        <n-data-table
          :columns="columns"
          :data="settings.bots"
          :bordered="false"
        />
      </n-card>
    </n-space>

    <!-- 机器人编辑弹窗 -->
    <n-modal v-model:show="showEditModal" preset="card" :title="editingBot.id ? '编辑机器人' : '添加机器人'" style="width: 600px">
      <n-form
        ref="formRef"
        :model="editingBot"
        label-placement="left"
        label-width="100"
        require-mark-placement="right-asterisk"
      >
        <n-form-item label="名称" path="name">
          <n-input v-model:value="editingBot.name" placeholder="例如：Lens 备份助手" />
        </n-form-item>
        <n-form-item label="类型" path="type">
          <n-select v-model:value="editingBot.type" :options="typeOptions" disabled />
        </n-form-item>
        <n-form-item label="Bot Token" path="token">
          <n-input v-model:value="editingBot.token" type="password" show-password-on="click" placeholder="Telegram Bot API Token" />
        </n-form-item>
        <n-form-item label="Chat ID" path="chat_id">
          <n-input v-model:value="editingBot.chat_id" placeholder="接收通知的 Chat ID" />
        </n-form-item>
        <n-form-item label="订阅事件" path="subscribed_events">
          <n-select
            v-model:value="editingBot.subscribed_events"
            multiple
            filterable
            tag
            :options="eventOptions"
            placeholder="请选择要订阅的事件"
          />
        </n-form-item>
        <n-form-item label="开启交互">
          <n-space vertical style="width: 100%">
            <n-switch v-model:value="editingBot.is_interactive" />
            <n-alert v-if="editingBot.is_interactive" type="warning" size="small">
              开启后，你可以通过 Telegram 直接操控 Docker。请务必配置下方的授权用户 ID 以确保安全。
            </n-alert>
          </n-space>
        </n-form-item>
        <n-form-item v-if="editingBot.is_interactive" label="授权用户 ID">
          <n-select
            v-model:value="editingBot.allowed_user_ids"
            multiple
            filterable
            tag
            placeholder="输入你的 Telegram User ID 并回车"
          />
        </n-form-item>
        <n-form-item label="是否启用">
          <n-switch v-model:value="editingBot.enabled" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="handleSaveBot">确定</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 测试消息弹窗 -->
    <n-modal v-model:show="showTestModal" preset="dialog" title="发送测试消息" positive-text="发送" negative-text="取消" @positive-click="sendTestMessage">
      <n-input v-model:value="testMessage" type="textarea" placeholder="输入测试内容..." />
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { 
  useMessage, 
  NButton, 
  NSpace, 
  NTag, 
  NPopconfirm,
  NCard,
  NSwitch,
  NAlert,
  NDataTable,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  DataTableColumns
} from 'naive-ui'
import { AddOutlined as AddIcon } from '@vicons/material'
import axios from 'axios'

interface NotificationBot {
  id: string
  name: string
  type: string
  token: string
  chat_id: string
  enabled: boolean
  subscribed_events: string[]
  is_interactive: boolean
  allowed_user_ids: string[]
}

interface NotificationSettings {
  enabled: boolean
  bots: NotificationBot[]
}

const message = useMessage()
const settings = ref<NotificationSettings>({ enabled: false, bots: [] })
const showEditModal = ref(false)
const showTestModal = ref(false)
const saving = ref(false)
const testMessage = ref('这是一条来自 Lens 的测试消息')
const currentBotId = ref('')
const newUserIds = ref('')

const editingBot = ref<NotificationBot>({
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

const typeOptions = [
  { label: 'Telegram', value: 'telegram' }
]

const eventOptions = [
  { label: '所有事件 (*)', value: '*' },
  { label: '备份成功 (backup.success)', value: 'backup.success' },
  { label: '备份失败 (backup.failed)', value: 'backup.failed' },
  { label: '登录提醒 (auth.login)', value: 'auth.login' },
  { label: '标签匹配 (autotag.match)', value: 'autotag.match' },
  { label: '标签任务完成 (autotag.task_done)', value: 'autotag.task_done' },
  { label: '容器操作 (docker.container_action)', value: 'docker.container_action' },
  { label: '主机维护 (docker.host_action)', value: 'docker.host_action' },
  { label: '系统告警 (system.alert)', value: 'system.alert' }
]

const columns: DataTableColumns<NotificationBot> = [
  { title: '名称', key: 'name' },
  { 
    title: '状态', 
    key: 'enabled',
    render(row) {
      return h(NTag, { type: row.enabled ? 'success' : 'default', size: 'small' }, { default: () => row.enabled ? '启用' : '禁用' })
    }
  },
  {
    title: '订阅事件',
    key: 'subscribed_events',
    render(row) {
      return h(NSpace, { size: 'small' }, {
        default: () => row.subscribed_events.map(ev => h(NTag, { size: 'tiny', bordered: false, type: 'info' }, { default: () => ev }))
      })
    }
  },
  {
    title: '操作',
    key: 'actions',
    render(row) {
      return h(NSpace, {}, {
        default: () => [
          h(NButton, { size: 'tiny', secondary: true, onClick: () => handleTestBot(row.id) }, { default: () => '测试' }),
          h(NButton, { size: 'tiny', onClick: () => handleEditBot(row) }, { default: () => '编辑' }),
          h(NPopconfirm, { onPositiveClick: () => handleDeleteBot(row.id) }, {
            trigger: () => h(NButton, { size: 'tiny', type: 'error', secondary: true }, { default: () => '删除' }),
            default: () => '确定删除该机器人吗？'
          })
        ]
      })
    }
  }
]

const fetchSettings = async () => {
  try {
    const res = await axios.get('/api/notification/settings')
    settings.value = res.data
  } catch (err) {
    message.error('加载设置失败')
  }
}

const saveSettings = async () => {
  try {
    await axios.post('/api/notification/settings', settings.value)
    message.success('设置已更新')
  } catch (err) {
    message.error('保存设置失败')
  }
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

const handleEditBot = (bot: NotificationBot) => {
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
      await axios.put(`/api/notification/bots/${editingBot.value.id}`, editingBot.value)
    } else {
      await axios.post('/api/notification/bots', editingBot.value)
    }
    message.success('保存成功')
    showEditModal.value = false
    fetchSettings()
  } catch (err) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleDeleteBot = async (id: string) => {
  try {
    await axios.delete(`/api/notification/bots/${id}`)
    message.success('已删除')
    fetchSettings()
  } catch (err) {
    message.error('删除失败')
  }
}

const handleTestBot = (id: string) => {
  currentBotId.value = id
  showTestModal.value = true
}

const sendTestMessage = async () => {
  try {
    await axios.post('/api/notification/test', {
      bot_id: currentBotId.value,
      message: testMessage.value
    })
    message.success('消息已发送，请在 Telegram 中查看')
  } catch (err: any) {
    message.error('发送失败: ' + (err.response?.data?.detail || err.message))
  }
}

onMounted(fetchSettings)
</script>

<style scoped>
.notification-manager {
  max-width: 1200px;
  margin: 0 auto;
}
.settings-content {
  padding: 10px 0;
}
</style>
