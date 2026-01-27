<template>
  <n-modal :show="show" @update:show="$emit('update:show', $event)" preset="card" :title="task.id ? '编辑备份任务' : '新增备份任务'" style="width: 650px">
    <n-form :model="task" label-placement="left" label-width="120">
      <!-- 远程任务特殊说明 -->
      <n-alert v-if="task.host_id && task.host_id !== 'local'" title="远程 SSH 备份模式" type="warning" :bordered="false" style="margin-bottom: 20px">
        <template #header-extra>
          <n-tag size="tiny" type="warning" quaternary>Host ID: {{ task.host_id }}</n-tag>
        </template>
        <ul style="margin: 0; padding-left: 18px; font-size: 12px; line-height: 1.6">
          <li><b>数据源：</b>该任务将从远程 Docker 主机拉取文件夹。</li>
          <li><b>依赖环境：</b>请确保远程主机已安装 <n-text code>tar</n-text> 或 <n-text code>7z</n-text> 命令。</li>
          <li><b>中转逻辑：</b>Lens 将通过网络执行远程打包并拉取回本地目的地。</li>
          <li><b>过滤规则：</b>已自动同步 Lens 的精准过滤逻辑，不符合规则的文件不会被打包传输。</li>
        </ul>
      </n-alert>

      <n-grid :cols="2" :x-gap="12">
        <n-form-item-gi :span="2" label="任务名称">
          <n-input v-model:value="task.name" placeholder="例如：数据库每日备份" />
        </n-form-item-gi>
        
        <n-form-item-gi label="备份模式">
          <n-space vertical :size="4" style="width: 100%">
            <n-select v-model:value="task.mode" :options="modeOptions" />
            <n-text depth="3" style="font-size: 12px; line-height: 1.4">
              <span v-if="task.mode === '7z'">🗜️ <b>7z 压缩</b>：最高压缩比，支持密码加密和文件名加密。适合节省空间的长期存档。</span>
              <span v-if="task.mode === 'tar'">📦 <b>Tar 打包</b>：Linux 原生打包格式，速度快，完美保持文件权限。适合快速迁移。</span>
              <span v-if="task.mode === 'sync'">🔄 <b>Sync 同步</b>：直接同步原始文件（不打包），无需解压即可直接查看，支持增量更新。</span>
            </n-text>
          </n-space>
        </n-form-item-gi>
        
        <n-form-item-gi label="存储介质">
          <n-space vertical :size="4" style="width: 100%">
            <n-select v-model:value="task.storage_type" :options="storageOptions" />
            <n-text depth="3" style="font-size: 12px; line-height: 1.4">
              <span v-if="task.storage_type === 'ssd'">🚀 <b>SSD 优化</b>：开启最大并发线程，充分利用闪存带宽。</span>
              <span v-if="task.storage_type === 'hdd'">🛡️ <b>HDD 保护</b>：限制并发线程（max=2），防止磁头剧烈抖动，保护硬盘寿命。</span>
              <span v-if="task.storage_type === 'cloud'">☁️ <b>云盘优化</b>：本地生成暂存盘后再流式上传，通过 --size-only 规避 API 频率限制。</span>
            </n-text>
          </n-space>
        </n-form-item-gi>

        <n-form-item-gi label="同步策略" v-if="task.mode === 'sync'">
          <n-space vertical :size="4" style="width: 100%">
            <n-select v-model:value="task.sync_strategy" :options="[
              { label: '镜像模式 (完全一致)', value: 'mirror' },
              { label: '增量模式 (只增不删)', value: 'incremental' }
            ]" />
            <n-text depth="3" style="font-size: 12px; line-height: 1.4">
              <span v-if="task.sync_strategy === 'mirror'">🔄 <b>镜像</b>：目标目录将与源目录完全同步，源端删除的文件，目标端也会被清理。</span>
              <span v-if="task.sync_strategy === 'incremental'">📥 <b>增量</b>：仅同步新增和修改，目标端已有的文件即使源端删了也会保留。</span>
            </n-text>
          </n-space>
        </n-form-item-gi>

        <n-form-item-gi :span="2" :label="task.host_id && task.host_id !== 'local' ? '源路径 (远程)' : '源路径'">
          <n-input-group>
            <n-input v-model:value="task.src_path" :placeholder="task.host_id && task.host_id !== 'local' ? '远程主机上的绝对路径' : '/app/data'" />
            <n-button v-if="!task.host_id || task.host_id === 'local'" @click="$emit('browse', 'src')">浏览</n-button>
          </n-input-group>
        </n-form-item-gi>
        
        <n-form-item-gi :span="2" label="目标目录">
          <n-input-group>
            <n-input v-model:value="task.dst_path" placeholder="/backup" />
            <n-button @click="$emit('browse', 'dst')">浏览</n-button>
          </n-input-group>
        </n-form-item-gi>

        <n-form-item-gi label="压缩强度" v-if="task.mode === '7z'">
          <n-slider v-model:value="task.compression_level" :min="1" :max="9" :step="1" />
          <n-text depth="3" style="margin-left: 12px">等级 {{ task.compression_level }}</n-text>
        </n-form-item-gi>

        <n-form-item-gi label="加密密码" v-if="task.mode === '7z'">
          <n-input v-model:value="task.password" type="password" show-password-on="click" placeholder="可选" />
        </n-form-item-gi>

        <n-form-item-gi :span="2">
          <n-divider title-placement="left">自动化运行计划</n-divider>
        </n-form-item-gi>

        <n-form-item-gi label="启用定时备份">
          <n-switch v-model:value="task.enabled" />
        </n-form-item-gi>

        <template v-if="task.enabled">
          <n-form-item-gi label="运行频率">
            <n-select v-model:value="simpleScheduleMode" :options="scheduleOptions" />
          </n-form-item-gi>

          <n-form-item-gi :span="2" label="执行时间" v-if="simpleScheduleMode === 'daily'">
            <n-time-picker v-model:formatted-value="dailyTime" format="HH:mm" />
            <n-text depth="3" style="margin-left: 12px">每天此时间点自动开始备份</n-text>
          </n-form-item-gi>

          <n-form-item-gi :span="2" label="间隔时间" v-if="simpleScheduleMode === 'interval'">
            <n-input-number v-model:value="intervalValue" :min="1" style="width: 120px" />
            <n-select v-model:value="intervalUnit" :options="unitOptions" style="width: 100px; margin-left: 8px" />
          </n-form-item-gi>

          <n-form-item-gi :span="2" label="Cron 表达式" v-if="simpleScheduleMode === 'cron'">
            <n-input v-model:value="task.schedule_value" placeholder="0 3 * * *" />
          </n-form-item-gi>
        </template>

        <n-form-item-gi :span="2" label="忽略模式">
          <n-space vertical :size="8" style="width: 100%">
            <n-space :size="4">
              <n-text depth="3" style="font-size: 12px; margin-right: 4px">常用预设:</n-text>
              <n-tag 
                v-for="p in presetPatterns" 
                :key="p" 
                size="small" 
                round 
                checkable 
                :checked="task.ignore_patterns.includes(p)"
                @update:checked="(val) => handleTogglePattern(p, val)"
                style="cursor: pointer"
              >
                {{ p }}
              </n-tag>
            </n-space>
            <n-dynamic-input v-model:value="task.ignore_patterns" placeholder="例如：*.log" />
          </n-space>
        </n-form-item-gi>
      </n-grid>
    </n-form>
    <template #footer>
      <n-space justify="end">
        <n-button @click="$emit('update:show', false)">取消</n-button>
        <n-button type="primary" @click="handleSave">保存</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { 
  NModal, NForm, NFormItemGi, NInput, NSelect, NInputGroup, NButton, NSlider, 
  NText, NDynamicInput, NSpace, NGrid, NDivider, NSwitch, NTimePicker, NInputNumber, NTag, NAlert 
} from 'naive-ui'

