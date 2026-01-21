<template>
  <div class="maintenance-panel">
    <n-grid :cols="2" :x-gap="12" :y-gap="12">
      <n-gi :span="2">
        <n-card title="Docker Daemon 配置" size="small">
          <template #header-extra>
            <n-space align="center">
              <n-button size="tiny" quaternary type="primary" @click="openRawEdit">直接编辑 JSON</n-button>
              <n-text depth="3" type="warning" style="font-size: 12px">
                <n-icon><warning-icon /></n-icon> 需要 Root 权限的 SSH 账户
              </n-text>
            </n-space>
          </template>

          <n-alert type="info" size="small" style="margin-bottom: 16px" :show-icon="true">
            该配置将直接修改远程主机的 <n-text code>/etc/docker/daemon.json</n-text> 文件。保存前建议确保了解配置项的含义。
          </n-alert>
          
          <n-form label-placement="top" :disabled="loading.daemon">
            <n-grid :cols="2" :x-gap="24">
              <n-gi>
                <n-form-item label="镜像加速器 (Registry Mirrors)">
                  <n-input
                    v-model:value="daemonForm.mirrors"
                    type="textarea"
                    placeholder="每行一个 URL，例如: https://docker.fnnas.com"
                    :autosize="{ minRows: 3 }"
                  />
                </n-form-item>
                <n-form-item label="私有仓库 (Insecure Registries)">
                  <n-input
                    v-model:value="daemonForm.insecure"
                    type="textarea"
                    placeholder="每行一个地址，例如: 192.168.50.12:6100"
                    :autosize="{ minRows: 3 }"
                  />
                </n-form-item>
                
                <n-space vertical style="border: 1px solid #333; padding: 12px; border-radius: 4px">
                  <n-space align="center" justify="space-between">
                    <n-space align="center" size="small">
                      <n-text strong>代理设置 (Proxies)</n-text>
                      <n-tag size="tiny" :type="daemonForm.proxyEnabled ? 'success' : 'default'">
                        {{ daemonForm.proxyEnabled ? '已启用' : '已禁用' }}
                      </n-tag>
                    </n-space>
                    <n-switch v-model:value="daemonForm.proxyEnabled" size="small" />
                  </n-space>
                  
                  <template v-if="daemonForm.proxyEnabled">
                    <n-alert type="warning" size="small" :show-icon="false">
                      注意：Docker 守护进程通常仅支持 HTTP/HTTPS 协议代理，暂不支持 SOCKS5。
                    </n-alert>
                    <n-grid :cols="4" :x-gap="8">
                      <n-gi :span="3">
                        <n-form-item label="服务器地址" size="small">
                          <n-input v-model:value="daemonForm.proxyHost" placeholder="例如: 192.168.50.66" />
                        </n-form-item>
                      </n-gi>
                      <n-gi>
                        <n-form-item label="端口" size="small">
                          <n-input v-model:value="daemonForm.proxyPort" placeholder="7890" />
                        </n-form-item>
                      </n-gi>
                    </n-grid>
                    <n-grid :cols="2" :x-gap="8">
                      <n-gi>
                        <n-form-item label="用户名 (可选)" size="small">
                          <n-input v-model:value="daemonForm.proxyUser" placeholder="可选" />
                        </n-form-item>
                      </n-gi>
                      <n-gi>
                        <n-form-item label="密码 (可选)" size="small">
                          <n-input v-model:value="daemonForm.proxyPass" type="password" show-password-on="click" placeholder="可选" />
                        </n-form-item>
                      </n-gi>
                    </n-grid>
                    <n-form-item label="无需代理地址 (No Proxy)" size="small">
                      <n-input v-model:value="daemonForm.noProxy" placeholder="localhost,127.0.0.1" />
                    </n-form-item>
                  </template>
                </n-space>
              </n-gi>
              <n-gi>
                <n-grid :cols="2" :x-gap="12">
                  <n-gi>
                    <n-form-item label="日志单文件大小">
                      <n-input v-model:value="daemonForm.logSize" placeholder="例如: 100m" />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item label="日志保留份数">
                      <n-input-number v-model:value="daemonForm.logFiles" :min="1" style="width: 100%" />
                    </n-form-item>
                  </n-gi>
                </n-grid>
                <n-space vertical>
                  <n-checkbox v-model:checked="daemonForm.liveRestore">
                    开启 Live Restore (守护进程重启时不停止容器)
                  </n-checkbox>
                  <n-alert type="info" size="small" :show-icon="false">
                    保存时将自动备份旧配置至本地 data 目录及远程 .bak 文件。
                  </n-alert>
                  <n-space align="center">
                    <n-checkbox v-model:checked="daemonForm.shouldRestart">
                      保存后重启 Docker 服务 (会导致容器短暂中断)
                    </n-checkbox>
                  </n-space>
                </n-space>
              </n-gi>
            </n-grid>
            <n-space justify="end" style="margin-top: 12px">
              <n-button type="primary" :loading="loading.daemon" @click="handleSaveDaemonConfig">
                保存并应用配置
              </n-button>
            </n-space>
          </n-form>
        </n-card>
      </n-gi>

      <n-gi>
        <n-card title="镜像清理" size="small">
          <n-space vertical size="large">
            <n-text depth="3">清理无用的 Docker 镜像以释放磁盘空间。</n-text>
            <n-space item-style="display: flex; align-items: center">
              <n-checkbox v-model:checked="imageOptions.dangling">
                清理未标签镜像 (Dangling)
              </n-checkbox>
              <n-checkbox v-model:checked="imageOptions.all">
                清理所有未使用镜像 (Unused)
              </n-checkbox>
            </n-space>
            <n-button type="primary" secondary :loading="loading.images" @click="handlePruneImages">
              开始清理镜像
            </n-button>
          </n-space>
        </n-card>
      </n-gi>

      <n-gi>
        <n-card title="构建缓存清理" size="small">
          <n-space vertical size="large">
            <n-text depth="3">清理 Docker Buildx 或 BuildKit 的构建缓存。</n-text>
            <div style="height: 24px"></div> <!-- 保持高度对齐 -->
            <n-button type="warning" secondary :loading="loading.cache" @click="handlePruneCache">
              开始清理构建缓存
            </n-button>
          </n-space>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 结果弹窗 -->
    <n-modal v-model:show="showResult" preset="dialog" title="清理结果" style="width: 600px">
      <template #default>
        <div style="background: #1e1e1e; color: #adadad; padding: 10px; font-family: monospace; border-radius: 4px; overflow: auto; max-height: 400px; white-space: pre-wrap;">
          {{ resultOutput }}
        </div>
      </template>
    </n-modal>

    <!-- 原生 JSON 编辑弹窗 -->
    <n-modal v-model:show="showRawModal" preset="card" title="直接编辑 daemon.json" style="width: 800px">
      <n-space vertical size="large">
        <n-alert type="warning" size="small">
          警告：直接编辑 JSON 可能会导致 Docker 无法启动。系统将会在保存前验证 JSON 格式并自动创建备份。
        </n-alert>
        <n-input
          v-model:value="rawJsonContent"
          type="textarea"
          placeholder="{ ... }"
          :autosize="{ minRows: 15, maxRows: 25 }"
          style="font-family: monospace"
          @input="validateRawJson"
        />
        <n-text v-if="rawJsonError" type="error" style="font-size: 12px">{{ rawJsonError }}</n-text>
        
        <n-space align="center">
          <n-checkbox v-model:checked="daemonForm.shouldRestart">
            保存后重启 Docker 服务
          </n-checkbox>
        </n-space>
      </n-space>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showRawModal = false">取消</n-button>
          <n-button type="primary" :disabled="!!rawJsonError" @click="handleSaveRawJson" :loading="loading.daemon">
            保存原始配置
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, h } from 'vue'
import { NGrid, NGi, NCard, NSpace, NText, NCheckbox, NSwitch, NButton, NModal, NForm, NFormItem, NInput, NInputNumber, NAlert, NIcon, useMessage, useDialog, NTag } from 'naive-ui'
import { WarningAmberOutlined as WarningIcon } from '@vicons/material'
import axios from 'axios'

