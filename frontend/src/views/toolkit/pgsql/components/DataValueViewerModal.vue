<template>
  <n-modal
    :show="show"
    preset="card"
    :title="displayTitle"
    style="width: 80%; max-width: 1000px"
    content-style="padding: 0;"
    @update:show="$emit('update:show', $event)"
  >
    <div class="viewer-container">
      <div class="viewer-content">
        <pre>{{ formattedContent }}</pre>
      </div>
    </div>
    <template #footer>
      <n-space justify="end">
        <n-button @click="copyToClipboard">复制内容</n-button>
        <n-button type="primary" @click="$emit('update:show', false)">关闭</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NModal, NSpace, NButton, useMessage } from 'naive-ui'

const props = defineProps<{
  show: boolean
  title: string
  value: any
}>()

const emit = defineEmits(['update:show'])
const message = useMessage()

const displayTitle = computed(() => `查看: ${props.title}`)

const formattedContent = computed(() => {
  const val = props.value
  if (val === null) return 'NULL'
  
  if (typeof val === 'object') {
    return JSON.stringify(val, null, 2)
  }
  
  if (typeof val === 'string') {
    try {
      // 尝试解析并美化 JSON 字符串
      if ((val.startsWith('{') && val.endsWith('}')) || (val.startsWith('[') && val.endsWith(']'))) {
        return JSON.stringify(JSON.parse(val), null, 2)
      }
    } catch (e) {
      // 解析失败则按原样显示
    }
    return val
  }
  
  return String(val)
})

const copyToClipboard = () => {
  navigator.clipboard.writeText(formattedContent.value)
  message.success('已复制到剪贴板')
}
</script>

<style scoped>
.viewer-container {
  padding: 16px;
  background-color: #1a1a1a;
  max-height: 70vh;
  overflow: auto;
}

.viewer-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  color: #adbac7;
  font-family: v-mono, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 13px;
  line-height: 1.5;
}
</style>