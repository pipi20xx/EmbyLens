<template>
  <div class="search-panel">
    <n-form label-placement="top">
      <n-form-item label="名称 (Keywords)">
        <n-input 
          v-model:value="searchForm.keywords" 
          placeholder="输入动画名称..." 
          @keyup.enter="handleSearch" 
        />
      </n-form-item>
      <n-form-item label="类型">
        <n-select v-model:value="searchForm.type" :options="subjectTypeOptions" />
      </n-form-item>
      <n-button 
        block 
        type="primary" 
        secondary 
        :loading="loading" 
        @click="handleSearch"
      >
        搜索条目
      </n-button>
    </n-form>

    <div v-if="results.length > 0" class="search-results-list">
      <n-divider title-placement="left">搜索结果</n-divider>
      <n-list hoverable clickable size="small">
        <n-list-item v-for="item in results" :key="item.id" @click="$emit('select', item)">
          <n-thing 
            :title="item.name_cn || item.name" 
            :description="`ID: ${item.id} | ${item.air_date || '未知日期'}`" 
          />
        </n-list-item>
      </n-list>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NForm, NFormItem, NInput, NSelect, NButton, NDivider, NList, NListItem, NThing } from 'naive-ui'

defineProps<{
  searchForm: any
  results: any[]
  loading: boolean
}>()

const emit = defineEmits(['search', 'select'])

const subjectTypeOptions = [
  { label: '书籍 (Book)', value: 1 },
  { label: '动画 (Anime)', value: 2 },
  { label: '音乐 (Music)', value: 3 },
  { label: '游戏 (Game)', value: 4 },
  { label: '三次元 (Real)', value: 6 }
]

const handleSearch = () => {
  emit('search')
}
</script>

<script lang="ts">
export default {
  name: 'SearchPanel'
}
</script>

<style scoped>
.search-results-list {
  margin-top: 12px;
  max-height: 400px;
  overflow-y: auto;
}
</style>
