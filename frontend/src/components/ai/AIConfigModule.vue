<template>
  <div class="ai-config-module">
    <n-card title="AI 设置" :bordered="false" class="glass-card">
      <n-form label-placement="top">
        <n-form-item label="服务商 (Provider)">
          <n-select 
            v-model:value="config.provider" 
            :options="providerOptions" 
            @update:value="handleProviderChange"
          />
        </n-form-item>
        <n-form-item label="API Key" v-if="config.provider === 'openai'">
          <n-input type="password" v-model:value="config.api_key" placeholder="sk-..." show-password-on="click" />
        </n-form-item>
        <n-form-item label="Base URL">
          <n-input v-model:value="config.base_url" placeholder="https://api.openai.com/v1" />
        </n-form-item>
        <n-form-item label="Model Name">
          <n-input v-model:value="config.model" placeholder="gpt-3.5-turbo" />
        </n-form-item>
        <n-form-item>
          <n-button type="primary" @click="saveConfig" :loading="saving" block>保存配置</n-button>
        </n-form-item>
      </n-form>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { aiApi } from '@/api/ai'
import { useMessage } from 'naive-ui'
import { NCard, NForm, NFormItem, NInput, NButton, NSelect } from 'naive-ui'

const message = useMessage()
const config = ref({
  provider: 'openai',
  api_key: '',
  base_url: 'https://api.openai.com/v1',
  model: 'gpt-3.5-turbo'
})
const saving = ref(false)

const providerOptions = [
  { label: 'OpenAI (官方或代理)', value: 'openai' },
  { label: 'Ollama (本地部署)', value: 'ollama' }
]

const handleProviderChange = (val: string) => {
  if (val === 'ollama') {
    config.value.base_url = 'http://localhost:11434/v1'
    config.value.model = 'llama3'
    config.value.api_key = ''
  } else {
    config.value.base_url = 'https://api.openai.com/v1'
    config.value.model = 'gpt-3.5-turbo'
  }
}

const loadConfig = async () => {
  try {
    const res: any = await aiApi.getConfig()
    if (res) {
      config.value = { ...config.value, ...res }
    }
  } catch (e) {
    console.error(e)
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    await aiApi.saveConfig(config.value)
    message.success('配置已保存')
  } catch (e) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
}

/* Dark mode support */
:deep(.n-card) {
    background-color: var(--n-color);
}
</style>