const props = defineProps({
  hostId: String | null
})

const message = useMessage()
const dialog = useDialog()
const loading = ref({ images: false, cache: false, daemon: false })
const showResult = ref(false)
const showRawModal = ref(false)
const rawJsonContent = ref('')
const rawJsonError = ref<string | null>(null)
const resultOutput = ref('')

const imageOptions = ref({
  dangling: true,
  all: false
})

const daemonForm = ref({
  mirrors: '',
  insecure: '',
  logSize: '100m',
  logFiles: 5,
  liveRestore: true,
  shouldRestart: false,
  proxyEnabled: false,
  proxyHost: '',
  proxyPort: '',
  proxyUser: '',
  proxyPass: '',
  noProxy: 'localhost,127.0.0.1'
})

const rawDaemonConfig = ref<any>({})

const fetchDaemonConfig = async () => {
  if (!props.hostId) return
  loading.value.daemon = true
  try {
    const res = await axios.get(`/api/docker/${props.hostId}/daemon-config`)
    rawDaemonConfig.value = res.data
    
    daemonForm.value.mirrors = (res.data['registry-mirrors'] || []).join('\n')
    daemonForm.value.insecure = (res.data['insecure-registries'] || []).join('\n')
    daemonForm.value.logSize = res.data['log-opts']?.['max-size'] || '100m'
    daemonForm.value.logFiles = parseInt(res.data['log-opts']?.['max-file'] || '5')
    daemonForm.value.liveRestore = res.data['live-restore'] ?? true
    
    const proxies = res.data['proxies'] || {}
    const httpProxy = proxies['http-proxy'] || ''
    daemonForm.value.noProxy = proxies['no-proxy'] || 'localhost,127.0.0.1'
    
    if (httpProxy) {
      daemonForm.value.proxyEnabled = true
      try {
        const url = new URL(httpProxy)
        daemonForm.value.proxyHost = url.hostname
        daemonForm.value.proxyPort = url.port
        daemonForm.value.proxyUser = decodeURIComponent(url.username)
        daemonForm.value.proxyPass = decodeURIComponent(url.password)
      } catch (e) {
        daemonForm.value.proxyHost = httpProxy
      }
    } else {
      daemonForm.value.proxyEnabled = false
    }
  } catch (e) {
    message.error('无法读取 Daemon 配置')
  } finally {
    loading.value.daemon = false
  }
}

