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
  DeleteOutlined as DeleteIcon
} from '@vicons/material'
import { useSiteNav, SiteNav } from './useSiteNav'

// 导入积木组件
import SiteEditorModal from './components/SiteEditorModal.vue'
import CategoryManagerModal from './components/CategoryManagerModal.vue'

const { 
  sites, categories, loading, fetchSites, fetchCategories, 
  addSite, updateSite, deleteSite, updateSiteOrder,
  addCategory, deleteCategory, updateCategory, updateCategoryOrder, fetchIconFromUrl, 
  exportConfig, importConfig, message
} = useSiteNav()

onMounted(() => {
  fetchSites()
  fetchCategories()
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
    // 关键：如果跨分类拖拽，我们需要更新被拖拽项的 category_id
    const fromSite = sites.value[fromIndex]
    const toSite = sites.value[toIndex]
    
    if (fromSite.category_id !== toSite.category_id) {
      fromSite.category_id = toSite.category_id
      fromSite.category = toSite.category
    }

    // 物理交换数组位置
    const [item] = sites.value.splice(fromIndex, 1)
    sites.value.splice(toIndex, 0, item)
  }
}

const onDragEnd = async () => {
  if (dragItem.value === null) return
  // 同步到后端
  await updateSiteOrder(sites.value.map(s => s.id))
  dragItem.value = null
}

// --- 其他交互 ---

const handleAddSite = (categoryId?: number) => {
  editingSite.value = {
    title: '', url: '', icon: '', description: '',
    // 关键修复：如果没有传入 ID，尝试使用第一个现有分类，否则留空
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
  // 如果包含斜杠或点，说明是路径或 URL，不是 Emoji
  if (str.includes('/') || str.includes('.')) return false
  return /\p{Emoji}/u.test(str) && str.length <= 4
}
const openUrl = (url: string) => window.open(url, '_blank')
</script>

<template>
  <div class="site-nav-page">
    <div class="nav-header">
      <div class="header-left">
        <div class="page-title">站点导航</div>
        <div class="page-subtitle">右键编辑卡片，直接拖动卡片排序（支持跨分类拖拽）</div>
      </div>
      <div class="header-right">
        <n-button circle quaternary @click="showSettings = true">
          <template #icon><n-icon><SettingsIcon /></n-icon></template>
        </n-button>
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
        <div class="category-line"></div>
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

    <n-dropdown
      placement="bottom-start" trigger="manual" :x="xRef" :y="yRef"
      :options="contextMenuOptions" :show="showContextMenu"
      @clickoutside="showContextMenu = false" @select="handleContextMenuSelect"
    />

    <SiteEditorModal 
      v-model:show="showEditor" :editingSite="editingSite"
      :categories="categories" :fetchingIcon="fetchingIcon"
      @save="handleSaveSite" @fetchIcon="handleAutoFetchIcon"
    />

    <!-- 分类积木 -->
    <CategoryManagerModal 
      v-model:show="showSettings"
      :categories="categories"
      @add="addCategory"
      @delete="deleteCategory"
      @reorder="updateCategoryOrder"
      @export="exportConfig"
      @import="importConfig"
      @update="updateCategory"
    />
  </div>
</template>

<style scoped>
.site-nav-page { padding: 12px; }
.nav-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-title { font-size: 20px; font-weight: 700; color: var(--primary-color); }
.page-subtitle { font-size: 12px; opacity: 0.5; }
.category-section { margin-bottom: 32px; }
.category-header { display: flex; align-items: center; margin-bottom: 12px; gap: 8px; }
.category-title { font-size: 15px; font-weight: 600; opacity: 0.8; }
.category-action { opacity: 0; transition: opacity 0.2s; }
.category-header:hover .category-action { opacity: 1; }
.category-line { height: 1px; background: var(--primary-color); opacity: 0.1; flex: 1; }

.sites-flex-container {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.site-item-wrapper {
  /* 确保拖拽时占位正确 */
  flex-shrink: 0;
}

.site-card {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 4px 8px;
  height: 60px;
  /* 固定宽度：180px */
  width: 180px;
  background: var(--card-bg-color);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}


.site-card:hover {
  transform: translateY(-2px);
  border-color: var(--primary-color);
  box-shadow: 0 4px 12px -6px var(--primary-color);
  background: rgba(255, 255, 255, 0.05);
}

.site-icon-wrapper {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  /* 减少右边距 */
  margin-right: 6px;
  flex-shrink: 0;
}

.image-icon {
  /* 图片尽可能撑满容器 */
  width: 48px;
  height: 48px;
  object-fit: contain;
}

.emoji-icon {
  /* Emoji 也要足够大 */
  font-size: 36px;
  line-height: 1;
}

.site-info {
  flex: 1;
  min-width: 0;
  text-align: left;
  /* 补偿一下文字的垂直居中 */
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.site-name {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.site-desc {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}


</style>
