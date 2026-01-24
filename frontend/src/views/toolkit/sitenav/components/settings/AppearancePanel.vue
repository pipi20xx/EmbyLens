<script setup lang="ts">
import { 
  NSpace, NButton, NIcon, NText, NUpload, NSlider, NSelect, NCard, NColorPicker, NDivider, NGrid, NGridItem
} from 'naive-ui'
import { 
  ImageOutlined as ImageIcon,
  PaletteOutlined as PaletteIcon
} from '@vicons/material'

const props = defineProps<{
  settings: {
    background_url: string
    background_opacity: number
    background_blur: number
    background_size: string
    background_color: string
    card_background: string
    card_blur: number
    card_border_color: string
    text_color: string
    text_description_color: string
    category_title_color: string
  }
}>()

const emit = defineEmits(['uploadBg', 'updateSettings', 'resetSettings'])

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
      <n-card embedded :bordered="false" size="small">
        <template #header>
          <n-text depth="3" style="font-size: 13px;">背景样式</n-text>
        </template>
        
        <n-space vertical size="large">
          <div class="setting-item">
            <div class="label-row">
              <span class="label">背景底色</span>
              <n-text depth="3" size="small">无图片或图片透明时显示的颜色</n-text>
            </div>
            <n-color-picker 
              :value="settings.background_color" 
              @update:value="val => emit('updateSettings', { background_color: val })" 
            />
          </div>

          <n-divider style="margin: 8px 0" />

          <div v-if="settings.background_url" style="margin-top: 8px;">
            <div class="setting-item">
              <div class="label-row">
                <span class="label">填充模式</span>
                <n-text depth="3" size="small">决定图片如何适配屏幕</n-text>
              </div>
              <n-select 
                :value="settings.background_size" 
                :options="sizeOptions" 
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
                @update:value="val => emit('updateSettings', { background_blur: val })" 
              />
            </div>
          </div>
        </n-space>
      </n-card>

      <!-- 卡片样式高级设置 -->
      <n-card embedded :bordered="false" size="small">
        <template #header>
          <n-text depth="3" style="font-size: 13px;">卡片高级样式</n-text>
        </template>

        <n-space vertical size="large">
          <n-grid :x-gap="12" :y-gap="12" :cols="2">
            <n-grid-item>
              <div class="setting-item">
                <span class="label-small">卡片背景色</span>
                <n-color-picker 
                  show-alpha
                  :value="settings.card_background" 
                  @update:value="val => emit('updateSettings', { card_background: val })" 
                />
              </div>
            </n-grid-item>
            <n-grid-item>
              <div class="setting-item">
                <span class="label-small">卡片边框色</span>
                <n-color-picker 
                  show-alpha
                  :value="settings.card_border_color" 
                  @update:value="val => emit('updateSettings', { card_border_color: val })" 
                />
              </div>
            </n-grid-item>
            <n-grid-item>
              <div class="setting-item">
                <span class="label-small">标题文字色</span>
                <n-color-picker 
                  :value="settings.text_color" 
                  @update:value="val => emit('updateSettings', { text_color: val })" 
                />
              </div>
            </n-grid-item>
            <n-grid-item>
              <div class="setting-item">
                <span class="label-small">描述文字色</span>
                <n-color-picker 
                  show-alpha
                  :value="settings.text_description_color" 
                  @update:value="val => emit('updateSettings', { text_description_color: val })" 
                />
              </div>
            </n-grid-item>
            <n-grid-item>
              <div class="setting-item">
                <span class="label-small">分类标题色</span>
                <n-color-picker 
                  :value="settings.category_title_color" 
                  @update:value="val => emit('updateSettings', { category_title_color: val })" 
                />
              </div>
            </n-grid-item>
          </n-grid>

          <div class="setting-item">
            <div class="label-row">
              <span class="label">卡片模糊度 (Glassmorphism)</span>
              <n-text depth="3" size="small">{{ settings.card_blur }}px</n-text>
            </div>
            <n-slider 
              :value="settings.card_blur" 
              :min="0" :max="30" :step="1" 
              @update:value="val => emit('updateSettings', { card_blur: val })" 
            />
          </div>

          <n-button block quaternary type="warning" @click="emit('resetSettings')">
            恢复默认样式
          </n-button>
        </n-space>
      </n-card>
    </n-space>
  </div>
</template>

<style scoped>
.tab-content { padding: 8px 0; }
.setting-item { margin-bottom: 12px; }
.label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.label { font-size: 14px; font-weight: 500; }
.label-small { font-size: 12px; margin-bottom: 4px; display: block; color: rgba(255,255,255,0.7); }
</style>

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