<template>
  <div class="account-container">
    <n-scrollbar style="max-height: calc(100vh - 64px)">
      <div class="account-content">
        <n-space vertical size="large">
          <div class="page-header">
            <n-h2 prefix="bar" align-text>
              <n-text type="primary">账号安全管理</n-text>
            </n-h2>
            <n-text depth="3">
              维护管理员凭据及多因素认证设置。
            </n-text>
          </div>

          <n-grid x-gap="24" y-gap="24" cols="1 s:1 m:2 l:2" responsive="screen">
            <!-- 0. 全局登录开关 (新增) -->
            <n-gi span="1 s:1 m:2 l:2">
              <n-card title="系统访问安全" size="small" :bordered="false">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <n-thing title="强制登录验证" description="开启后，访问系统必须先通过账号密码登录。关闭则直接进入仪表盘。" />
                  <n-switch v-model:value="authInfo.ui_auth_enabled" @update:value="toggleGlobalAuth" size="large">
                    <template #checked>已开启</template>
                    <template #unchecked>已关闭</template>
                  </n-switch>
                </div>
              </n-card>
            </n-gi>

            <!-- 1. 密码修改 -->
            <n-gi>
              <n-card title="修改管理员密码" size="small" :bordered="false" style="height: 100%">
                <n-form size="medium">
                  <n-form-item label="旧密码">
                    <n-input v-model:value="pwdForm.old_password" type="password" show-password-on="mousedown" placeholder="请输入当前密码" />
                  </n-form-item>
                  <n-form-item label="新密码">
                    <n-input v-model:value="pwdForm.new_password" type="password" show-password-on="mousedown" placeholder="请输入新密码" />
                  </n-form-item>
                  <n-button type="primary" block @click="handleChangePassword" style="height: 44px; border-radius: 8px;">
                    确认修改密码
                  </n-button>
                </n-form>
              </n-card>
            </n-gi>

            <!-- 2. 2FA 设置 -->
            <n-gi>
              <n-card title="双重验证 (2FA)" size="small" :bordered="false" style="height: 100%">
                <n-space vertical size="large">
                  <n-alert 
                    :type="authInfo.is_otp_enabled ? 'success' : 'warning'" 
                    :title="authInfo.is_otp_enabled ? '已开启安全保护' : '未开启保护'"
                  >
                    {{ authInfo.is_otp_enabled ? '登录时需要输入动态验证码。' : '建议开启以防止密码泄露导致账号被盗。' }}
                  </n-alert>
                  
                  <!-- 未开启状态 -->
                  <div v-if="!authInfo.is_otp_enabled">
                    <div v-if="!otpSetup.qr_code">
                      <n-p depth="3">使用 Google Authenticator 或微软验证器扫描二维码进行绑定。</n-p>
                      <n-button block type="primary" @click="setupOtp" style="height: 44px; margin-top: 10px;">
                        开始设置 2FA
                      </n-button>
                    </div>
                    
                    <div v-else style="display: flex; flex-direction: column; align-items: center;">
                      <div style="background: white; padding: 8px; border-radius: 8px; margin-bottom: 16px;">
                        <img :src="otpSetup.qr_code" style="width: 180px; display: block;" />
                      </div>
                      <n-input-group>
                        <n-input v-model:value="otpSetup.code" placeholder="输入 6 位验证码" maxlength="6" />
                        <n-button type="primary" @click="enableOtp">确认绑定</n-button>
                      </n-input-group>
                      <n-button text @click="otpSetup.qr_code = ''" style="margin-top: 10px;">返回</n-button>
                    </div>
                  </div>
                  
                  <!-- 已开启状态 -->
                  <n-button 
                    v-else 
                    block 
                    @click="disableOtp" 
                    type="error" 
                    secondary 
                    style="height: 44px; border-radius: 8px;"
                  >
                    停用双重验证 (2FA)
                  </n-button>
                </n-space>
              </n-card>
            </n-gi>
          </n-grid>
        </n-space>
      </div>
    </n-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { 
  NScrollbar, NSpace, NH2, NText, NCard, NForm, NFormItem, 
  NInput, NButton, NGrid, NGi, NAlert, NInputGroup, NSwitch, NThing, NP
} from 'naive-ui'

// 导入提取的逻辑
import { useAuthManager } from './auth/hooks/useAuthManager'

const { 
  pwdForm, authInfo, otpSetup,
  toggleGlobalAuth, loadAuthInfo, setupOtp, enableOtp, disableOtp, handleChangePassword 
} = useAuthManager()

onMounted(() => {
  loadAuthInfo()
})
</script>

<style scoped>
.account-container {
  height: 100%;
  padding: 16px;
}
@media (min-width: 768px) {
  .account-container {
    padding: 24px;
  }
}
.account-content {
  width: 100%;
}
</style>
