<script setup lang="ts">
import { ref, onMounted, computed, nextTick, h, watch } from 'vue'
import { 
  NSpace, NIcon, NEmpty, NGrid, NGridItem, NButton, 
  NDropdown, NTooltip, NModal
} from 'naive-ui'
import {
  LinkOutlined as LinkIcon,
  LaunchOutlined as LaunchIcon,
  AddCircleOutlineOutlined as AddIcon,
  SettingsOutlined as SettingsIcon,
  EditOutlined as EditIcon,
  DeleteOutlined as DeleteIcon,
  MenuOpenOutlined as MenuOpenIcon,
  MenuOutlined as MenuIcon,
  BookmarkBorderOutlined as BookmarkIcon
} from '@vicons/material'
import { useSiteNav, SiteNav } from './useSiteNav'
import { isHomeEntry } from '@/store/navigationStore'
import { useRouter } from 'vue-router'

// 导入积木组件
import SiteEditorModal from './components/SiteEditorModal.vue'
import CategoryManagerModal from './components/CategoryManagerModal.vue'
import NavClock from './components/NavClock.vue'
import SiteCard from './components/SiteCard.vue'
import BookmarkManager from '../BookmarkManager.vue'

const { 
  sites, categories, navSettings, loading, fetchSites, fetchCategories, fetchSettings,  addSite, updateSite, deleteSite, updateSiteOrder,
  addCategory, deleteCategory, updateCategory, updateCategoryOrder,
  updateNavSettings, resetNavSettings, uploadBackground, fetchIconFromUrl, 
  exportConfig, importConfig, message, hitokoto, fetchHitokoto,
  bingInfo, fetchBingWallpaper, wallpaperSeed, wallpaperLoading, resolvedWallpaperUrl, refreshWallpaper, saveCurrentWallpaper
} = useSiteNav()

onMounted(() => {
  fetchSites()
  fetchCategories()
  fetchSettings()
  fetchHitokoto()
})

// 原始随机 API 地址计算
const baseRandomApiUrl = computed(() => {
  const mode = navSettings.value.wallpaper_mode
  const type = navSettings.value.wallpaper_type || 'scenery'
  const res = navSettings.value.wallpaper_resolution || '1920x1080'
  let [width, height] = res.split('x')
  if (res === 'UHD' || res === '3840x2160') { width = '3840'; height = '2160'; }
  if (res === '2K' || res === '2560x1440') { width = '2560'; height = '1440'; }

  if (mode === 'unsplash') {
    if (type === 'anime') return `https://www.loliapi.com/acg/pc/`
    if (type === 'scenery') return `https://picsum.photos/${width}/${height}?nature,landscape`
    if (type === 'minimalist') return `https://picsum.photos/${width}/${height}?minimalist,abstract`
    return `https://picsum.photos/${width}/${height}`
  }
  return ''
})

// 最终显示的背景图 URL
const computedBgUrl = computed(() => {
  const mode = navSettings.value.wallpaper_mode
  if (mode === 'bing') return bingInfo.value.url
  if (mode === 'unsplash') {
    // 优先使用已解析出的静态地址
    return resolvedWallpaperUrl.value || baseRandomApiUrl.value
  }
  return navSettings.value.background_url
})

// 监听配置变化，触发预解析
watch(() => [
  navSettings.value.wallpaper_mode, 
  navSettings.value.wallpaper_type, 
  navSettings.value.wallpaper_resolution,
  navSettings.value.wallpaper_keyword
], (newValues) => {
  const mode = newValues[0]
  if (mode === 'unsplash') {
    // 只有当模式切换到 unsplash，或者在 unsplash 模式下其它关键参数改变时才刷新
    nextTick(() => refreshWallpaper(baseRandomApiUrl.value))
  }
}, { immediate: true })
// --- 状态管理 ---
const showEditor = ref(false)
const showSettings = ref(false)
const showBookmarkManager = ref(false)
const fetchingIcon = ref(false)
const editingSite = ref<Partial<SiteNav> | null>(null)
const dragItem = ref<number | null>(null)

