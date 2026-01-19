<template>
  <div class="maintenance-panel">
    <n-grid :cols="2" :x-gap="12" :y-gap="12">
      <n-gi>
        <n-card title="镜像清理" size="small">
          <n-space vertical size="large">
            <n-text depth="3">清理无用的 Docker 镜像以释放磁盘空间。</n-text>
            <n-space item-style="display: flex; align-items: center">
              <n-checkbox v-model:checked="imageOptions.dangling">
                清理未标签镜像 (Dangling)
              </n-checkbox>
              <n-checkbox v-model:checked="imageOptions.all">
                清理所有未使用镜像 (Unused)
              </n-checkbox>
            </n-space>
            <n-button type="primary" secondary :loading="loading.images" @click="handlePruneImages">
              开始清理镜像
            </n-button>
          </n-space>
        </n-card>
      </n-gi>

      <n-gi>
        <n-card title="构建缓存清理" size="small">
          <n-space vertical size="large">
            <n-text depth="3">清理 Docker Buildx 或 BuildKit 的构建缓存。</n-text>
            <div style="height: 24px"></div> <!-- 保持高度对齐 -->
            <n-button type="warning" secondary :loading="loading.cache" @click="handlePruneCache">
              开始清理构建缓存
            </n-button>
          </n-space>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 结果弹窗 -->
    <n-modal v-model:show="showResult" preset="dialog" title="清理结果" style="width: 600px">
      <template #default>
        <div style="background: #1e1e1e; color: #adadad; padding: 10px; font-family: monospace; border-radius: 4px; overflow: auto; max-height: 400px; white-space: pre-wrap;">
          {{ resultOutput }}
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NGrid, NGi, NCard, NSpace, NText, NCheckbox, NButton, NModal, useMessage, useDialog } from 'naive-ui'
import axios from 'axios'

const props = defineProps<{
  hostId: string | null
}>()

const message = useMessage()
const dialog = useDialog()
const loading = ref({ images: false, cache: false })
const showResult = ref(false)
const resultOutput = ref('')

const imageOptions = ref({
  dangling: true,
  all: false
})

const handlePruneImages = () => {
  if (!props.hostId) return
  if (!imageOptions.value.dangling && !imageOptions.value.all) {
    message.warning('请至少选择一个清理选项')
    return
  }

  dialog.warning({
    title: '确认清理镜像',
    content: '此操作将永久删除满足条件的本地镜像。如果删除了正在使用的镜像（在 all 模式下），下次启动时需要重新下载。',
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: () => {
      // 立即触发异步逻辑而不返回 Promise，从而让弹窗立即关闭
      executeImagePrune()
    }
  })
}

const executeImagePrune = async () => {
  loading.value.images = true
  try {
    const res = await axios.post(`/api/docker/${props.hostId}/prune-images`, {
      dangling: imageOptions.value.dangling,
      all_unused: imageOptions.value.all
    })
    resultOutput.value = res.data.stdout || '清理完成，未释放额外空间。'
    showResult.value = true
    message.success('镜像清理任务已执行')
  } catch (e) {
    message.error('清理失败')
  } finally {
    loading.value.images = false
  }
}

const handlePruneCache = () => {
  if (!props.hostId) return
  dialog.warning({
    title: '确认清理构建缓存',
    content: '此操作将清理所有未使用的构建缓存，这可能会让下次镜像构建速度变慢。',
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: () => {
      executeCachePrune()
    }
  })
}

const executeCachePrune = async () => {
  loading.value.cache = true
  try {
    const res = await axios.post(`/api/docker/${props.hostId}/prune-cache`)
    resultOutput.value = res.data.stdout || '清理完成。'
    showResult.value = true
    message.success('缓存清理任务已执行')
  } catch (e) {
    message.error('清理失败')
  } finally {
    loading.value.cache = false
  }
}
</script>
