<template>
  <div class="page-container">
    <n-grid :x-gap="16" :y-gap="16" cols="1 800:24" item-responsive>
      <n-gi span="24 800:8">
        <AIConfigModule />
        <div class="info-card">
          <n-card title="关于 AI 实验室" :bordered="false">
            <p>这是一个独立的 AI 功能演示模块。</p>
            <p>您可以在此配置 OpenAI 兼容的 API 服务，并在右侧进行对话测试。</p>
            <p>未来此模块的能力将被复用到系统的其他功能中。</p>
          </n-card>
        </div>
      </n-gi>
      <n-gi span="24 800:16">
        <AIChatModule />
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import AIConfigModule from '@/components/ai/AIConfigModule.vue'
import AIChatModule from '@/components/ai/AIChatModule.vue'
import { NGrid, NGi, NCard } from 'naive-ui'
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.info-card {
  margin-top: 16px;
}
</style>