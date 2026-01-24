<script setup lang="ts">
import { ref, onMounted, computed, nextTick, h } from 'vue'
import { 
  NSpace, NIcon, NEmpty, NGrid, NGridItem, NButton, 
  NDropdown, NTooltip
} from 'naive-ui'
import { 
  LinkOutlined as LinkIcon, 
  LaunchOutlined as LaunchIcon,
  AddCircleOutlineOutlined as AddIcon,
  SettingsOutlined as SettingsIcon,
  EditOutlined as EditIcon,
  DeleteOutlined as DeleteIcon,
  MenuOpenOutlined as MenuOpenIcon,
  MenuOutlined as MenuIcon
} from '@vicons/material'
import { useSiteNav, SiteNav } from './useSiteNav'
import { isHomeEntry } from '../../../store/navigationStore'

// 导入积木组件
import SiteEditorModal from './components/SiteEditorModal.vue'
import CategoryManagerModal from './components/CategoryManagerModal.vue'

const { 
  sites, categories, navSettings, loading, fetchSites, fetchCategories, fetchSettings,
  addSite, updateSite, deleteSite, updateSiteOrder,
  addCategory, deleteCategory, updateCategory, updateCategoryOrder,
  updateNavSettings, resetNavSettings, uploadBackground, fetchIconFromUrl, 
  exportConfig, importConfig, message
} = useSiteNav()

onMounted(() => {
  fetchSites()
  fetchCategories()
  fetchSettings()
})

// --- 状态管理 ---
const showEditor = ref(false)
const showSettings = ref(false)
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
      '--nav-content-width': `${navSettings.content_max_width || 90}%`
    }"
  >
    <!-- 背景层：底层实色 -->
    <div class="site-nav-background-base"></div>
    
    <!-- 背景层：顶层图片（受透明度和模糊度影响） -->
    <div 
      v-if="navSettings.background_url"
      class="site-nav-background-image"
      :style="{
        backgroundImage: `url('${navSettings.background_url}')`,
        opacity: navSettings.background_opacity ?? 0.7,
        filter: `blur(${navSettings.background_blur ?? 0}px)`,
        backgroundSize: navSettings.background_size || 'cover'
      }"
    ></div>

    <!-- 内容包裹层 -->
    <div class="site-nav-content" style="max-width: var(--nav-content-width); margin: 0 auto; padding: 0 20px;">
      <div class="nav-header">
        <div class="header-left">
          <div class="page-title">{{ navSettings.page_title }}</div>
          <div class="page-subtitle">{{ navSettings.page_subtitle }}</div>
        </div>
        <div class="header-right">
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
              <div class="category-header">
                <div class="category-title">{{ group.name }}</div>
                <div class="category-action">
                  <n-button circle quaternary size="small" @click="handleAddSite(group.id)" class="add-btn">
                    <template #icon><n-icon><AddIcon /></n-icon></template>
                  </n-button>
                </div>
              </div>
                <div class="sites-flex-container">
          <div v-for="site in group.sites" :key="site.id" class="site-item-wrapper">
            <div 
              class="site-card" 
              :class="{ 'is-dragging': dragItem === site.id }"
              draggable="true"
              @dragstart="onDragStart(site.id)"
              @dragover.prevent
              @dragenter="onDragEnter(site.id)"
              @dragend="onDragEnd"
              @click="openUrl(site.url)"
              @contextmenu="handleContextMenu($event, site)"
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
          </div>
        </div>
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
      @add="addCategory" @delete="deleteCategory" @reorder="updateCategoryOrder"
      @export="exportConfig" @import="importConfig" @update="updateCategory"
      @uploadBg="uploadBackground" @updateSettings="updateNavSettings"
      @resetSettings="resetNavSettings"
    />
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
  position: fixed;
  inset: 0;
  z-index: 0;
  background-color: var(--nav-bg-color);
  width: 100%;
  height: 100%;
}

/* 背景顶层：图片 */
.site-nav-background-image {
  position: fixed;
  inset: 0;
  z-index: 1;
  background-position: center;
  background-repeat: no-repeat;
  pointer-events: none;
  width: 100%;
  height: 100%;
}

.site-nav-content {
  position: relative;
  z-index: 2;
}

.nav-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-title { font-size: 20px; font-weight: 700; color: var(--nav-text-color); text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
.page-subtitle { font-size: 12px; color: var(--nav-text-desc-color); }

.category-section { margin-bottom: 32px; }
.category-header { display: flex; align-items: center; margin-bottom: 12px; gap: 8px; }
.category-title { font-size: 15px; font-weight: 600; color: var(--nav-category-color); text-shadow: 0 1px 2px rgba(0,0,0,0.5); }
.category-action { opacity: 0; transition: opacity 0.2s; }
.category-header:hover .category-action { opacity: 1; }

.sites-flex-container { display: flex; flex-wrap: wrap; gap: 16px; }
.site-item-wrapper { flex-shrink: 0; }

.site-card {
  display: flex; align-items: center; padding: 8px 12px;
  height: 64px; width: 200px;
  background: var(--nav-card-bg);
  backdrop-filter: blur(var(--nav-card-blur));
  border: 1px solid var(--nav-card-border);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border-radius: 12px; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.site-card:hover { 
  border-color: var(--primary-color); 
  transform: translateY(-4px); 
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 0.2);
}
.site-card.is-dragging { opacity: 0.1; transform: scale(0.9); }

.site-icon-wrapper {
  width: 44px; height: 44px; display: flex; align-items: center; justify-content: center;
  background: rgba(255, 255, 255, 0.1); margin-right: 12px; flex-shrink: 0;
  border-radius: 10px; overflow: hidden;
  transition: all 0.3s ease;
}
.image-icon { width: 100%; height: 100%; object-fit: cover; }
.emoji-icon { font-size: 28px; line-height: 1; }

.site-info { flex: 1; min-width: 0; text-align: left; display: flex; flex-direction: column; justify-content: center; }
.site-name { font-size: 14px; font-weight: 600; color: var(--nav-text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.site-desc { font-size: 11px; color: var(--nav-text-desc-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.empty-state { margin-top: 100px; }
</style>