// 右键菜单
const showContextMenu = ref(false)
const xRef = ref(0)
const yRef = ref(0)
const rightClickedSite = ref<SiteNav | null>(null)

const contextMenuOptions = [
  { label: '编辑站点', key: 'edit', icon: () => h(NIcon, null, { default: () => h(EditIcon) }) },
  { label: '删除站点', key: 'delete', icon: () => h(NIcon, null, { default: () => h(DeleteIcon) }) },
]

// --- 核心拖拽排序逻辑 ---

const onDragStart = (id: number) => {
  dragItem.value = id
}

const onDragEnter = (targetId: number) => {
  if (dragItem.value === null || dragItem.value === targetId) return

  const fromIndex = sites.value.findIndex(s => s.id === dragItem.value)
  const toIndex = sites.value.findIndex(s => s.id === targetId)

  if (fromIndex !== -1 && toIndex !== -1) {
    const fromSite = sites.value[fromIndex]
    const toSite = sites.value[toIndex]
    
    if (fromSite.category_id !== toSite.category_id) {
      fromSite.category_id = toSite.category_id
      fromSite.category = toSite.category
    }

    const [item] = sites.value.splice(fromIndex, 1)
    sites.value.splice(toIndex, 0, item)
  }
}

const onDragEnd = async () => {
  if (dragItem.value === null) return
  await updateSiteOrder(sites.value.map(s => s.id))
  dragItem.value = null
}

// --- 其他交互 ---

const handleAddSite = (categoryId?: number) => {
  editingSite.value = {
    title: '', url: '', icon: '', description: '',
    category_id: categoryId || (categories.value.length > 0 ? categories.value[0].id : undefined),
    order: sites.value.length
  }
  showEditor.value = true
}

const handleContextMenu = (e: MouseEvent, site: SiteNav) => {
  e.preventDefault()
  showContextMenu.value = false
  nextTick(() => {
    rightClickedSite.value = site
    showContextMenu.value = true
    xRef.value = e.clientX
    yRef.value = e.clientY
  })
}

const handleContextMenuSelect = (key: string) => {
  showContextMenu.value = false
  if (!rightClickedSite.value) return
  if (key === 'edit') {
    editingSite.value = { ...rightClickedSite.value }
    showEditor.value = true
  } else if (key === 'delete') {
    deleteSite(rightClickedSite.value.id)
  }
}

const handleSaveSite = async () => {
  if (!editingSite.value) return
  let success = editingSite.value.id 
    ? await updateSite(editingSite.value.id, editingSite.value)
    : await addSite(editingSite.value)
  if (success) showEditor.value = false
}

const handleAutoFetchIcon = async () => {
  if (!editingSite.value?.url) return
  fetchingIcon.value = true
  const icon = await fetchIconFromUrl(editingSite.value.url)
  if (icon) editingSite.value.icon = icon
  fetchingIcon.value = false
}

const groupedSites = computed(() => {
  const result: { id: number, name: string, sites: SiteNav[] }[] = []
  categories.value.forEach(cat => {
    result.push({ id: cat.id, name: cat.name, sites: [] })
  })
  sites.value.forEach(site => {
    const group = result.find(g => g.id === site.category_id)
    if (group) group.sites.push(site)
  })
  return result
})

const isEmoji = (str: string) => {
  if (!str) return false
  if (str.includes('/') || str.includes('.')) return false
  return /\p{Emoji}/u.test(str) && str.length <= 4
}

const getCategoryIcon = (categoryId: number) => {
  const cat = categories.value.find(c => c.id === categoryId)
  return cat?.icon || ''
}

const openUrl = (url: string) => window.open(url, '_blank')
</script>

