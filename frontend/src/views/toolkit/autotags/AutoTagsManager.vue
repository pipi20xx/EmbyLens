<template>
  <div class="autotag-container">
    <n-space vertical size="large">
      <n-card embedded :bordered="false">
        <n-page-header title="自动标签助手" subtitle="基于规则全自动维护 Emby 媒体标签。支持实时 Webhook 联动自动化。">
          <template #extra>
            <n-button type="primary" quaternary @click="handleSync">
              <template #icon><n-icon><SyncIcon /></n-icon></template>
              同步 Emby 媒体
            </n-button>
          </template>
        </n-page-header>
      </n-card>

      <!-- 1. Webhook 自动化配置面板 -->
      <n-card title="Webhook 实时自动化" size="small" segmented>
        <template #header-extra>
          <n-switch v-model:value="whConfig.enabled" @update:value="saveWH" />
        </template>
        
        <n-form label-placement="left" label-width="100" size="small">
          <n-form-item label="Webhook URL:">
            <n-input-group>
              <n-input :value="webhookUrl" disabled />
              <n-button type="primary" ghost @click="copyUrl">复制</n-button>
            </n-input-group>
          </n-form-item>

          <n-alert title="Emby Webhook 配置指南" type="info" :bordered="false" style="margin-bottom: 16px">
            请在 Emby 后台添加此 URL，并确保：
            <br />1. <b>请求内容类型</b>：选择 <b>application/json</b>
            <br />2. <b>勾选事件</b>：必须勾选 <b>“已添加新媒体”</b> (library.new)
          </n-alert>

          <n-grid :cols="3" :x-gap="12">
            <n-form-item-gi label="安全密钥:">
              <n-input v-model:value="whConfig.secret_token" @blur="saveWH" placeholder="自定义 Token" />
            </n-form-item-gi>
            <n-form-item-gi label="写入模式:">
              <n-select v-model:value="whConfig.write_mode" :options="[
                { label: '合并现有标签', value: 'merge' },
                { label: '覆盖所有标签', value: 'overwrite' }
              ]" @update:value="saveWH" />
            </n-form-item-gi>
            <n-form-item-gi label="处理延迟(秒):">
              <n-input-number v-model:value="whConfig.delay_seconds" @blur="saveWH" :min="0" :max="3600" />
            </n-form-item-gi>
          </n-grid>
          <n-form-item label="自动化状态:">
            <n-checkbox v-model:checked="whConfig.automation_enabled" @update:checked="saveWH">
              接收到 item.added 事件时自动执行规则比对
            </n-checkbox>
          </n-form-item>
        </n-form>
      </n-card>

      <!-- 2. 任务控制 -->
      <TaskPanel :onRun="startTask" />

      <!-- 3. 辅助维护 -->
      <MaintenancePanel :onClearAll="clearAll" :onClearSpecific="clearSpecific" :onTestWrite="testWrite" />

      <!-- 4. 规则配置 -->
      <div class="section-header">
        <n-space align="center">
          <n-h3 style="margin: 0">打标签规则配置</n-h3>
          <n-text depth="3">按住手柄 ⠿ 拖拽调整顺序</n-text>
        </n-space>
        <n-button type="primary" ghost @click="prepareNewRule">
          <template #icon><n-icon><AddIcon /></n-icon></template>
          添加新规则
        </n-button>
      </div>

      <div class="rules-grid" @dragover.prevent @drop="onDrop">
        <div v-for="(rule, index) in rules" :key="index" class="rule-item-wrapper" @dragenter="onDragEnter(index)">
          <RuleCard :rule="rule" :index="index" @edit="openEditor(index)" @delete="handleDeleteRule(index)" @drag-start="onDragStart" />
        </div>
        <div v-if="!rules.length" class="empty-rules"><n-empty description="尚未配置任何规则" /></div>
      </div>
    </n-space>

    <RuleEditorModal v-model:show="showEditor" :rule="editingRule" :is-new="isNew" @confirm="onRuleSave" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { NCard, NSpace, NButton, NPageHeader, NEmpty, NH3, NText, NIcon, useMessage, NForm, NFormItem, NInput, NInputGroup, NGrid, NFormItemGi, NSwitch, NInputNumber, NCheckbox, NSelect, NAlert } from 'naive-ui'
