<script setup lang="ts">
const props = withDefaults(defineProps<{
  size?: number | string
}>(), { size: 24 })
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="logo-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color: var(--primary-color); stop-opacity: 1" />
        <stop offset="100%" style="stop-color: var(--primary-hover); stop-opacity: 1" />
      </linearGradient>
    </defs>
    <circle cx="100" cy="100" r="85" fill="none" stroke="url(#logo-gradient)" stroke-width="18" />
    <circle cx="100" cy="100" r="55" fill="none" stroke="url(#logo-gradient)" stroke-width="8" stroke-dasharray="20 10" opacity="0.6" />
    <circle cx="100" cy="100" r="25" fill="url(#logo-gradient)" />
    <path d="M60 60 A60 60 0 0 1 140 60" fill="none" stroke="white" stroke-width="10" stroke-linecap="round" opacity="0.4" />
  </svg>
</template>
