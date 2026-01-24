<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  NModal, NInput, NSelect, NGrid, NGridItem, 
  NScrollbar, NSpin, NEmpty, NButton, NSpace, NTooltip
} from 'naive-ui'
import { SearchOutlined as SearchIcon } from '@vicons/material'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits(['update:show', 'select'])

const loading = ref(false)
const searchText = ref('')
const selectedStyle = ref('border-radius')
const iconData = ref<any[]>([])

const styles = [
  { label: 'Border Radius (圆角)', value: 'border-radius' },
  { label: 'Circle (圆形)', value: 'circle' },
  { label: 'SVG (矢量)', value: 'svg' }
]

const fetchIcons = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/toolkit/navigation/hd-icons')
    const data = await response.json()
    iconData.value = data.icons || []
  } catch (error) {
    console.error('Failed to fetch HD-Icons:', error)
  } finally {
    loading.value = false
  }
}

const filteredIcons = computed(() => {
  // 先按风格过滤
  const styleMatch = iconData.value.filter(item => item.url.includes(`/${selectedStyle.value}/`))
  
  if (!searchText.value) return styleMatch
  const kw = searchText.value.toLowerCase()
  return styleMatch.filter(item => item.name.toLowerCase().includes(kw))
})

const handleSelect = (url: string) => {
  emit('select', url)
  emit('update:show', false)
}

onMounted(() => {
  fetchIcons()
})

const onStyleChange = () => {
  searchText.value = ''
}
</script>

<template>
  <n-modal 
    :show="show" 
    @update:show="val => emit('update:show', val)" 
    preset="card" 
    title="HD-Icons 图标库" 
    style="width: 800px; max-height: 90vh;"
  >
    <n-space vertical size="large">
      <n-space justify="space-between">
        <n-space>
          <n-select 
            v-model:value="selectedStyle" 
            :options="styles" 
            style="width: 200px" 
            @update:value="onStyleChange"
          />
          <n-input 
            v-model:value="searchText" 
            placeholder="搜索图标名称 (英文)..." 
            style="width: 300px"
            clearable
          >
            <template #prefix><n-icon><SearchIcon /></n-icon></template>
          </n-input>
        </n-space>
        <div class="count-tag">已加载 {{ iconData.length }} 个图标</div>
      </n-space>

      <n-spin :show="loading">
        <div class="icon-grid-container">
          <n-scrollbar style="max-height: 60vh">
            <n-empty v-if="!loading && filteredIcons.length === 0" description="未找到匹配图标" />
            <n-grid :cols="6" :x-gap="12" :y-gap="12">
              <n-grid-item v-for="item in filteredIcons" :key="item.url">
                <div class="icon-card" @click="handleSelect(item.url)">
                  <div class="icon-img-box">
                    <img :src="item.url" loading="lazy" />
                  </div>
                  <div class="icon-name">{{ item.name }}</div>
                </div>
              </n-grid-item>
            </n-grid>
          </n-scrollbar>
        </div>
      </n-spin>
    </n-space>

    <template #footer>
      <div class="footer-tip">图标数据来自 GitHub: xushier/HD-Icons</div>
    </template>
  </n-modal>
</template>

<style scoped>
.count-tag {
  line-height: 34px;
  color: rgba(255,255,255,0.4);
  font-size: 12px;
}
.icon-grid-container {
  min-height: 300px;
  padding: 4px;
}
.icon-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.icon-card:hover {
  background: rgba(255,255,255,0.15);
  border-color: var(--primary-color);
  transform: translateY(-2px);
}
.icon-img-box {
  width: 48px;
  height: 48px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-img-box img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.icon-name {
  font-size: 11px;
  text-align: center;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: rgba(255,255,255,0.7);
}
.footer-tip {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  text-align: right;
}
</style>