import { SyncOutlined as SyncIcon, AddOutlined as AddIcon } from '@vicons/material'
import axios from 'axios'
import { copyText } from '../../../utils/clipboard'

import TaskPanel from './components/TaskPanel.vue'
import RuleCard from './components/RuleCard.vue'
import RuleEditorModal from './components/RuleEditorModal.vue'
import MaintenancePanel from './components/MaintenancePanel.vue'
import { useAutoTags } from './useAutoTags'

const message = useMessage()
const { rules, fetchRules, saveRules, startTask, testWrite, clearAll, clearSpecific } = useAutoTags()

const showEditor = ref(false)
const isNew = ref(false)
const editingIndex = ref(-1)
const editingRule = ref<any>({})
const draggedIndex = ref<number | null>(null)

const whConfig = reactive({
  enabled: true,
  secret_token: '',
  automation_enabled: true,
  delay_seconds: 10,
  write_mode: 'merge'
})

const webhookUrl = computed(() => {
  const base = window.location.origin
  return `${base}/api/autotags/webhook/${whConfig.secret_token}`
})

onMounted(async () => {
  fetchRules()
  const res = await axios.get('/api/autotags/webhook-config')
  Object.assign(whConfig, res.data)
})

const saveWH = async () => {
  await axios.post('/api/autotags/webhook-config', whConfig)
  message.success('Webhook 配置已更新')
}

const copyUrl = async () => {
  if (await copyText(webhookUrl.value)) {
    message.success('URL 已成功复制到剪贴板')
  } else {
    message.error('复制失败，请手动选取')
  }
}

const onDragStart = (index: number) => { draggedIndex.value = index }
const onDragEnter = (index: number) => {
  if (draggedIndex.value === null || draggedIndex.value === index) return
  const newRules = [...rules.value]; const item = newRules.splice(draggedIndex.value, 1)[0]
  newRules.splice(index, 0, item); rules.value = newRules; draggedIndex.value = index
}
const onDrop = async () => { draggedIndex.value = null; await saveRules(rules.value) }

const prepareNewRule = () => {
  isNew.value = true
  editingRule.value = { name: '', tag: '', item_type: 'all', match_all_conditions: false, is_negative_match: false, conditions: { countries: [], genres: [], years_text: '' } }
  showEditor.value = true
}
const openEditor = (index: number) => { isNew.value = false; editingIndex.value = index; editingRule.value = JSON.parse(JSON.stringify(rules.value[index])); showEditor.value = true }
const onRuleSave = async (rule: any) => {
  const newRules = [...rules.value]
  if (isNew.value) newRules.push(rule); else newRules[editingIndex.value] = rule
  if (await saveRules(newRules)) showEditor.value = false
}
const handleDeleteRule = async (index: number) => { const newRules = [...rules.value]; newRules.splice(index, 1); await saveRules(newRules) }
const handleSync = async () => { message.info('同步指令已下发'); await axios.post('/api/dedupe/sync') }
</script>

<style scoped>

.autotag-container { 

  width: 100%;

}

.section-header { 

  display: flex; 

  justify-content: space-between; 

  align-items: center; 

  margin: 24px 0 12px 0; 

}

.rules-grid { 

  display: grid; 

  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); 

  gap: 12px; 

  min-height: 100px; 

}

.empty-rules { 

  grid-column: 1 / -1; 

  padding: 40px; 

  background: rgba(255,255,255,0.02); 

  border-radius: 8px; 

  border: 1px dashed var(--border-color);

}

</style>
