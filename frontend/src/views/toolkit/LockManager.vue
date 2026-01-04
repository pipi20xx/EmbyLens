<template>
  <div class="toolkit-container">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="info">元数据锁定管理 (1:1 源码复刻版)</n-text></n-h2>
        <n-text depth="3">严格遵循 emby-box 逻辑：区分元数据字段解锁与项目整体锁定/解锁。</n-text>
      </div>

      <!-- 1. 全局媒体类型选择 (所有工具共用) -->
      <n-card title="操作媒体类型选择" size="small" segmented>
        <n-checkbox-group v-model:value="selectedTypes">
          <n-space>
            <n-checkbox value="Movie">电影</n-checkbox>
            <n-checkbox value="Series">剧集 (Series)</n-checkbox>
            <n-checkbox value="Season">季 (Season)</n-checkbox>
            <n-checkbox value="Episode">集 (Episode)</n-checkbox>
          </n-space>
        </n-checkbox-group>
      </n-card>

      <!-- 2. 工具卡片区 -->
      <n-grid :cols="3" :x-gap="12">
        <!-- 原子工具 A -->
        <n-gi>
          <n-card title="元数据字段解锁" size="small" status="error">
            <n-p depth="3" style="font-size: 12px">
              <b>Metadata Field Unlocker</b><br/>
              清空 LockedFields 列表，并确保主锁解除。
            </n-p>
            <n-button block type="error" ghost @click="handleAction('metadata_field_unlocker')" :loading="loading">
              一键字段全解锁
            </n-button>
          </n-card>
        </n-gi>

        <!-- 原子工具 B -->
        <n-gi>
          <n-card title="项目整体锁定" size="small" status="info">
            <n-p depth="3" style="font-size: 12px">
              <b>Item Locker</b><br/>
              仅设置 LockData = true。保护所有元数据不被修改。
            </n-p>
            <n-button block type="info" secondary @click="handleAction('item_locker')" :loading="loading">
              执行项目锁定
            </n-button>
          </n-card>
        </n-gi>

        <!-- 原子工具 C -->
        <n-gi>
          <n-card title="项目整体解锁" size="small" status="success">
            <n-p depth="3" style="font-size: 12px">
              <b>Item Unlocker</b><br/>
              设置 LockData = false，并同步清空锁定字段列表。
            </n-p>
            <n-button block type="success" secondary @click="handleAction('item_unlocker')" :loading="loading">
              执行项目解锁
            </n-button>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 3. 调试控制台 (完全对齐原版 Payload) -->
      <n-card title="调试：原版接口请求快照" embedded :bordered="false">
        <template #header-extra>
          <n-switch v-model:value="dryRun" size="small">
            <template #checked>预览模式</template>
            <template #unchecked>实调模式</template>
          </n-switch>
        </template>
        <n-code :code="debugPayload" language="json" word-wrap />
      </n-card>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  useMessage, NSpace, NH2, NText, NCard, NP, NButton, NGrid, NGi, 
  NCode, NCheckboxGroup, NCheckbox, NSwitch 
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const loading = ref(false)
const selectedTypes = ref(['Movie', 'Series', 'Season', 'Episode'])
const dryRun = ref(true)
const lastAction = ref('metadata_field_unlocker')

const debugPayload = computed(() => {
  return JSON.stringify({
    endpoint: `/api/toolkit/${lastAction.value}`,
    request_body: {
      lib_names: ["电影", "剧集"], // 复刻原版必填参数
      dry_run: dryRun.value,
      item_types: selectedTypes.value
    }
  }, null, 2)
})

const handleAction = async (endpoint: string) => {
  lastAction.value = endpoint
  if (selectedTypes.value.length === 0) {
    message.warning('请选择媒体类型')
    return
  }
  loading.value = true
  try {
    const res = await axios.post(`/api/toolkit/${endpoint}`, {
      lib_names: ["电影", "剧集"],
      dry_run: dryRun.value,
      item_types: selectedTypes.value
    })
    message.success(`任务完成，处理条目: ${res.data.processed_count}`)
  } catch (e) {
    message.error('接口请求失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.toolkit-container { max-width: 1200px; margin: 0 auto; }
</style>