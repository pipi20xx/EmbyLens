<template>
  <n-card size="small" v-if="subject">
    <template #header>
      <n-space align="center">
        <n-text strong style="font-size: 18px">{{ subject.name_cn || subject.name }}</n-text>
        <n-tag size="small" type="primary" round>{{ subject.date || '未知日期' }}</n-tag>
        <n-tag size="small" type="info">{{ typeName }}</n-tag>
      </n-space>
    </template>

    <div class="subject-info-box">
      <n-grid :cols="24" :x-gap="16">
        <n-gi :span="6">
          <n-image
            width="100%"
            lazy
            :src="subject.images?.large"
            fallback-src="https://bgm.tv/img/no_icon_subject.png"
            border-radius="8"
          />
        </n-gi>
        <n-gi :span="18">
          <n-descriptions label-placement="left" :column="1" size="small" bordered label-style="width: 100px">
            <n-descriptions-item label="原始名称">{{ subject.name }}</n-descriptions-item>
            <n-descriptions-item label="中文名称">{{ subject.name_cn || 'N/A' }}</n-descriptions-item>
            <n-descriptions-item label="Bangumi ID">{{ subject.id }}</n-descriptions-item>
            <n-descriptions-item label="评分">
              <n-text type="warning" strong>{{ subject.rating?.score || '0.0' }}</n-text>
              <n-text depth="3" style="margin-left: 8px">({{ subject.rating?.total || 0 }} 人评价)</n-text>
            </n-descriptions-item>
          </n-descriptions>
        </n-gi>
      </n-grid>
    </div>

    <div class="overview-box" style="margin-top: 16px">
      <n-p depth="3" style="white-space: pre-wrap;">{{ subject.summary || '暂无简介' }}</n-p>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NSpace, NText, NTag, NGrid, NGi, NImage, NDescriptions, NDescriptionsItem, NP } from 'naive-ui'

const props = defineProps<{ subject: any }>()

const typeName = computed(() => {
  const types: Record<number, string> = { 1: '书籍', 2: '动画', 3: '音乐', 4: '游戏', 6: '三次元' }
  return types[props.subject.type] || '未知'
})
</script>

<style scoped>
.subject-info-box { background: rgba(0, 0, 0, 0.1); padding: 12px; border-radius: 8px; }
.overview-box {
  background: rgba(255, 255, 255, 0.03);
  padding: 12px;
  border-left: 4px solid var(--primary-color);
  border-radius: 4px;
}
</style>
