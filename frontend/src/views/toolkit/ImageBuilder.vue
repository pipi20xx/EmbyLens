<template>
  <div class="image-builder">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">Docker 镜像构建与推送</n-text></n-h2>
        <n-text depth="3">模块化管理 Docker 镜像构建项目，支持多平台 (Buildx) 构建、自动推送至私有仓库及代理加速。</n-text>
      </div>

      <n-card size="small" segmented>
        <n-tabs v-model:value="activeTab" type="line" animated>
          <n-tab-pane name="projects" tab="项目管理">
            <project-list />
          </n-tab-pane>
          <n-tab-pane name="registries" tab="仓库与凭据">
            <registry-manager />
          </n-tab-pane>
          <n-tab-pane name="proxies" tab="代理设置">
            <proxy-manager />
          </n-tab-pane>
          <n-tab-pane name="system" tab="环境监测">
            <system-info />
          </n-tab-pane>
        </n-tabs>
      </n-card>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NSpace, NCard, NText, NH2, NTabs, NTabPane } from 'naive-ui'
import ProjectList from './image_builder/components/ProjectList.vue'
import RegistryManager from './image_builder/components/RegistryManager.vue'
import ProxyManager from './image_builder/components/ProxyManager.vue'
import SystemInfo from './image_builder/components/SystemInfo.vue'

const activeTab = ref('projects')
</script>

<style scoped>
.page-header {
  margin-bottom: 8px;
}
</style>
