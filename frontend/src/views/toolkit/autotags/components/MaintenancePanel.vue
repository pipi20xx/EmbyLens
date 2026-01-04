<template>
  <n-card title="辅助维护工具" size="small">
    <n-space vertical>
      <n-space>
        <n-button size="small" secondary type="warning" @click="handleSpecific">清除指定标签</n-button>
        <n-button size="small" secondary type="error" @click="handleClearAll">清空所有标签</n-button>
      </n-space>
      <n-divider />
      <n-text depth="3" style="font-size: 12px">写入测试 (手动验证权限与解锁逻辑)</n-text>
      <n-input-group>
        <n-input v-model:value="testId" size="small" placeholder="Emby ID" style="width: 120px" />
        <n-input v-model:value="testTag" size="small" placeholder="标签名" />
        <n-button size="small" type="primary" ghost @click="handleTest">测试</n-button>
      </n-input-group>
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
import { ref, h } from 'vue'
import { NCard, NSpace, NButton, NDivider, NText, NInputGroup, NInput, useDialog, useMessage } from 'naive-ui'

const props = defineProps<{
  onClearAll: () => void
  onClearSpecific: (tags: string[]) => void
  onTestWrite: (id: string, tag: string) => Promise<boolean>
}>()

const dialog = useDialog()
const message = useMessage()
const testId = ref('')
const testTag = ref('测试')

const handleClearAll = () => {
  dialog.error({
    title: '危险：清空所有标签',
    content: '此操作将永久移除库中所有电影/剧集的标签。确认执行？',
    positiveText: '清空',
    onPositiveClick: () => props.onClearAll()
  })
}

const handleSpecific = () => {
  let val = ''
  dialog.warning({
    title: '移除特定标签',
    content: () => h(NInput, {
      placeholder: '多个标签用逗号隔开',
      onUpdateValue: (v) => val = v
    }),
    positiveText: '移除',
    onPositiveClick: () => {
      const tags = val.split(',').map(t => t.trim()).filter(t => t)
      if (tags.length) props.onClearSpecific(tags)
    }
  })
}

const handleTest = async () => {
  if (!testId.value) return message.warning('请输入 ID')
  const ok = await props.onTestWrite(testId.value, testTag.value)
  if (ok) message.success('写入指令已发送')
}
</script>
