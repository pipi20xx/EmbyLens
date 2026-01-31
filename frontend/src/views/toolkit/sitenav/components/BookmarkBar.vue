<template>
  <div 
    class="bookmark-bar-wrapper" 
    :class="{ 'is-visible': isVisible || isHovered }"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
  >
    <!-- 触发区：鼠标靠近顶部时感知 -->
    <div class="trigger-area"></div>

    <div class="bookmark-bar-content glass-effect">
      <div class="flex items-center gap-1 px-4 h-full overflow-x-auto no-scrollbar">
        <!-- 书签项 -->
        <template v-for="item in bookmarks" :key="item.id">
          <!-- 文件夹 -->
          <n-dropdown
            v-if="item.type === 'folder'"
            :options="renderDropdownOptions(item.children || [])"
            @select="(key) => handleSelect(key)"
            trigger="hover"
          >
            <div class="bookmark-item group">
              <span class="i-mdi-folder text-yellow-500/80 text-lg"></span>
              <span class="text-sm">{{ item.title }}</span>
              <span class="i-mdi-chevron-down text-xs opacity-0 group-hover:opacity-50 transition-opacity"></span>
            </div>
          </n-dropdown>

          <!-- 单个书签 -->
          <div 
            v-else 
            class="bookmark-item"
            @click="openUrl(item.url)"
          >
            <img v-if="item.icon" :src="item.icon" class="w-4 h-4 object-contain" />
            <span v-else class="i-mdi-web text-gray-400"></span>
            <span class="text-sm truncate max-w-[120px]">{{ item.title }}</span>
          </div>
        </template>

        <!-- 管理入口 -->
        <div class="ml-auto flex items-center gap-2 pl-4 border-l border-white/10">
          <n-tooltip trigger="hover">
            <template #trigger>
              <button @click="router.push('/toolkit/bookmark-manager')" class="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors">
                <span class="i-mdi-bookmark-edit-outline text-lg"></span>
              </button>
            </template>
            管理书签
          </n-tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { NDropdown, NTooltip } from 'naive-ui'
import { useBookmark, type Bookmark } from '../useBookmark'

const router = useRouter()
const { bookmarks, fetchBookmarks } = useBookmark()

const isVisible = ref(false)
const isHovered = ref(false)

onMounted(() => {
  fetchBookmarks()
  window.addEventListener('mousemove', handleMouseMove)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove)
})

const handleMouseMove = (e: MouseEvent) => {
  // 靠近顶部 30px 时显示
  if (e.clientY < 30) {
    isVisible.value = true
  } else if (e.clientY > 60 && !isHovered.value) {
    isVisible.value = false
  }
}

const openUrl = (url?: string) => {
  if (url) window.open(url, '_blank')
}

const handleSelect = (url: string) => {
  window.open(url, '_blank')
}

const renderDropdownOptions = (items: Bookmark[]): any[] => {
  return items.map(item => ({
    label: item.title,
    key: item.url || item.id,
    disabled: item.type === 'folder' && (!item.children || item.children.length === 0),
    children: item.children ? renderDropdownOptions(item.children) : undefined,
    icon: () => item.type === 'folder' 
      ? h('span', { class: 'i-mdi-folder text-yellow-500' })
      : (item.icon ? h('img', { src: item.icon, class: 'w-4 h-4' }) : h('span', { class: 'i-mdi-web text-gray-400' }))
  }))
}
</script>

<style scoped>
.bookmark-bar-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 40px;
  z-index: 1000;
  transform: translateY(-100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none; /* 默认穿透 */
}

.bookmark-bar-wrapper.is-visible {
  transform: translateY(0);
  pointer-events: auto; /* 显示时可点击 */
}

.trigger-area {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  pointer-events: auto; /* 触发区必须可感应 */
}

.bookmark-bar-content {
  height: 100%;
  margin: 0 auto;
  width: 95%;
  max-width: 1400px;
  border-radius: 0 0 12px 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-top: none;
  background: rgba(30, 30, 34, 0.6);
}

.glass-effect {
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.bookmark-item {
  display: flex;
  items-center: center;
  gap: 6px;
  padding: 0 10px;
  height: 28px;
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
  color: rgba(255, 255, 255, 0.8);
  transition: all 0.2s;
}

.bookmark-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
