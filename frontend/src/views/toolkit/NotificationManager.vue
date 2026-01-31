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
import { onMounted, h } from 'vue'
import { 
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

// 导入提取的逻辑
import { useNotificationManager } from './notification/hooks/useNotificationManager'

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

const {
  settings, showEditModal, showTestModal, saving, testMessage, editingBot,
  fetchSettings, saveSettings, handleAddBot, handleEditBot, handleSaveBot, handleDeleteBot, handleTestBot, sendTestMessage
} = useNotificationManager()

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