<template>
  <div 
    class="site-nav-page"
    :style="{
      '--nav-card-bg': navSettings.card_background || 'rgba(255, 255, 255, 0.12)',
      '--nav-card-blur': `${navSettings.card_blur ?? 16}px`,
      '--nav-card-border': navSettings.card_border_color || 'rgba(255, 255, 255, 0.15)',
      '--nav-text-color': navSettings.text_color || '#ffffff',
      '--nav-text-desc-color': navSettings.text_description_color || 'rgba(255, 255, 255, 0.7)',
      '--nav-bg-color': navSettings.background_color || '#1e1e22',
      '--nav-category-color': navSettings.category_title_color || '#ffffff',
      '--nav-content-width': `${navSettings.content_max_width || 90}%`,
      '--nav-category-align': navSettings.category_alignment || 'left',
      '--nav-header-align': navSettings.header_alignment || 'left',
      '--nav-header-gap': `${navSettings.header_item_spacing ?? 12}px`,
      '--nav-header-mt': `${navSettings.header_margin_top ?? 20}px`,
      '--nav-header-mb': `${navSettings.header_margin_bottom ?? 30}px`
    }"
  >
    <!-- 背景层：底层实色 -->
    <div class="site-nav-background-base"></div>
    
    <!-- 背景层：顶层图片（受透明度和模糊度影响） -->
    <transition name="fade-bg">
      <div 
        :key="computedBgUrl"
        v-if="computedBgUrl"
        class="site-nav-background-image"
        :style="{
          backgroundImage: `url('${computedBgUrl}')`,
          opacity: navSettings.background_opacity ?? 0.7,
          filter: `blur(${navSettings.background_blur ?? 0}px)`,
          backgroundSize: navSettings.background_size || 'cover'
        }"
      ></div>
    </transition>

    <!-- 背景遮罩层：防止壁纸太亮干扰视线 -->
    <div class="site-nav-overlay"></div>

    <!-- 每日一言底部对齐保护层 -->
    <div 
      v-if="navSettings.wallpaper_mode === 'bing' && navSettings.show_wallpaper_info && bingInfo.title" 
      class="wallpaper-info-layer"
    >
      <div class="wp-info-content">
        <div class="wp-title">{{ bingInfo.title }}</div>
        <div class="wp-copyright">{{ bingInfo.copyright }}</div>
      </div>
    </div>

    <!-- 内容包裹层 -->
    <div class="site-nav-content" style="max-width: var(--nav-content-width); margin: 0 auto; padding: 0 20px;">
      <div class="nav-header" :style="{ marginTop: 'var(--nav-header-mt)', marginBottom: 'var(--nav-header-mb)' }">
        <div class="header-left" :style="{ 
          textAlign: 'var(--nav-header-align)', 
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: navSettings.header_alignment === 'center' ? 'center' : (navSettings.header_alignment === 'right' ? 'flex-end' : 'flex-start'),
          gap: 'var(--nav-header-gap)'
        }">
          <!-- 时钟积木 -->
          <NavClock 
            v-if="navSettings.show_clock" 
            :alignment="navSettings.header_alignment" 
            :textColor="navSettings.text_color"
          />

          <div class="page-title">{{ navSettings.page_title }}</div>
          <div class="page-subtitle" style="margin-bottom: 0;">{{ navSettings.page_subtitle }}</div>
          
          <!-- 每日一言积木 -->
          <div v-if="navSettings.show_hitokoto" class="hitokoto-container" @click="fetchHitokoto" :style="{
             alignItems: navSettings.header_alignment === 'center' ? 'center' : (navSettings.header_alignment === 'right' ? 'flex-end' : 'flex-start'),
             marginTop: 0
          }">
            <span class="hitokoto-text">“ {{ hitokoto.text }} ”</span>
            <span class="hitokoto-from">—— {{ hitokoto.from }}</span>
          </div>
        </div>
        <div class="header-right" style="align-self: flex-start;">
          <n-space>
            <n-tooltip trigger="hover">
              <template #trigger>
                <n-button circle quaternary @click="isHomeEntry = !isHomeEntry">
                  <template #icon>
                    <n-icon>
                      <MenuOpenIcon v-if="isHomeEntry" />
                      <MenuIcon v-else />
                    </n-icon>
                  </template>
                </n-button>
              </template>
              {{ isHomeEntry ? '显示侧边导航' : '隐藏侧边导航' }}
            </n-tooltip>
            <n-tooltip trigger="hover">
              <template #trigger>
                <n-button circle quaternary @click="showBookmarkManager = true">
                  <template #icon><n-icon><BookmarkIcon /></n-icon></template>
                </n-button>
              </template>
              书签管理
            </n-tooltip>
            <n-button circle quaternary @click="showSettings = true">
              <template #icon><n-icon><SettingsIcon /></n-icon></template>
            </n-button>
          </n-space>
        </div>
      </div>

      <div v-if="sites.length === 0 && !loading" class="empty-state">
        <n-empty description="还没有站点">
          <template #extra>
            <n-button type="primary" @click="handleAddSite()">添加第一个站点</n-button>
          </template>
        </n-empty>
      </div>

      <div v-for="group in groupedSites" :key="group.id" class="category-section">
        <div class="category-header" :style="{ 
          justifyContent: navSettings.category_alignment === 'center' ? 'center' : (navSettings.category_alignment === 'right' ? 'flex-end' : 'flex-start'),
          margin: '0 0 20px 0',
        }">
          <div class="category-title-container">
            <!-- 分类图标 -->
            <div v-if="getCategoryIcon(group.id)" class="category-icon">
              <span v-if="isEmoji(getCategoryIcon(group.id))">{{ getCategoryIcon(group.id) }}</span>
              <img v-else :src="getCategoryIcon(group.id)" />
            </div>
            <div class="category-title">{{ group.name }}</div>
          </div>
          <div v-if="navSettings.show_category_line" class="category-line"></div>
          <div class="category-action">
            <n-button circle quaternary size="small" @click="handleAddSite(group.id)" class="add-btn">
              <template #icon><n-icon><AddIcon /></n-icon></template>
            </n-button>
          </div>
        </div>
        
        <transition-group 
          name="stagger" 
          tag="div" 
          class="sites-grid-container"
        >
          <div 
            v-for="(site, index) in group.sites" 
            :key="site.id" 
            class="site-item-wrapper"
            :style="{ '--i': index }"
          >
            <SiteCard 
              :site="site"
              :styleMode="navSettings.card_style"
              :isDragging="dragItem === site.id"
              @dragstart="onDragStart(site.id)"
              @dragenter="onDragEnter(site.id)"
              @dragend="onDragEnd"
              @click="openUrl(site.url)"
              @contextmenu="handleContextMenu($event, site)"
            />
          </div>
        </transition-group>
      </div>
    </div>

    <n-dropdown
      placement="bottom-start" trigger="manual" :x="xRef" :y="yRef"
      :options="contextMenuOptions" :show="showContextMenu"
      @clickoutside="showContextMenu = false" @select="handleContextMenuSelect"
    />

    <SiteEditorModal 
      v-model:show="showEditor" :editingSite="editingSite"
      :categories="categories" :fetchingIcon="fetchingIcon"
      @save="handleSaveSite" @fetchIcon="handleAutoFetchIcon"
      @update-icon="icon => { if (editingSite) editingSite.icon = icon }"
    />

        <CategoryManagerModal 

          v-model:show="showSettings" :categories="categories" :settings="navSettings"

          :wallpaperLoading="wallpaperLoading"

          @add="(name, icon) => addCategory(name, icon)" @delete="deleteCategory" @reorder="updateCategoryOrder"

          @export="exportConfig" @import="importConfig" @update="(id, name, icon) => updateCategory(id, name, icon)"

          @uploadBg="uploadBackground" @updateSettings="updateNavSettings"

          @resetSettings="resetNavSettings" @refreshWallpaper="() => refreshWallpaper(baseRandomApiUrl, true)"

          @saveWallpaper="() => saveCurrentWallpaper(computedBgUrl)"

        />

    <n-modal v-model:show="showBookmarkManager" :mask-closable="true">
      <div class="bookmark-manager-modal glass-effect" style="width: 90vw; height: 85vh; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); overflow: hidden; background: #1e1e22;">
        <BookmarkManager isModal @close="showBookmarkManager = false" />
      </div>
    </n-modal>
    
  </div>