const props = defineProps<{
  show: boolean
  task: any
}>()

const emit = defineEmits(['update:show', 'save', 'browse'])

const simpleScheduleMode = ref('daily')
const dailyTime = ref('03:00')
const intervalValue = ref(1)
const intervalUnit = ref(60) // 默认小时 (60分钟)

const modeOptions = [
  { label: '7z 压缩', value: '7z' },
  { label: 'Tar.gz 打包', value: 'tar' },
  { label: '物理增量镜像 (Sync)', value: 'sync' }
]

const storageOptions = [
  { label: 'SSD (高性能)', value: 'ssd' },
  { label: 'HDD (机械硬盘)', value: 'hdd' },
  { label: '云盘 (CloudDrive/Rclone)', value: 'cloud' }
]

const scheduleOptions = [
  { label: '每天固定时间', value: 'daily' },
  { label: '固定间隔频率', value: 'interval' },
  { label: '自定义 Cron', value: 'cron' }
]

const unitOptions = [
  { label: '分钟', value: 1 },
  { label: '小时', value: 60 },
  { label: '天', value: 1440 }
]

const presetPatterns = [
  '__pycache__', '*.pyc', '.git', 'node_modules', 'target', 
  '.vscode', '.idea', 'dist', 'build', '*.log', '.DS_Store'
]

const handleTogglePattern = (pattern: string, checked: boolean) => {
  const patterns = [...props.task.ignore_patterns]
  if (checked) {
    if (!patterns.includes(pattern)) {
      patterns.push(pattern)
    }
  } else {
    const index = patterns.indexOf(pattern)
    if (index > -1) {
      patterns.splice(index, 1)
    }
  }
  props.task.ignore_patterns = patterns
}

// 监听任务数据变化，反向初始化简单模式
watch(() => props.show, (newVal) => {
  if (newVal) {
    if (props.task.schedule_type === 'cron') {
      const cron = props.task.schedule_value || ''
      const dailyMatch = cron.match(/^(\d+)\s+(\d+)\s+\*\s+\*\s+\*$/)
      if (dailyMatch) {
        simpleScheduleMode.value = 'daily'
        const m = dailyMatch[1].padStart(2, '0')
        const h = dailyMatch[2].padStart(2, '0')
        dailyTime.value = `${h}:${m}`
      } else {
        simpleScheduleMode.value = 'cron'
      }
    } else if (props.task.schedule_type === 'interval') {
      simpleScheduleMode.value = 'interval'
      const totalMin = parseInt(props.task.schedule_value) || 60
      if (totalMin % 1440 === 0) {
        intervalUnit.value = 1440
        intervalValue.value = totalMin / 1440
      } else if (totalMin % 60 === 0) {
        intervalUnit.value = 60
        intervalValue.value = totalMin / 60
      } else {
        intervalUnit.value = 1
        intervalValue.value = totalMin
      }
    }
  }
})

const handleSave = () => {
  if (simpleScheduleMode.value === 'daily') {
    const [h, m] = dailyTime.value.split(':').map(x => parseInt(x))
    props.task.schedule_type = 'cron'
    props.task.schedule_value = `${m} ${h} * * *`
  } else if (simpleScheduleMode.value === 'interval') {
    props.task.schedule_type = 'interval'
    props.task.schedule_value = String(intervalValue.value * intervalUnit.value)
  }
  emit('save')
}
</script>
