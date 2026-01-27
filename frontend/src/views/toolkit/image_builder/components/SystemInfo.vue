<template>
  <div class="system-info">
    <n-space vertical size="large">
      <n-card size="small">
        <n-space align="center" justify="space-between">
          <n-space align="center">
            <n-text>选择监测主机:</n-text>
            <n-select v-model:value="selectedHostId" :options="hostOptions" style="width: 220px" @update:value="fetchInfo" />
          </n-space>
          <n-tag v-if="info.platforms.length > 0" type="success" size="large" round>
            <template #icon>
              <n-icon><CheckIcon /></n-icon>
            </template>
            多架构环境就绪
          </n-tag>
          <n-tag v-else-if="info.docker_version !== 'Unknown'" type="warning" size="large" round>
            基础 Docker 就绪
          </n-tag>
        </n-space>
      </n-card>

      <n-grid :cols="2" :x-gap="12" :y-gap="12">
        <n-gi :span="2">
          <n-card title="Docker 服务状态" size="small">
            <n-descriptions :column="2" label-placement="left" bordered>
              <n-descriptions-item label="Docker 版本">
                <n-space align="center">
                  <n-text strong>{{ info.docker_version }}</n-text>
                  <n-tag v-if="info.docker_version !== 'Unknown'" type="success" size="small">运行中</n-tag>
                </n-space>
              </n-descriptions-item>
              <n-descriptions-item label="Buildx 构建引擎">
                <n-space align="center">
                  <n-text strong>{{ info.buildx_version }}</n-text>
                  <n-tag v-if="info.buildx_version !== 'Not Found'" type="success" size="small">就绪</n-tag>
                </n-space>
              </n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-gi>
        <n-gi :span="2">
          <n-card title="多架构构建支持" size="small">
            <template #header-extra>
              <n-text v-if="info.platforms.length" type="success" depth="2">多架构环境已就绪</n-text>
            </template>
            <n-space v-if="info.platforms.length">
              <n-tag v-for="plat in info.platforms" :key="plat" type="info" size="small" ghost>
                {{ plat }}
              </n-tag>
            </n-space>
            <n-empty v-else description="未检测到多架构支持" />
          </n-card>
        </n-gi>
        <n-gi :span="2">
          <n-card title="Buildx 构建器列表 (Builders)" size="small">
            <div class="code-block">
              <pre v-if="info.builders && info.builders.length">{{ info.builders.join('\n') }}</pre>
              <n-empty v-else description="未发现活跃构建器" />
            </div>
          </n-card>
        </n-gi>
      </n-grid>
      <n-space justify="center" style="margin-top: 20px" size="large">
        <n-button @click="fetchInfo" :loading="loading" secondary type="primary">手动刷新环境状态</n-button>
        <n-button @click="handleRepair" :loading="fixing" type="warning" ghost>
          <template #icon>
            <n-icon><RepairIcon /></n-icon>
          </template>
          一键初始化/修复构建环境
        </n-button>
      </n-space>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NGrid, NGi, NCard, NDescriptions, NDescriptionsItem,
  NText, NSpace, NButton, NEmpty, NSelect, NTag, NIcon
} from 'naive-ui'
import {
  CheckCircleOutlined as CheckIcon,
  BuildCircleOutlined as RepairIcon
} from '@vicons/material'
import axios from 'axios'
import { useMessage, useDialog } from 'naive-ui'

const message = useMessage()
const dialog = useDialog()

const info = ref({
  docker_version: 'Unknown',
  buildx_version: 'Not Found',
  builders: [],
  platforms: []
})
const loading = ref(false)
const fixing = ref(false)
const selectedHostId = ref(null)
const hostOptions = ref([])

const fetchHosts = async () => {
  try {
    const res = await axios.get('/api/docker/hosts')
    hostOptions.value = res.data.map((h: any) => ({ label: h.name, value: h.id }))
    if (hostOptions.value.length > 0 && !selectedHostId.value) {
      selectedHostId.value = hostOptions.value[0].value
      fetchInfo()
    }
  } catch (e) {}
}

const fetchInfo = async () => {
  if (!selectedHostId.value) return
  loading.value = true
  try {
    const res = await axios.get('/api/image-builder/system-info', {
      params: { host_id: selectedHostId.value }
    })
    info.value = res.data
  } catch (e) {
    info.value = { docker_version: 'Unknown', buildx_version: 'Not Found', builders: [], platforms: [] }
  } finally {
    loading.value = false
  }
}

const handleRepair = () => {
  dialog.info({
    title: '初始化构建环境',
    content: '该操作将为远程主机安装 QEMU 仿真支持并配置专用 Buildx 构建器，以实现跨平台（如 ARM64）构建。是否继续？',
    positiveText: '立即开始',
    negativeText: '取消',
    onPositiveClick: async () => {
      fixing.value = true
      try {
        const res = await axios.post('/api/image-builder/setup-env', { host_id: selectedHostId.value })
        if (res.data.success) {
          message.success('构建环境初始化成功')
          fetchInfo()
        } else {
          message.error('修复失败: ' + res.data.message)
        }
      } catch (e) {
        message.error('请求失败')
      } finally {
        fixing.value = false
      }
    }
  })
}

onMounted(fetchHosts)
</script>

<style scoped>
.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
pre {
  margin: 0;
  white-space: pre-wrap;
}
</style>