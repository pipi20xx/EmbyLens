<script setup lang="ts">
import { h } from 'vue'
import { NIcon } from 'naive-ui'
import { LinkOutlined as LinkIcon } from '@vicons/material'
import { SiteNav } from '../useSiteNav'

const props = defineProps<{
  site: SiteNav
  styleMode: string
  isDragging: boolean
}>()

const emit = defineEmits(['click', 'contextmenu', 'dragstart', 'dragenter', 'dragend'])

const isEmoji = (str: string) => {
  if (!str) return false
  if (str.includes('/') || str.includes('.')) return false
  return /\p{Emoji}/u.test(str) && str.length <= 4
}
</script>

<template>
  <div 
    class="site-card" 
    :class="[
      `style-${styleMode || 'glass'}`,
      { 'is-dragging': isDragging }
    ]"
    draggable="true"
    @dragstart="emit('dragstart')"
    @dragover.prevent
    @dragenter="emit('dragenter')"
    @dragend="emit('dragend')"
    @click="emit('click')"
    @contextmenu="emit('contextmenu', $event)"
  >
    <div class="site-icon-wrapper">
      <span v-if="isEmoji(site.icon)" class="emoji-icon">{{ site.icon }}</span>
      <img v-else-if="site.icon" :src="site.icon" class="image-icon" />
      <n-icon v-else size="20" :component="LinkIcon" />
    </div>
    <div class="site-info">
      <div class="site-name">{{ site.title }}</div>
      <div class="site-desc" v-if="site.description">{{ site.description }}</div>
    </div>
  </div>
</template>

<style scoped>
.site-card {
  display: flex; align-items: center; padding: 10px 14px;
  height: 64px; 
  width: 100%;
  max-width: 280px; 
  border-radius: 12px; cursor: pointer; 
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  box-sizing: border-box;
  overflow: hidden;
  position: relative;
}

/* --- 1. 玻璃风格 (Glass) --- */
.site-card.style-glass {
  background: var(--nav-card-bg);
  backdrop-filter: blur(var(--nav-card-blur));
  border: 1px solid var(--nav-card-border);
  box-shadow: 0 4px 10px -2px rgba(0, 0, 0, 0.1);
}
.site-card.style-glass:hover {
  border-color: var(--primary-color);
  transform: translateY(-6px);
  background: rgba(255, 255, 255, 0.2);
}

/* --- 2. 水玻璃风格 (Liquid) --- */
@keyframes water-ripple {
  0% { transform: translate(-50%, -50%) scale(0); opacity: 0.6; border: 2px solid rgba(255, 255, 255, 0.8); }
  100% { transform: translate(-50%, -50%) scale(2.5); opacity: 0; border: 1px solid rgba(255, 255, 255, 0); }
}

.site-card.style-liquid {
  background: rgba(255, 255, 255, 0.01);
  backdrop-filter: none !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-top: 1.5px solid rgba(255, 255, 255, 0.5);
  border-left: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px -12px rgba(0, 0, 0, 0.2);
}

.site-card.style-liquid::after {
  content: ''; position: absolute; top: 50%; left: 50%; width: 100px; height: 100px;
  border-radius: 50%; pointer-events: none; z-index: 0; transform: translate(-50%, -50%) scale(0);
}

.site-card.style-liquid:hover {
  background: rgba(255, 255, 255, 0.03);
  transform: translateY(-8px) scale(1.03);
  box-shadow: 0 15px 45px -10px rgba(0, 0, 0, 0.3), inset 0 0 15px rgba(255, 255, 255, 0.1);
}

.site-card.style-liquid:hover::after {
  animation: water-ripple 1s cubic-bezier(0, 0.2, 0.8, 1) infinite;
}

/* 额外反光层 */
.site-card.style-liquid .site-info::before {
  content: ''; position: absolute; top: -50%; left: -150%; width: 200%; height: 200%;
  background: linear-gradient(115deg, transparent 0%, rgba(255, 255, 255, 0.05) 30%, rgba(255, 255, 255, 0.2) 45%, rgba(255, 255, 255, 0.05) 60%, transparent 100%);
  transition: all 0.6s ease; pointer-events: none; z-index: -1;
}
.site-card.style-liquid:hover .site-info::before { left: 100%; }

/* --- 3. 极简风格 (Pure) --- */
.site-card.style-pure {
  background: transparent;
  backdrop-filter: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: none;
}
.site-card.style-pure:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-4px);
}

/* --- 通用内部样式 --- */
.site-card.is-dragging { opacity: 0.1; transform: scale(0.9); }

.site-icon-wrapper {
  width: 44px; height: 44px; display: flex; align-items: center; justify-content: center;
  background: rgba(255, 255, 255, 0.12); margin-right: 14px; flex-shrink: 0;
  border-radius: 12px; overflow: hidden; transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2); z-index: 1;
}
.site-card:hover .site-icon-wrapper { transform: scale(1.1) rotate(5deg); background: rgba(255, 255, 255, 0.2); }
.image-icon { width: 100%; height: 100%; object-fit: cover; }
.emoji-icon { font-size: 28px; line-height: 1; }

.site-info { flex: 1; min-width: 0; text-align: left; display: flex; flex-direction: column; justify-content: center; z-index: 1; position: relative; }
.site-name { font-size: 14px; font-weight: 600; color: var(--nav-text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px; transition: color 0.3s; }
.site-card:hover .site-name { color: var(--primary-color); }
.site-desc { font-size: 11px; color: var(--nav-text-desc-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; opacity: 0.7; transition: opacity 0.3s; }
.site-card:hover .site-desc { opacity: 1; }
</style>