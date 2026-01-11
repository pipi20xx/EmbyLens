<template>
  <div class="toolkit-container">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="info">元数据锁定管理 (1:1 源码复刻版)</n-text></n-h2>
        <n-text depth="3">严格区分 Emby 的“主锁 (LockData)”与“小锁 (LockedFields)”维度的操作逻辑。</n-text>
      </div>

      <!-- 1. 全局配置 -->
      <n-card title="通用执行参数" size="small" segmented>
        <n-form label-placement="left" label-width="120">
          <n-form-item label="目标媒体库">
            <n-select 
              v-model:value="common.lib_names" 
              multiple 
              filterable 
              :options="libOptions"
              placeholder="请选择要操作的媒体库" 
            />
          </n-form-item>
          <n-form-item label="执行模式">
            <n-switch v-model:value="common.dry_run">
              <template #checked>预览模式 (Dry Run)</template>
              <template #unchecked>实调模式 (Execute)</template>
            </n-switch>
          </n-form-item>
        </n-form>
      </n-card>

      <!-- 2. 操作类型选择 -->
      <n-card title="操作媒体类型选择" size="small">
        <n-checkbox-group v-model:value="selectedTypes">
          <n-space>
            <n-checkbox value="Movie">电影</n-checkbox>
            <n-checkbox value="Series">剧集 (Series)</n-checkbox>
            <n-checkbox value="Season">季 (Season)</n-checkbox>
            <n-checkbox value="Episode">集 (Episode)</n-checkbox>
          </n-space>
        </n-checkbox-group>
      </n-card>

      <!-- 3. 二重功能工具区 -->
      <n-grid :cols="3" :x-gap="12">
        <!-- 字段锁解除 -->
        <n-gi>
          <n-card title="元数据字段全解锁" size="small" status="error">
            <n-p depth="3" style="font-size: 12px">
              <b>[深度释放]</b><br/>
              逻辑：清空 LockedFields 列表 (小锁) <b>并</b> 设置 LockData = false (主锁)。
            </n-p>
            <n-button block type="error" ghost @click="handleAction('metadata_field_unlocker')" :loading="loading">
              字段全解锁
            </n-button>
          </n-card>
        </n-gi>

        <!-- 主锁开启 -->
        <n-gi>
          <n-card title="项目整体锁定" size="small" status="info">
            <n-p depth="3" style="font-size: 12px">
              <b>[主锁保护]</b><br/>
              逻辑：仅设置 LockData = true。保护整体元数据，但不修改各字段锁定状态。
            </n-p>
            <n-button block type="info" secondary @click="handleAction('item_locker')" :loading="loading">
              锁定主开关
            </n-button>
          </n-card>
        </n-gi>

        <!-- 全局彻底解锁 -->
        <n-gi>
          <n-card title="项目深度全解锁" size="small" status="success">
            <n-p depth="3" style="font-size: 12px">
              <b>[彻底释放]</b><br/>
              逻辑：主锁、小锁一起解除 (LockData=false + 列表清空)。
            </n-p>
            <n-button block type="success" secondary @click="handleAction('item_unlocker')" :loading="loading">
              全量彻底解锁
            </n-button>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 4. 调试：Payload 快照 -->
      <n-card title="调试：当前原子接口请求快照" embedded :bordered="false">
        <n-code :code="debugPayload" language="json" word-wrap />
      </n-card>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { 
  useMessage, NSpace, NH2, NText, NCard, NP, NButton, NGrid, NGi, 
  NCode, NCheckboxGroup, NCheckbox, NSwitch, NForm, NFormItem, NSelect, NDivider 
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const loading = ref(false)
const libOptions = ref([])
const selectedTypes = ref(['Movie', 'Series', 'Season', 'Episode'])
const lastAction = ref('metadata_field_unlocker')

const savedCommon = localStorage.getItem('embylens_lock_common')
const common = reactive(savedCommon ? JSON.parse(savedCommon) : {
  lib_names: [],
  dry_run: true
})

watch(common, (val) => {
  localStorage.setItem('embylens_lock_common', JSON.stringify(val))
}, { deep: true })

const fetchLibraries = async () => {
  try {
    const res = await axios.get('/api/server/libraries')
    libOptions.value = res.data
  } catch (e) {}
}

onMounted(fetchLibraries)

const debugPayload = computed(() => {
  return JSON.stringify({
    endpoint: `/api/toolkit/${lastAction.value}`,
    body: {
      ...common,
      item_types: selectedTypes.value
    }
  }, null, 2)
})

const handleAction = async (endpoint: string) => {
  lastAction.value = endpoint
  if (common.lib_names.length === 0) {
    message.warning('请选择媒体库')
    return
  }
  loading.value = true
  try {
    const res = await axios.post(`/api/toolkit/${endpoint}`, {
      ...common,
      item_types: selectedTypes.value
    })
    message.success(`任务完成: ${res.data.message} (处理数: ${res.data.processed_count})`)
  } catch (e) {
    message.error('接口请求失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>

.toolkit-container { 

  width: 100%; 

}

:deep(.n-h2 .n-text--info-type),

:deep(.n-h2 .n-text--primary-type) {

  color: var(--primary-color);

}

</style>
