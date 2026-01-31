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
      authInfo.ui_auth_enabled = !authInfo.ui_auth_enabled
    }
  }

  const loadAuthInfo = async () => {
    const meData: any = await authApi.getMe()
    authInfo.is_otp_enabled = meData.is_otp_enabled
    
    const statusData: any = await authApi.getStatus()
    authInfo.ui_auth_enabled = statusData.ui_auth_enabled
  }

  const setupOtp = async () => {
    const data: any = await authApi.setup2fa()
    otpSetup.qr_code = data.qr_code
    otpSetup.secret = data.secret
  }

  const enableOtp = async () => {
    if (!otpSetup.code) return
    await authApi.enable2fa(otpSetup.code)
    message.success('双重验证已成功开启')
    authInfo.is_otp_enabled = true
    otpSetup.qr_code = ''
    otpSetup.code = ''
  }

  const disableOtp = async () => {
    await authApi.disable2fa()
    message.success('双重验证已停用')
    authInfo.is_otp_enabled = false
  }

  const handleChangePassword = async () => {
    if (!pwdForm.old_password || !pwdForm.new_password) {
      message.warning('请填写完整的密码信息')
      return
    }
    await authApi.changePassword(pwdForm)
    message.success('密码修改成功')
    pwdForm.old_password = ''
    pwdForm.new_password = ''
  }

  return {
    pwdForm, authInfo, otpSetup,
    toggleGlobalAuth, loadAuthInfo, setupOtp, enableOtp, disableOtp, handleChangePassword
  }
}