</template>

<style scoped>
.site-nav-page { 
  position: relative; 
  min-height: 100vh; 
  padding: 8px; 
}

/* 背景底层：实色 */
.site-nav-background-base {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  background-color: var(--nav-bg-color);
}

/* 背景顶层：图片 */
.site-nav-background-image {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
  background-position: center;
  background-repeat: no-repeat;
  pointer-events: none;
  transition: opacity 1s ease, filter 1s ease;
}

/* 遮罩层：增加暗角和深度感，保护文字阅读 */
.site-nav-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2;
  background: radial-gradient(circle at center, transparent 0%, rgba(0, 0, 0, 0.4) 100%),
              linear-gradient(to bottom, rgba(0, 0, 0, 0.2) 0%, transparent 20%, transparent 80%, rgba(0, 0, 0, 0.3) 100%);
  pointer-events: none;
}

.site-nav-content {
  position: relative;
  z-index: 3;
}

.nav-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-title { 
  font-size: 24px; font-weight: 800; color: var(--nav-text-color); 
  text-shadow: 0 4px 12px rgba(0,0,0,0.5); 
  letter-spacing: -0.5px;
}
.page-subtitle { font-size: 13px; color: var(--nav-text-desc-color); margin-bottom: 8px; opacity: 0.9; }

