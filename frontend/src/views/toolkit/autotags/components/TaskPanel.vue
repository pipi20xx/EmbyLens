<template>
  <n-card title="一键打标签任务" size="small" segmented>
    <template #header-extra>
      <n-text depth="3" style="font-size: 12px">此功能将遍历媒体库，应用预设规则或自定义标签</n-text>
    </template>
    
    <n-form label-placement="left" label-width="100" size="small">
      <n-grid :cols="2" :x-gap="24">
        <n-form-item-gi label="写入模式:">
          <n-radio-group v-model:value="form.mode">
            <n-space>
              <n-radio value="merge">合并现有标签</n-radio>
              <n-radio value="overwrite">覆盖所有标签</n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item-gi>
        <n-form-item-gi label="库类型:">
          <n-radio-group v-model:value="form.library_type">
            <n-space>
              <n-radio value="all">全库媒体</n-radio>
              <n-radio value="favorite">仅收藏项</n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item-gi>
      </n-grid>

      <n-form-item label="自定义标签:">
        <n-space vertical style="width: 100%">
          <n-checkbox v-model:checked="form.use_custom">使用固定标签内容 (不走自动匹配规则)</n-checkbox>
          <n-input 
            v-if="form.use_custom"
            v-model:value="form.custom_tags_text" 
            placeholder="请输入标签名，多个用英文逗号分隔" 
          />
        </n-space>
      </n-form-item>

      <div style="display: flex; justify-content: flex-end; margin-top: 8px">
        <n-button type="primary" @click="handleRun">🚀 开始任务</n-button>
      </div>
    </n-form>
  </n-card>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { NCard, NForm, NGrid, NFormItemGi, NRadioGroup, NRadio, NSpace, NCheckbox, NInput, NButton, NText, NFormItem, useDialog, useMessage } from 'naive-ui'

const props = defineProps<{ onRun: (options: any) => void }>()
const dialog = useDialog()
const message = useMessage()

const form = reactive({
  mode: 'merge',
  library_type: 'all',
  use_custom: false,
  custom_tags_text: ''
})

const handleRun = () => {
  dialog.info({
    title: '确认启动任务',
    content: '任务将在后台执行，每一项媒体都会调用 TMDB 进行精准元数据匹配。确认开始？',
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: () => {
      const customTags = form.use_custom 
        ? form.custom_tags_text.split(',').map(t => t.trim()).filter(t => t)
        : null
      
      props.onRun({
        mode: form.mode,
        library_type: form.library_type,
        custom_tags: customTags
      })
      message.success('后台任务已排队')
    }
  })
}
</script>
