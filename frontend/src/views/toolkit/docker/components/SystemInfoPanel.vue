<template>
  <div class="system-info-panel">
    <n-grid :cols="2" :x-gap="12" :y-gap="12">
      <n-gi :span="2">
        <n-card title="环境检测" size="small">
          <template #header-extra>
            <n-space>
              <n-button 
                type="warning" size="tiny" secondary 
                @click="showRepairModal = true" 
                :loading="installing"
              >
                一键修复/安装
              </n-button>
              <n-button size="tiny" quaternary @click="fetchInfo" :loading="loading">
                <template #icon><n-icon><refresh-icon /></n-icon></template>
                重新检测
              </n-button>
            </n-space>
          </template>
          
          <n-skeleton v-if="loading" text :repeat="4" />
          <n-descriptions v-else bordered label-placement="left" :column="2">
            <n-descriptions-item label="Docker 版本">
              <n-tag :type="info.docker === '未安装' ? 'error' : 'success'" size="small">
                {{ info.docker }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="Compose 版本">
              <n-tag :type="info.compose === '未安装' ? 'error' : 'success'" size="small">
                {{ info.compose }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="服务状态">
              <n-space align="center">
                <n-badge 
                  :value="info.status === 'active' ? '运行中' : (info.status === 'inactive' ? '已停止' : '未知')" 
                  :type="info.status === 'active' ? 'success' : 'error'" 
                />
                <n-button-group size="tiny" style="margin-left: 12px">
                  <n-button 
                    v-if="info.status !== 'active'" 
                    type="success" ghost 
                    @click="handleServiceAction('start')"
                    :loading="actionLoading === 'start'"
                  >
                    启动
                  </n-button>
                  <n-button 
                    v-if="info.status === 'active'" 
                    type="error" ghost 
                    @click="handleServiceAction('stop')"
                    :loading="actionLoading === 'stop'"
                  >
                    停止
                  </n-button>
                  <n-button 
                    type="warning" ghost 
                    @click="handleServiceAction('restart')"
                    :loading="actionLoading === 'restart'"
                  >
                    重启
                  </n-button>
                </n-button-group>
              </n-space>
            </n-descriptions-item>
            <n-descriptions-item label="操作系统">
              {{ info.os }}
            </n-descriptions-item>
          </n-descriptions>
        </n-card>
      </n-gi>

      <n-gi :span="2" v-if="installing">
        <n-alert title="正在安装环境" type="warning">
          正在远程主机上下载并安装 Docker 及 Docker Compose，这通常需要 1-3 分钟，请耐心等待...
        </n-alert>
      </n-gi>
      
      <n-gi :span="2">
        <n-alert title="环境说明" type="info">
          本页面显示的是远程 Docker 主机的实时环境状态。如果 Docker 或 Compose 未安装，您可以使用“一键修复”功能尝试自动安装。
        </n-alert>
      </n-gi>
    </n-grid>

    <!-- 修复配置弹窗 -->
    <n-modal v-model:show="showRepairModal" preset="card" title="环境修复/安装配置" style="width: 450px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="使用国内镜像">
          <n-switch v-model:value="repairForm.useMirror" />
          <template #feedback>开启后使用阿里云镜像安装，国内环境建议开启</template>
        </n-form-item>
        <n-form-item label="安装代理">
          <n-input v-model:value="repairForm.proxy" placeholder="例如: http://192.168.1.10:7890" />
          <template #feedback>仅在安装过程中生效。留空则不使用代理。</template>
        </n-form-item>
        <n-alert type="warning" size="small">
          此操作将修改远程主机的系统组件。如果主机已有 Docker 运行，执行此操作可能会尝试更新或重置配置。
        </n-alert>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showRepairModal = false">取消</n-button>
          <n-button type="primary" @click="handleRepair" :loading="installing">开始执行</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 安装结果弹窗 -->
    <n-modal v-model:show="showResult" preset="dialog" title="安装结果" style="width: 600px">
      <template #default>
        <div style="background: #1e1e1e; color: #adadad; padding: 10px; font-family: monospace; border-radius: 4px; overflow: auto; max-height: 400px; white-space: pre-wrap;">
          {{ resultOutput }}
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from 'vue'
import { NGrid, NGi, NCard, NDescriptions, NDescriptionsItem, NTag, NBadge, NSkeleton, NButton, NIcon, NAlert, NSpace, NModal, useMessage, useDialog, NForm, NFormItem, NInput, NSwitch, NButtonGroup } from 'naive-ui'
import { RefreshOutlined as RefreshIcon } from '@vicons/material'
import axios from 'axios'

const props = defineProps<{ hostId: string | null }>()
const message = useMessage()

const loading = ref(false)
const installing = ref(false)
const actionLoading = ref<string | null>(null)
const showRepairModal = ref(false)
const showResult = ref(false)
const resultOutput = ref('')

const repairForm = reactive({
  useMirror: true,
  proxy: ''
})

const info = ref({
  docker: '',
  compose: '',
  os: '',
  status: ''
})

const handleServiceAction = async (action: string) => {
  if (!props.hostId) return
  actionLoading.value = action
  try {
    const res = await axios.post(`/api/docker/${props.hostId}/service-action`, { action })
    if (res.data.success) {
      message.success(`服务已尝试${action === 'start' ? '启动' : action === 'stop' ? '停止' : '重启'}`)
    } else {
      message.error('操作失败: ' + res.data.stderr)
    }
    setTimeout(fetchInfo, 1000)
  } catch (e: any) {
    message.error('请求失败')
  } finally {
    actionLoading.value = null
  }
}

const fetchInfo = async () => {
  if (!props.hostId) return
  loading.value = true
  try {
    const res = await axios.get(`/api/docker/${props.hostId}/system-info`)
    info.value = res.data
  } catch (e) {
  } finally {
    loading.value = false
  }
}

const handleRepair = async () => {
  showRepairModal.value = false
  installing.value = true
  try {
    const res = await axios.post(`/api/docker/${props.hostId}/install-env`, { 
      use_mirror: repairForm.useMirror,
      proxy: repairForm.proxy
    })
    resultOutput.value = res.data.stdout || res.data.stderr || '安装已完成。'
    showResult.value = true
    if (res.data.success) message.success('环境任务执行完毕')
    else message.error('安装过程中出现错误')
    fetchInfo()
  } catch (e: any) {
    message.error('请求失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    installing.value = false
  }
}

watch(() => props.hostId, fetchInfo, { immediate: true })
</script>
