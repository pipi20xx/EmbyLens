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
            评分项目越靠前优先级越高。值按优先级从高到低排列，英文逗号分隔。
          </n-alert>
          
          <n-form-item label="媒体规格 (如: 4k, 2160p, 1080p, 720p)">
            <n-input v-model:value="form.display_title" placeholder="例如: 4k, 2160p, 1080p" />
          </n-form-item>
          
          <n-form-item label="视频编码 (如: hevc, h265, h264, av1)">
            <n-input v-model:value="form.video_codec" placeholder="例如: hevc, h265, h264" />
          </n-form-item>
          
          <n-form-item label="动态范围 (如: dolbyvision, hdr, sdr)">
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
          <n-form-item label="绝对不会被选中的路径前缀">
            <n-input
              v-model:value="excludeText"
              type="textarea"
              placeholder="每行一个路径，例如：/vol1/Anime/Protected"
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
