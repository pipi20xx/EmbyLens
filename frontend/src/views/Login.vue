<template>
  <div class="login-container">
    <!-- 动态背景装饰 -->
    <div class="bg-decoration top-left"></div>
    <div class="bg-decoration bottom-right"></div>

    <n-card class="login-card" :bordered="false">
      <div class="login-header">
        <n-icon size="48" color="var(--n-primary-color)"><LockIcon /></n-icon>
        <n-h2>Lens</n-h2>
        <n-text depth="3">请输入管理员凭据以访问系统</n-text>
      </div>

      <n-form ref="formInst" :model="formValue" :rules="rules" size="large">
        <template v-if="!showOtp">
          <n-form-item path="username">
            <n-input v-model:value="formValue.username" placeholder="用户名">
              <template #prefix><n-icon><UserIcon /></n-icon></template>
            </n-input>
          </n-form-item>
          <n-form-item path="password">
            <n-input
              v-model:value="formValue.password"
              type="password"
              show-password-on="mousedown"
              placeholder="密码"
              @keyup.enter="handleLogin"
            >
              <template #prefix><n-icon><KeyIcon /></n-icon></template>
            </n-input>
          </n-form-item>
        </template>

        <template v-else>
          <n-form-item label="双重验证码" path="otp_code">
            <n-input
              v-model:value="formValue.otp_code"
              placeholder="请输入 6 位动态验证码"
              maxlength="6"
              @keyup.enter="handleLogin"
              autofocus
            >
              <template #prefix><n-icon><LockIcon /></n-icon></template>
            </n-input>
          </n-form-item>
          <n-button text block @click="showOtp = false" style="margin-bottom: 10px;">返回账号登录</n-button>
        </template>
        
        <n-button
          type="primary"
          block
          strong
          :loading="loading"
          @click="handleLogin"
          style="margin-top: 10px; height: 48px;"
        >
          {{ showOtp ? '验证并登录' : '立即登录' }}
        </n-button>
      </n-form>

      <div class="login-footer">
        <n-text depth="3">Initial Admin: admin / admin123</n-text>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { 
  NCard, NForm, NFormItem, NInput, NButton, NIcon, NH2, NText, useMessage 
} from 'naive-ui'
import { 
  LockOpenOutlined as LockIcon,
  PersonOutlined as UserIcon,
  KeyOutlined as KeyIcon
} from '@vicons/material'
import axios from 'axios'
import { loginSuccess, initMenuSettingsFromBackend } from '../store/navigationStore'

const message = useMessage()
const router = useRouter()
const loading = ref(false)
const showOtp = ref(false)

const formValue = reactive({
  username: '',
  password: '',
  otp_code: ''
})

const rules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' },
  otp_code: { len: 6, message: '请输入 6 位验证码', trigger: 'input' }
}

const handleLogin = async () => {
  if (!formValue.username || !formValue.password) {
    message.warning('请填写完整信息')
    return
  }

  loading.value = true
  try {
    const res = await axios.post('/api/auth/login', formValue)
    
    if (res.data.status === '2fa_required') {
      showOtp.value = true
      localStorage.setItem('lens_access_token', res.data.access_token)
      message.info('请输入双重验证码')
    } else {
      loginSuccess(res.data.access_token, res.data.username)
      // 初始化菜单设置
      initMenuSettingsFromBackend()
      message.success(`欢迎回来, ${res.data.username}`)
      router.push('/')
    }
  } catch (err: any) {
    message.error(err.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #000;
  position: relative;
  overflow: hidden;
}

.bg-decoration {
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
  z-index: 0;
}

.top-left {
  top: -100px;
  left: -100px;
  background-color: var(--n-primary-color);
}

.bottom-right {
  bottom: -100px;
  right: -100px;
  background-color: #03dac6;
}

.login-card {
  width: 420px;
  z-index: 1;
  background-color: rgba(24, 24, 28, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  padding: 32px;
  border-radius: 24px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  margin: 12px 0 8px 0;
  letter-spacing: 4px;
  font-weight: 700;
}

.login-footer {
  margin-top: 30px;
  text-align: center;
  font-size: 12px;
}
</style>
