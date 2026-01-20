<template>
  <div v-if="episodes" style="margin-top: 24px">
    <n-divider title-placement="left">
      <n-space align="center">
        <n-text type="primary" strong>章节列表 (Episodes)</n-text>
        <n-tag size="tiny" round>{{ episodes.total }}</n-tag>
      </n-space>
    </n-divider>
    <n-scrollbar style="max-height: 500px">
      <n-list size="small" hoverable>
        <n-list-item v-for="ep in episodes.data" :key="ep.id">
          <n-thing>
            <template #header>
              <n-space align="center">
                <n-tag size="small" :type="getEpTypeTag(ep.type)" quaternary>
                  {{ getEpTypeName(ep.type) }}{{ ep.sort }}
                </n-tag>
                <n-text strong>{{ ep.name_cn || ep.name }}</n-text>
              </n-space>
            </template>
            <template #header-extra>
               <n-text depth="3" style="font-size: 12px">{{ ep.airdate }}</n-text>
            </template>
            <template #description>
              <div v-if="ep.name_cn && ep.name !== ep.name_cn" style="font-size: 12px; color: #888">{{ ep.name }}</div>
              <n-p v-if="ep.desc" depth="3" style="font-size: 12px; margin-top: 4px; line-height: 1.4">{{ ep.desc }}</n-p>
            </template>
          </n-thing>
        </n-list-item>
      </n-list>
    </n-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { NDivider, NSpace, NText, NTag, NScrollbar, NList, NListItem, NThing, NP } from 'naive-ui'

defineProps<{ episodes: any }>()

const getEpTypeName = (type: number) => {
  const types: Record<number, string> = { 0: '本篇', 1: '特别篇', 2: 'OP', 3: 'ED', 4: '预告', 5: 'MAD', 6: '其他' }
  return types[type] || ''
}

const getEpTypeTag = (type: number) => {
  if (type === 0) return 'primary'
  if (type === 1) return 'info'
  return 'default'
}
</script>
