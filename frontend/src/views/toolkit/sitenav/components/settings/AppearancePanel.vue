<script setup lang="ts">
import { 
  NSpace, NButton, NIcon, NText, NUpload, NSlider, NSelect, NCard
} from 'naive-ui'
import { 
  ImageOutlined as ImageIcon
} from '@vicons/material'

const props = defineProps<{
  settings: {
    background_url: string
    background_opacity: number
    background_blur: number
    background_size: string
  }
}>()

const emit = defineEmits(['uploadBg', 'updateSettings'])

const sizeOptions = [
  { label: '全部填充 (Cover)', value: 'cover' },
  { label: '完整显示 (Contain)', value: 'contain' },
  { label: '强制拉伸 (Stretch)', value: '100% 100%' }
]

const handleUploadBg = (options: { file: { file: File } }) => {
  emit('uploadBg', options.file.file)
}
</script>

<template>
  <div class="tab-content">
    <n-space vertical size="large">
      <!-- 核心图片上传区 -->
      <n-card embedded :bordered="false" size="small">
        <template #header>
          <n-text depth="3" style="font-size: 13px;">底图资源</n-text>
        </template>
        <n-space align="center" justify="space-between">
          <n-upload :show-file-list="false" @change="handleUploadBg" accept=".png,.jpg,.jpeg,.webp,.svg,.gif">
            <n-button type="primary" secondary>
              <template #icon><n-icon><ImageIcon /></n-icon></template>
              {{ settings.background_url ? '更换背景图片' : '上传背景图片' }}
            </n-button>
          </n-upload>
          
          <n-button 
            v-if="settings.background_url"
            secondary 
            type="error" 
            quaternary 
            @click="emit('updateSettings', { background_url: '' })"
          >
            移除当前背景
          </n-button>
        </n-space>
      </n-card>

      <!-- 样式精调区 -->
      <n-card embedded :bordered="false" size="small" :disabled="!settings.background_url">
        <template #header>
          <n-text depth="3" style="font-size: 13px;">样式精调</n-text>
        </template>
        
        <n-space vertical size="large" :style="{ opacity: settings.background_url ? 1 : 0.4 }">
          <div class="setting-item">
            <div class="label-row">
              <span class="label">填充模式</span>
              <n-text depth="3" size="small">决定图片如何适配屏幕</n-text>
            </div>
            <n-select 
              :value="settings.background_size" 
              :options="sizeOptions" 
              :disabled="!settings.background_url"
              @update:value="val => emit('updateSettings', { background_size: val })" 
            />
          </div>

          <div class="setting-item">
            <div class="label-row">
              <span class="label">背景透明度</span>
              <n-text depth="3" size="small">{{ Math.round(settings.background_opacity * 100) }}%</n-text>
            </div>
            <n-slider 
              :value="settings.background_opacity" 
              :min="0" :max="1" :step="0.01" 
              :disabled="!settings.background_url"
              @update:value="val => emit('updateSettings', { background_opacity: val })" 
            />
          </div>

          <div class="setting-item">
            <div class="label-row">
              <span class="label">背景模糊度</span>
              <n-text depth="3" size="small">{{ settings.background_blur }}px</n-text>
            </div>
            <n-slider 
              :value="settings.background_blur" 
              :min="0" :max="20" :step="1" 
              :disabled="!settings.background_url"
              @update:value="val => emit('updateSettings', { background_blur: val })" 
            />
          </div>
        </n-space>
        
        <div v-if="!settings.background_url" class="overlay-tip">
          请先上传背景图以解锁样式调整
        </div>
      </n-card>
    </n-space>
  </div>
</template>

<style scoped>
.tab-content { padding: 8px 0; min-height: 350px; }
.setting-item { margin-bottom: 20px; }
.label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.label { font-size: 14px; font-weight: 500; }
.overlay-tip {
  text-align: center;
  padding: 10px;
  color: var(--primary-color);
  font-size: 12px;
  background: rgba(var(--primary-color-rgb), 0.1);
  border-radius: 4px;
  margin-top: 10px;
}
</style>