watch(() => props.hostId, fetchDaemonConfig, { immediate: true })

const openRawEdit = async () => {
  if (!props.hostId) return
  loading.value.daemon = true
  try {
    const res = await axios.get(`/api/docker/${props.hostId}/daemon-config/raw`)
    rawJsonContent.value = res.data.content
    rawJsonError.value = null
    showRawModal.value = true
  } catch (e) {
    message.error('无法读取原始配置')
  } finally {
    loading.value.daemon = false
  }
}

const validateRawJson = (val: string) => {
  if (!val.trim()) {
    rawJsonError.value = '内容不能为空'
    return
  }
  try {
    JSON.parse(val)
    rawJsonError.value = null
  } catch (e: any) {
    rawJsonError.value = '无效的 JSON 格式'
  }
}

const handleSaveRawJson = () => {
  if (rawJsonError.value) return
  
  dialog.warning({
    title: '确认保存原始配置',
    content: () => h('div', null, [
      h('p', null, daemonForm.value.shouldRestart 
        ? '保存配置后将立即重启远程 Docker 服务，这会导致所有运行中的容器短暂中断。' 
        : '配置将保存并备份，但需要手动重启 Docker 服务后才能生效。'),
      h('p', { style: 'margin-top: 8px; color: #f0a020; font-weight: bold;' }, '注意：此操作将修改远程主机的 /etc/docker/daemon.json 文件。')
    ]),
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      loading.value.daemon = true
      try {
        const res = await axios.post(`/api/docker/${props.hostId}/daemon-config/raw`, {
          content: rawJsonContent.value,
          restart: daemonForm.value.shouldRestart
        })
        message.success(res.data.message)
        showRawModal.value = false
        fetchDaemonConfig()
      } catch (e: any) {
        message.error(e.response?.data?.detail || '保存失败')
      } finally {
        loading.value.daemon = false
      }
    }
  })
}

