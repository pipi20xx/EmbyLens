<template>
  <n-modal
    :show="show"
    @update:show="$emit('update:show', $event)"
    preset="card"
    title="智能选中与排除规则配置"
    style="width: 600px"
    :bordered="false"
    size="huge"
  >
    <n-form label-placement="top">
      <n-tabs type="line" animated>
        <!-- 1. 评分权重标签页 -->
        <n-tab-pane name="rules" tab="评分权重">
          <n-alert type="info" size="small" style="margin-bottom: 16px">
            <div><strong style="margin-right: 4px">优先级逻辑：</strong>从上到下权重递减。同一行内，排在前面的关键词优先级更高。</div>
            <div style="margin-top: 4px; opacity: 0.8">所有输入项均不区分大小写（系统会自动处理）。</div>
          </n-alert>
          
          <n-form-item label="媒体规格 (DisplayTitle)">
            <template #label>
              <span>媒体规格 <span style="opacity: 0.6; font-weight: normal; font-size: 12px">(对应 DisplayTitle, 如: 4k, 1080p)</span></span>
            </template>
            <n-input v-model:value="form.display_title" placeholder="例如: 4k, 2160p, 1080p" />
          </n-form-item>
          
          <n-form-item label="视频编码 (Codec)">
            <template #label>
              <span>视频编码 <span style="opacity: 0.6; font-weight: normal; font-size: 12px">(对应 Codec, 如: hevc, h264)</span></span>
            </template>
            <n-input v-model:value="form.video_codec" placeholder="例如: hevc, h265, h264, av1" />
          </n-form-item>
          
          <n-form-item label="动态范围 (VideoRange)">
            <template #label>
              <span>动态范围 <span style="opacity: 0.6; font-weight: normal; font-size: 12px">(对应 VideoRange, 如: hdr, sdr)</span></span>
            </template>
            <n-input v-model:value="form.video_range" placeholder="例如: dolbyvision, hdr, sdr" />
          </n-form-item>
          
          <n-form-item label="平局决策 (当评分完全一致时)">
            <n-select
              v-model:value="localConfig.rules.tie_breaker"
              :options="[
                { label: '保留较小的 Emby ID (旧文件优先)', value: 'small_id' },
                { label: '保留较大的 Emby ID (新文件优先)', value: 'large_id' }
              ]"
            />
          </n-form-item>
        </n-tab-pane>
        
        <!-- 2. 白名单排除标签页 -->
        <n-tab-pane name="exclude" tab="白名单排除">
          <n-form-item label="白名单关键词 (路径包含即保留)">
            <n-input
              v-model:value="excludeText"
              type="textarea"
              placeholder="每行一个关键词或路径片段 (不区分大小写)&#10;只要完整路径中包含该词，文件就会被保护。&#10;&#10;例如：&#10;2023&#10;Feature&#10;/vol1/Anime/Protected"
              :autosize="{ minRows: 8, maxRows: 15 }"
            />
          </n-form-item>
        </n-tab-pane>
      </n-tabs>
    </n-form>

    <template #footer>
      <n-space justify="end">
        <n-button @click="$emit('update:show', false)">取消</n-button>
        <n-button type="primary" :loading="loading" @click="handleSave">保存并应用</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { NModal, NForm, NFormItem, NTabs, NTabPane, NAlert, NInput, NSelect, NSpace, NButton } from 'naive-ui'

const props = defineProps({
  show: Boolean,
  config: Object,
  loading: Boolean
})

const emit = defineEmits(['update:show', 'save'])

// 内部影子状态，防止直接修改父组件数据导致副作用
const localConfig = ref<any>(JSON.parse(JSON.stringify(props.config)))
const excludeText = ref('')
const form = reactive({
  display_title: '',
  video_codec: '',
  video_range: ''
})

// 监听弹窗打开，同步外部配置到内部表单
watch(() => props.show, (val) => {
  if (val) {
    localConfig.value = JSON.parse(JSON.stringify(props.config))
    // 数组转字符串显示
    excludeText.value = (localConfig.value.exclude_paths || []).join('\n')
    const vw = localConfig.value.rules?.values_weight || {}
    form.display_title = (vw.display_title || []).join(', ')
    form.video_codec = (vw.video_codec || []).join(', ')
    form.video_range = (vw.video_range || []).join(', ')
  }
})

const handleSave = () => {
  // 字符串转回数组
  const configToSave = JSON.parse(JSON.stringify(localConfig.value))
  configToSave.exclude_paths = excludeText.value.split('\n').map(s => s.trim()).filter(s => s)
  configToSave.rules.values_weight = {
    display_title: form.display_title.split(',').map(s => s.trim().toLowerCase()).filter(s => s),
    video_codec: form.video_codec.split(',').map(s => s.trim().toLowerCase()).filter(s => s),
    video_range: form.video_range.split(',').map(s => s.trim().toLowerCase()).filter(s => s)
  }
  
  emit('save', configToSave)
}
</script>
