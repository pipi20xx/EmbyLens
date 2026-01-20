<template>
  <div class="lab-report-card" v-if="subject">
    <div class="report-header">
      <n-icon color="#bb86fc" size="18" style="margin-right: 8px"><TagIcon /></n-icon>
      <span class="report-title">元数据探针 (Infobox & Tags)</span>
    </div>

    <!-- 1. Infobox -->
    <div class="report-row">
      <div class="row-label"><n-icon size="14"><InfoIcon /></n-icon> 1. 信息框 (Infobox)</div>
      <div class="row-content">
        <n-grid :cols="2" :x-gap="12">
          <n-gi v-for="(info, index) in infobox" :key="index">
            <div class="data-tag" style="display: block; width: 100%">
              <n-text depth="3">{{ info.key }}: </n-text>
              <n-text>{{ info.value }}</n-text>
            </div>
          </n-gi>
        </n-grid>
      </div>
    </div>

    <!-- 2. Meta Tags -->
    <div class="report-row">
      <div class="row-label" style="color: #bb86fc"><n-icon size="14"><TagIcon /></n-icon> 2. 系统标签 (Meta Tags)</div>
      <div class="row-content">
        <span v-for="(tag, idx) in metaTags" :key="idx" class="data-tag tag-purple">
          {{ tag }}
        </span>
        <n-text v-if="!metaTags?.length" depth="3">暂无系统标签</n-text>
      </div>
    </div>

    <!-- 3. User Tags -->
    <div class="report-row">
      <div class="row-label"><n-icon size="14"><TagIcon /></n-icon> 3. 用户标签 (User Tags)</div>
      <div class="row-content">
        <span v-for="tag in subject.tags" :key="tag.name" class="data-tag">
          {{ tag.name }} <n-text depth="3">({{ tag.count }})</n-text>
        </span>
      </div>
    </div>

    <!-- 4. Title Pool -->
    <div class="report-row">
      <div class="row-label"><n-icon size="14"><ListIcon /></n-icon> 4. 全量标题池 ({{ titlePool.length }})</div>
      <div class="row-content" style="margin-top: 6px">
        <span v-for="t in titlePool" :key="t" class="data-tag">{{ t }}</span>
      </div>
    </div>

    <!-- 5. Alias Pool -->
    <div class="report-row">
      <div class="row-label" style="color: #f0a020"><n-icon size="14"><TagIcon /></n-icon> 5. 全量别名池 ({{ aliasPool.length }})</div>
      <div class="row-content" style="margin-top: 6px">
        <div v-if="aliasPool.length > 0">
          <span v-for="a in aliasPool" :key="a" class="data-tag tag-orange">{{ a }}</span>
        </div>
        <div v-else class="pool-box" style="color: rgba(255,255,255,0.2)">暂无别名信息</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NIcon, NText, NGrid, NGi } from 'naive-ui'
import { LocalOfferOutlined as TagIcon, InfoOutlined as InfoIcon, ListOutlined as ListIcon } from '@vicons/material'

defineProps<{ 
  subject: any, 
  infobox: any[], 
  metaTags: string[],
  titlePool: string[], 
  aliasPool: string[] 
}>()
</script>

<style scoped>
.lab-report-card {
  margin-top: 24px;
  background: var(--modal-bg-color) !important;
  border: 1px solid var(--primary-border-color) !important;
  border-radius: 8px;
  overflow: hidden;
}
.report-header {
  background: linear-gradient(90deg, var(--primary-border-color) 0%, transparent 100%);
  padding: 10px 16px; border-bottom: 1px solid var(--primary-border-color);
  display: flex; align-items: center;
}
.report-title { font-family: 'Fira Code', monospace; font-weight: 800; color: var(--primary-color); letter-spacing: 1px; }
.report-row { padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.report-row:last-child { border-bottom: none; }
.row-label { font-size: 12px; color: var(--primary-color); opacity: 0.8; margin-bottom: 6px; display: flex; align-items: center; gap: 6px; }
.data-tag {
  font-family: 'Fira Code', monospace; background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color); padding: 2px 8px; border-radius: 4px;
  font-size: 13px; color: var(--text-color); display: inline-block; margin: 0 6px 6px 0;
}
.tag-orange { color: #f0a020; border-color: rgba(240, 160, 32, 0.3); }
.tag-purple { color: #bb86fc; border-color: rgba(187, 134, 252, 0.3); }
.pool-box {
  background: rgba(0, 0, 0, 0.3); border: 1px solid var(--border-color);
  padding: 12px; border-radius: 6px; font-family: 'Fira Code', monospace;
  font-size: 13px; line-height: 1.6; color: var(--text-color); opacity: 0.9; word-break: break-all;
}
</style>