const handleSaveDaemonConfig = async () => {
  if (!props.hostId) return
  const newConfig = { ...rawDaemonConfig.value }
  newConfig['registry-mirrors'] = daemonForm.value.mirrors.split('\n').map(i => i.trim()).filter(i => i)
  newConfig['insecure-registries'] = daemonForm.value.insecure.split('\n').map(i => i.trim()).filter(i => i)
  newConfig['log-driver'] = 'json-file'
  newConfig['log-opts'] = {
    'max-size': daemonForm.value.logSize,
    'max-file': daemonForm.value.logFiles.toString()
  }
  newConfig['live-restore'] = daemonForm.value.liveRestore
  
  if (daemonForm.value.proxyEnabled && daemonForm.value.proxyHost) {
    let auth = ''
    if (daemonForm.value.proxyUser) {
      auth = `${encodeURIComponent(daemonForm.value.proxyUser)}:${encodeURIComponent(daemonForm.value.proxyPass)}@`
    }
    const port = daemonForm.value.proxyPort ? `:${daemonForm.value.proxyPort}` : ''
    const host = daemonForm.value.proxyHost.includes('://') ? daemonForm.value.proxyHost.split('://')[1] : daemonForm.value.proxyHost
    const proxyUrl = `http://${auth}${host}${port}`
    newConfig['proxies'] = {
      'http-proxy': proxyUrl,
      'https-proxy': proxyUrl,
      'no-proxy': daemonForm.value.noProxy
    }
  } else {
    delete newConfig['proxies']
  }

  dialog.warning({
    title: '确认保存并应用',
    content: () => h('div', null, [
      h('p', null, daemonForm.value.shouldRestart 
        ? '保存配置后将立即重启远程 Docker 服务，这会导致所有运行中的容器短暂中断。' 
        : '配置将保存并备份，但需要手动重启 Docker 服务后才能生效。'),
      h('p', { style: 'margin-top: 8px; color: #f0a020; font-weight: bold;' }, '注意：此操作将修改远程主机的 /etc/docker/daemon.json 文件。')
    ]),
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      loading.value.daemon = true
      try {
        const res = await axios.post(`/api/docker/${props.hostId}/daemon-config`, {
          config: newConfig,
          restart: daemonForm.value.shouldRestart
        })
        message.success(res.data.message)
        if (daemonForm.value.shouldRestart && res.data.restart_result) {
          resultOutput.value = res.data.restart_result.stdout || res.data.restart_result.stderr || '服务已尝试重启'
          showResult.value = true
        }
        fetchDaemonConfig()
      } catch (e) {
        message.error(e.response?.data?.detail || '保存失败')
      } finally {
        loading.value.daemon = false
      }
    }
  })
}

const handlePruneImages = async () => {
  if (!props.hostId) return
  if (!imageOptions.value.dangling && !imageOptions.value.all) {
    message.warning('请至少选择一个清理选项')
    return
  }

  dialog.warning({
    title: '确认清理镜像',
    content: '此操作将永久删除满足条件的本地镜像。',
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: async () => {
      loading.value.images = true
      try {
        const res = await axios.post(`/api/docker/${props.hostId}/prune-images`, {
          dangling: imageOptions.value.dangling,
          all_unused: imageOptions.value.all
        })
        resultOutput.value = res.data.stdout || '清理完成。'
        showResult.value = true
        message.success('镜像清理成功')
      } catch (e) { message.error('清理失败') }
      finally { loading.value.images = false }
    }
  })
}

const handlePruneCache = async () => {
  if (!props.hostId) return
  dialog.warning({
    title: '确认清理构建缓存',
    content: '此操作将清理所有未使用的构建缓存。',
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: async () => {
      loading.value.cache = true
      try {
        const res = await axios.post(`/api/docker/${props.hostId}/prune-cache`)
        resultOutput.value = res.data.stdout || '清理完成。'
        showResult.value = true
        message.success('缓存清理成功')
      } catch (e) { message.error('清理失败') }
      finally { loading.value.cache = false }
    }
  })
}
</script>