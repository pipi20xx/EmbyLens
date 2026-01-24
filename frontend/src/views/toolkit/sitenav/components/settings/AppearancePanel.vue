<script setup lang="ts">
import { 
  NSpace, NButton, NIcon, NText, NUpload, NSlider, NSelect, NCard, NColorPicker, NDivider, NGrid, NGridItem, NInput, NRadioGroup, NRadioButton, NSwitch
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
    content_max_width: number
    page_title: string
    page_subtitle: string
    wallpaper_mode: string
    bing_mkt: string
    bing_index: number
    bing_resolution: string
    show_wallpaper_info: boolean
    show_hitokoto: boolean
    show_clock: boolean
    header_alignment: string
    category_alignment: string
    header_item_spacing: number
    header_margin_top: number
    header_margin_bottom: number
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
          <n-text depth="3" style="font-size: 13px;">背景资源</n-text>
        </template>
        <n-space vertical size="medium">
          <n-radio-group 
            :value="settings.wallpaper_mode" 
            @update:value="val => emit('updateSettings', { wallpaper_mode: val })"
          >
            <n-radio-button value="custom">自定义上传</n-radio-button>
            <n-radio-button value="bing">必应每日壁纸</n-radio-button>
          </n-radio-group>

          <n-divider style="margin: 4px 0" />

          <div v-if="settings.wallpaper_mode === 'custom'">
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
                移除
              </n-button>
            </n-space>
          </div>
          <div v-else>
            <n-space vertical size="medium">
              <n-text depth="3" style="font-size: 12px;">
                已启用必应每日壁纸。您可以自定义地区和历史日期。
              </n-text>
              
              <div class="setting-item">
                <span class="label-small">壁纸地区 (Market)</span>
                <n-select 
                  :value="settings.bing_mkt" 
                  :options="[
                    { label: '中国 (zh-CN)', value: 'zh-CN' },
                    { label: '美国 (en-US)', value: 'en-US' },
                    { label: '日本 (ja-JP)', value: 'ja-JP' },
                    { label: '德国 (de-DE)', value: 'de-DE' },
                    { label: '英国 (en-GB)', value: 'en-GB' }
                  ]"
                  @update:value="val => emit('updateSettings', { bing_mkt: val })" 
                />
              </div>

              <div class="setting-item">
                <div class="label-row">
                  <span class="label-small">历史日期偏移</span>
                  <n-text depth="3" size="small">{{ settings.bing_index === 0 ? '今天' : settings.bing_index + ' 天前' }}</n-text>
                </div>
                <n-slider 
                  :value="settings.bing_index" 
                  :min="0" :max="7" :step="1" 
                  @update:value="val => emit('updateSettings', { bing_index: val })" 
                />
              </div>

              <div class="setting-item">
                <span class="label-small">分辨率质量</span>
                <n-radio-group 
                  :value="settings.bing_resolution" 
                  @update:value="val => emit('updateSettings', { bing_resolution: val })"
                >
                  <n-radio-button value="1920x1080">1080P</n-radio-button>
                  <n-radio-button value="UHD">4K UHD</n-radio-button>
                </n-radio-group>
              </div>

              <div class="setting-item">
                <n-space justify="space-between" align="center">
                  <span class="label-small" style="margin-bottom: 0">显示壁纸故事信息</span>
                  <n-switch 
                    :value="settings.show_wallpaper_info" 
                    @update:value="val => emit('updateSettings', { show_wallpaper_info: val })" 
                  />
                </n-space>
              </div>
            </n-space>
          </div>
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
        <div v-if="!settings.background_url" class="overlay-tip">
          请先上传背景图以解锁样式调整
        </div>
      </n-card>

      <!-- 内容文本 -->
      <n-card embedded :bordered="false" size="small">
        <template #header>
          <n-text depth="3" style="font-size: 13px;">内容组件</n-text>
        </template>
        <n-space vertical>
          <div class="setting-item">
            <n-space justify="space-between" align="center">
              <span class="label-small" style="margin-bottom: 0">显示数字时钟</span>
              <n-switch 
                :value="settings.show_clock" 
                @update:value="val => emit('updateSettings', { show_clock: val })" 
              />
            </n-space>
          </div>
          <div class="setting-item">
            <n-space justify="space-between" align="center">
              <span class="label-small" style="margin-bottom: 0">显示“每日一言”</span>
              <n-switch 
                :value="settings.show_hitokoto" 
                @update:value="val => emit('updateSettings', { show_hitokoto: val })" 
              />
            </n-space>
          </div>
          <div class="setting-item">
            <span class="label-small">主标题</span>
            <n-input 
              :value="settings.page_title" 
              placeholder="站点导航"
              @update:value="val => emit('updateSettings', { page_title: val })" 
            />
          </div>
          <div class="setting-item">
            <span class="label-small">副标题 (提示文字)</span>
            <n-input 
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 3 }"
              :value="settings.page_subtitle" 
              placeholder="提示文字..."
              @update:value="val => emit('updateSettings', { page_subtitle: val })" 
            />
          </div>
        </n-space>
      </n-card>

      <!-- 布局调整 -->
      <n-card embedded :bordered="false" size="small">
        <template #header>
          <n-text depth="3" style="font-size: 13px;">布局调整</n-text>
        </template>
        <n-space vertical size="large">
          <div class="setting-item">
            <span class="label-small">主标题对齐方式</span>
            <n-radio-group 
              :value="settings.header_alignment" 
              @update:value="val => emit('updateSettings', { header_alignment: val })"
            >
              <n-radio-button value="left">左对齐</n-radio-button>
              <n-radio-button value="center">居中对齐</n-radio-button>
              <n-radio-button value="right">右对齐</n-radio-button>
            </n-radio-group>
          </div>

          <div class="setting-item">
            <span class="label-small">分类标题对齐方式</span>
            <n-radio-group 
              :value="settings.category_alignment" 
              @update:value="val => emit('updateSettings', { category_alignment: val })"
            >
              <n-radio-button value="left">左对齐</n-radio-button>
              <n-radio-button value="center">居中对齐</n-radio-button>
              <n-radio-button value="right">右对齐</n-radio-button>
            </n-radio-group>
          </div>

          <div class="setting-item">
            <div class="label-row">
              <span class="label">页面内容宽度</span>
              <n-text depth="3" size="small">{{ settings.content_max_width }}%</n-text>
            </div>
            <n-slider 
              :value="settings.content_max_width" 
              :min="30" :max="100" :step="1" 
              @update:value="val => emit('updateSettings', { content_max_width: val })" 
            />
          </div>

          <n-divider style="margin: 4px 0" />

          <div class="setting-item">
            <div class="label-row">
              <span class="label">标题顶部边距 (MT)</span>
              <n-text depth="3" size="small">{{ settings.header_margin_top }}px</n-text>
            </div>
            <n-slider 
              :value="settings.header_margin_top" 
              :min="0" :max="200" :step="1" 
              @update:value="val => emit('updateSettings', { header_margin_top: val })" 
            />
          </div>

          <div class="setting-item">
            <div class="label-row">
              <span class="label">标题行间距</span>
              <n-text depth="3" size="small">{{ settings.header_item_spacing }}px</n-text>
            </div>
            <n-slider 
              :value="settings.header_item_spacing" 
              :min="0" :max="50" :step="1" 
              @update:value="val => emit('updateSettings', { header_item_spacing: val })" 
            />
          </div>

          <div class="setting-item">
            <div class="label-row">
              <span class="label">标题底部边距 (MB)</span>
              <n-text depth="3" size="small">{{ settings.header_margin_bottom }}px</n-text>
            </div>
            <n-slider 
              :value="settings.header_margin_bottom" 
              :min="0" :max="100" :step="1" 
              @update:value="val => emit('updateSettings', { header_margin_bottom: val })" 
            />
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