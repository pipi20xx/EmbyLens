<template>
  <svg :width="size" :height="size" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient :id="gradId" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" :style="{ 'stop-color': colorStart, 'stop-opacity': 1 }" />
        <stop offset="100%" :style="{ 'stop-color': colorEnd, 'stop-opacity': 1 }" />
      </linearGradient>
    </defs>
    <circle cx="100" cy="100" r="85" fill="none" :stroke="`url(#${gradId})`" stroke-width="18" />
    <circle cx="100" cy="100" r="55" fill="none" :stroke="`url(#${gradId})`" stroke-width="8" stroke-dasharray="20 10" opacity="0.6" />
    <circle cx="100" cy="100" r="25" :fill="`url(#${gradId})`" />
    <path d="M60 60 A60 60 0 0 1 140 60" fill="none" stroke="white" stroke-width="10" stroke-linecap="round" opacity="0.4" />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue';
const props = withDefaults(defineProps<{
  size?: number | string
  theme?: 'purple' | 'modern'
}>(), { size: 24, theme: 'purple' })

const gradId = computed(() => `logo_grad_${props.theme}`)
const colorStart = computed(() => props.theme === 'purple' ? '#705df2' : '#5946d1')
const colorEnd = computed(() => props.theme === 'purple' ? '#bb86fc' : '#705df2')
</script>
