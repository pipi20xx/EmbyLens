import { reactive } from 'vue'
import { useMessage } from 'naive-ui'
import { authApi } from '@/api/auth'

export function useAuthManager() {
  const message = useMessage()

  const pwdForm = reactive({
    old_password: '',
    new_password: ''
  })

  const authInfo = reactive({
    is_otp_enabled: false,
    ui_auth_enabled: true
  })

  const otpSetup = reactive({
    qr_code: '',
    secret: '',
    code: ''
  })

  const toggleGlobalAuth = async () => {
    try {
      await authApi.updateSystemConfig([
        { key: 'ui_auth_enabled', value: String(authInfo.ui_auth_enabled) }
      ])
      message.success(authInfo.ui_auth_enabled ? '已开启登录验证' : '已关闭登录验证 (免密模式)')
    } catch (err) {
      message.error('设置失败')
      authInfo.ui_auth_enabled = !authInfo.ui_auth_enabled
    }
  }

  const loadAuthInfo = async () => {
    try {
      const res = await authApi.getMe()
      authInfo.is_otp_enabled = res.data.is_otp_enabled
      
      const statusRes = await authApi.getStatus()
      authInfo.ui_auth_enabled = statusRes.data.ui_auth_enabled
    } catch (err) {}
  }

  const setupOtp = async () => {
    try {
      const res = await authApi.setup2fa()
      otpSetup.qr_code = res.data.qr_code
      otpSetup.secret = res.data.secret
    } catch (err) {
      message.error('获取 2FA 设置失败')
    }
  }

  const enableOtp = async () => {
    if (!otpSetup.code) return
    try {
      await authApi.enable2fa(otpSetup.code)
      message.success('双重验证已成功开启')
      authInfo.is_otp_enabled = true
      otpSetup.qr_code = ''
      otpSetup.code = ''
    } catch (err) {
      message.error('验证失败，请检查验证码是否正确')
    }
  }

  const disableOtp = async () => {
    try {
      await authApi.disable2fa()
      message.success('双重验证已停用')
      authInfo.is_otp_enabled = false
    } catch (err) {
      message.error('操作失败')
    }
  }

  const handleChangePassword = async () => {
    if (!pwdForm.old_password || !pwdForm.new_password) {
      message.warning('请填写完整的密码信息')
      return
    }
    try {
      await authApi.changePassword(pwdForm)
      message.success('密码修改成功')
      pwdForm.old_password = ''
      pwdForm.new_password = ''
    } catch (err) {
      message.error('密码修改失败')
    }
  }

  return {
    pwdForm, authInfo, otpSetup,
    toggleGlobalAuth, loadAuthInfo, setupOtp, enableOtp, disableOtp, handleChangePassword
  }
}
