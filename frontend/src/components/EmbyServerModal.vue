<template>
  <n-modal
    v-model:show="showModal"
    preset="card"
    :title="form.id ? '编辑 Emby 服务器' : '添加新 Emby 服务器'"
    style="width: 700px"
    :bordered="false"
    size="medium"
    segmented
    @after-leave="onClosed"
  >
    <n-form label-placement="top" :model="form" size="medium">
      <n-grid :cols="2" :x-gap="24">
        <n-form-item-gi label="服务器别名">
          <n-input v-model:value="form.name" placeholder="例如: 我的云端 Emby" />
        </n-form-item-gi>
        <n-form-item-gi label="服务器地址 (IP/URL)">
          <n-input v-model:value="form.url" placeholder="http://1.2.3.4:8096" />
        </n-form-item-gi>
        <n-form-item-gi label="管理级 API Key">
          <n-input v-model:value="form.api_key" type="password" show-password-on="mousedown" />
        </n-form-item-gi>
        <n-form-item-gi label="用户 ID (User ID)">
          <n-input v-model:value="form.user_id" placeholder="可选，由系统自动识别" />
        </n-form-item-gi>
      </n-grid>

      <n-divider title-placement="left">身份认证 (增强功能)</n-divider>
      <n-grid :cols="2" :x-gap="24">
        <n-form-item-gi label="Emby 用户名">
          <n-input v-model:value="form.username" placeholder="管理员用户名" />
        </n-form-item-gi>
        <n-form-item-gi label="Emby 密码">
          <n-input v-model:value="form.password" type="password" show-password-on="mousedown" />
        </n-form-item-gi>
      </n-grid>
      <n-form-item label="会话令牌 (Session Token)">
        <n-input v-model:value="form.session_token" disabled placeholder="登录后自动填充" />
      </n-form-item>
    </n-form>

    <template #footer>
      <n-space justify="end">
        <n-button secondary @click="handleTest" :loading="testing">连通性测试</n-button>
        <n-button type="info" secondary @click="handleLogin" :loading="loggingIn">登录鉴权</n-button>
        <n-button type="primary" @click="handleSave" :loading="saving">保存配置</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { 
  NModal, NForm, NGrid, NFormItemGi, NInput, NDivider, NSpace, NButton, useMessage 
} from 'naive-ui'
import axios from 'axios'

const props = defineProps<{
  show: boolean
  serverData: any
}>()

const emit = defineEmits(['update:show', 'on-success'])

const message = useMessage()
const showModal = ref(false)
const testing = ref(false)
const saving = ref(false)
const loggingIn = ref(false)

const form = reactive({
  id: '',
  name: '',
  url: '',
  api_key: '',
  user_id: '',
  username: '',
  password: '',
  session_token: '',
  emby_id: ''
})

watch(() => props.show, (val) => {
  showModal.value = val
  if (val && props.serverData) {
    Object.assign(form, props.serverData)
  } else if (val) {
    resetForm()
  }
})

watch(showModal, (val) => {
  emit('update:show', val)
})

const resetForm = () => {
  form.id = ''
  form.name = '新服务器'
  form.url = ''
  form.api_key = ''
  form.user_id = ''
  form.username = ''
  form.password = ''
  form.session_token = ''
  form.emby_id = ''
}

const onClosed = () => {
  resetForm()
}

const handleTest = async () => {
  if (!form.url || !form.api_key) {
    message.warning('请先填写 URL 和 API Key')
    return
  }
  testing.value = true
  try {
    const res = await axios.post('/api/server/test', form)
    message.success(`连接成功: ${res.data.server_name || ''}`)
    if (res.data.server_id) form.emby_id = res.data.server_id
  } catch (e: any) {
    message.error(e.response?.data?.detail || '连接失败')
  } finally {
    testing.value = false
  }
}

const handleLogin = async () => {
  if (!form.username) {
    message.warning('请输入用户名')
    return
  }
  loggingIn.value = true
  try {
    const res = await axios.post('/api/server/login', { server_id: form.id || null })
    message.success('登录成功')
    form.session_token = res.data.token
  } catch (e: any) {
    message.error(e.response?.data?.detail || '登录失败')
  } finally {
    loggingIn.value = false
  }
}

const handleSave = async () => {
  if (!form.url || !form.api_key) {
    message.warning('服务器配置不能为空')
    return
  }
  saving.value = true
  try {
    await axios.post('/api/server/save', form)
    message.success('配置已保存')
    emit('on-success')
    showModal.value = false
  } catch (e: any) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>