.hitokoto-container {
  display: inline-flex;
  flex-direction: column;
  margin-top: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  max-width: 600px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.hitokoto-container:hover { 
  background: rgba(255, 255, 255, 0.1); 
  transform: translateY(-2px);
}
.hitokoto-text { font-size: 14px; color: var(--nav-text-color); font-style: italic; opacity: 0.95; }
.hitokoto-from { font-size: 12px; color: var(--nav-text-desc-color); align-self: flex-end; margin-top: 6px; }

/* 分类标题美化 */
.category-section { margin-bottom: 48px; }
.category-header { 
  display: flex; 
  align-items: center; 
  gap: 12px;
  min-height: 32px;
}
.category-title-container {
  display: flex;
  align-items: center;
  gap: 8px;
}
.category-icon {
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  line-height: 1;
  flex-shrink: 0;
}
.category-icon span {
  display: block;
  width: 100%;
  height: 100%;
  text-align: center;
  line-height: 28px;
}
.category-icon img {
  width: 22px;
  height: 22px;
  object-fit: contain;
}
.category-title { 
  font-size: 18px; font-weight: 700; color: var(--nav-category-color); 
  text-shadow: 0 2px 4px rgba(0,0,0,0.3); opacity: 0.95;
  white-space: nowrap;
}
.category-line {
  height: 1px;
  flex: 1; /* 只有线条存在时才撑开空间 */
  background: linear-gradient(to right, var(--nav-category-color), transparent);
  opacity: 0.2;
}
.category-action { opacity: 0; transition: all 0.3s ease; display: flex; align-items: center; }
.category-header:hover .category-action { opacity: 1; transform: scale(1.1); }

/* Stagger 动画实现 */
.stagger-enter-active {
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  transition-delay: calc(var(--i) * 0.05s);
}
.stagger-enter-from {
  opacity: 0;
  transform: translateY(30px) scale(0.9);
}

/* 背景切换动画 */
.fade-bg-enter-active, .fade-bg-leave-active {
  transition: opacity 1.2s ease;
}
.fade-bg-enter-from, .fade-bg-leave-to {
  opacity: 0;
}

.sites-grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  width: 100%;
}
.site-item-wrapper { display: flex; }

.empty-state { margin-top: 100px; }
</style>