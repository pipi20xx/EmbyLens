<template>
  <div v-if="characters?.length" style="margin-top: 24px">
    <n-divider title-placement="left">
      <n-space align="center">
        <n-text type="primary" strong>角色列表 (Characters)</n-text>
        <n-tag size="tiny" round>{{ characters.length }}</n-tag>
      </n-space>
    </n-divider>
    <n-scrollbar x-scrollable>
      <n-space :size="12" style="padding-bottom: 8px">
        <n-card v-for="char in characters" :key="char.id" size="small" style="width: 140px; flex-shrink: 0" content-style="padding: 8px">
          <n-space vertical align="center" :size="4">
            <n-image
              width="80"
              height="80"
              style="border-radius: 50%"
              lazy
              :src="char.images?.grid || char.images?.small"
              fallback-src="https://bgm.tv/img/info_only_m.png"
              object-fit="cover"
            />
            <n-text strong style="font-size: 12px; text-align: center" class="line-clamp-1">{{ char.name }}</n-text>
            <n-tag size="tiny" :type="char.relation === '主角' ? 'primary' : 'default'">{{ char.relation }}</n-tag>
          </n-space>
        </n-card>
      </n-space>
    </n-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { NDivider, NSpace, NText, NTag, NScrollbar, NCard, NImage } from 'naive-ui'
defineProps<{ characters: any[] }>()
</script>
