<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { 
  NCard, NButton, NSpace, NDataTable, NModal, NForm, 
  NFormItem, NInput, NInputNumber, NIcon, NPopconfirm,
  NTag, NSelect, NDivider, NAvatar
} from 'naive-ui'
import { 
  AddOutlined as AddIcon,
  EditOutlined as EditIcon,
  DeleteOutlined as DeleteIcon,
  LanguageOutlined as WebIcon,
  AutoFixHighOutlined as MagicIcon,
  CategoryOutlined as CategoryIcon
} from '@vicons/material'
import { useSiteNav, SiteNav, Category } from './useSiteNav'

const { 
  sites, categories, loading, fetchSites, fetchCategories, 
  addCategory, deleteCategory, addSite, updateSite, deleteSite, 
  fetchIconFromUrl, message
} = useSiteNav()

const showModal = ref(false)
const showCatModal = ref(false)
const fetchingIcon = ref(false)
const newCatName = ref('')
const editingId = ref<number | null>(null)

const formValue = ref<Partial<SiteNav>>({
  title: '',
  url: '',
  icon: '',
  description: '',
  category_id: undefined,
  order: 0
})

onMounted(() => {
  fetchSites()
  fetchCategories()
})

const catOptions = computed(() => {
  return categories.value.map(c => ({ label: c.name, value: c.id }))
})

const handleAdd = () => {
  editingId.value = null
  formValue.value = { title: '', url: '', icon: '', description: '', category_id: categories.value[0]?.id, order: 0 }
  showModal.value = true
}

const handleEdit = (row: SiteNav) => {
  editingId.value = row.id
  formValue.value = { ...row }
  showModal.value = true
}

const handleAutoFetchIcon = async () => {
  if (!formValue.value.url) {
    message.warning('请先输入站点链接')
    return
  }
  fetchingIcon.value = true
  try {
    const icon = await fetchIconFromUrl(formValue.value.url)
    if (icon) {
      formValue.value.icon = icon
      message.success('图标抓取成功')
    } else {
      message.error('未能在页面中找到图标')
    }
  } catch (e) {
    message.error('抓取过程发生错误')
  } finally {
    fetchingIcon.value = false
  }
}

const isEmoji = (str: string) => {
  if (!str) return false
  return /\p{Emoji}/u.test(str) && str.length <= 4
}

const handleIconError = () => {
  // 如果图片加载失败，可以在这里处理，或者显示默认图
}

const handleSave = async () => {
  let success = false
  if (editingId.value) {
    success = await updateSite(editingId.value, formValue.value)
  } else {
    success = await addSite(formValue.value)
  }
  if (success) showModal.value = false
}

const handleAddCat = async () => {
  if (!newCatName.value) return
  await addCategory(newCatName.value)
  newCatName.value = ''
}

const columns = [
  { title: '排序', key: 'order', width: 60 },
  { title: '图标', key: 'icon', width: 60, render(row: SiteNav) {
    return h(NAvatar, { size: 'small', src: row.icon, round: true, fallbackSrc: 'https://007007.xyz/favicon.ico' })
  }},
  { title: '名称', key: 'title', width: 120 },
  { title: '分类', key: 'category', width: 100, render(row: SiteNav) {
    return h(NTag, { type: 'primary', size: 'small', bordered: false }, { default: () => row.category })
  }},
  { title: '链接', key: 'url', ellipsis: true },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render(row: SiteNav) {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { size: 'small', quaternary: true, onClick: () => handleEdit(row) }, { icon: () => h(NIcon, null, { default: () => h(EditIcon) }) }),
          h(NPopconfirm, { onPositiveClick: () => deleteSite(row.id) }, {
            trigger: () => h(NButton, { size: 'small', quaternary: true, type: 'error' }, { icon: () => h(NIcon, null, { default: () => h(DeleteIcon) }) }),
            default: () => '确定删除吗？'
          })
        ]
      })
    }
  }
]
</script>

<template>
  <div class="site-manager">
    <n-space vertical size="large">
      <n-card title="导航管理中心" :bordered="false" size="small">
        <template #header-extra>
          <n-space>
            <n-button secondary size="small" @click="showCatModal = true">
              <template #icon><n-icon><CategoryIcon /></n-icon></template>
              管理分类
            </n-button>
            <n-button type="primary" size="small" @click="handleAdd">
              <template #icon><n-icon><AddIcon /></n-icon></template>
              添加站点
            </n-button>
          </n-space>
        </template>

        <n-data-table
          :columns="columns"
          :data="sites"
          :loading="loading"
          size="small"
          :max-height="600"
        />
      </n-card>
    </n-space>

    <!-- 站点编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="card" :title="editingId ? '编辑站点' : '添加新站点'" style="width: 550px">
      <n-form :model="formValue" label-placement="left" label-width="80">
        <n-form-item label="访问链接">
          <n-input-group>
            <n-input v-model:value="formValue.url" placeholder="http://..." />
            <n-button type="primary" secondary :loading="fetchingIcon" @click="handleAutoFetchIcon">
              <template #icon><n-icon><MagicIcon /></n-icon></template>
              获取图标
            </n-button>
          </n-input-group>
        </n-form-item>
        
        <n-form-item label="站点名称">
          <n-input v-model:value="formValue.title" placeholder="例如：Emby" />
        </n-form-item>

        <n-form-item label="所属分类">
          <n-select v-model:value="formValue.category_id" :options="catOptions" placeholder="请选择分类" />
        </n-form-item>

        <n-form-item label="图标地址">
          <n-space vertical style="width: 100%">
            <n-input-group>
              <n-input v-model:value="formValue.icon" placeholder="URL 或 Emoji" />
              <n-button type="primary" secondary :loading="fetchingIcon" @click="handleAutoFetchIcon">
                <template #icon><n-icon><MagicIcon /></n-icon></template>
                抓取图标
              </n-button>
            </n-input-group>
            
            <div class="icon-preview-box">
              <div class="preview-label">效果预览：</div>
              <div class="preview-content">
                <template v-if="formValue.icon">
                  <div v-if="isEmoji(formValue.icon)" class="preview-emoji">{{ formValue.icon }}</div>
                  <img v-else :src="formValue.icon" class="preview-img" @error="handleIconError" />
                </template>
                <div v-else class="preview-placeholder">
                  <n-icon size="24"><WebIcon /></n-icon>
                  <span>待填入</span>
                </div>
              </div>
              <div v-if="formValue.icon && !isEmoji(formValue.icon)" class="preview-url">
                {{ formValue.icon }}
              </div>
            </div>
          </n-space>
        </n-form-item>

        <n-form-item label="站点描述">
          <n-input v-model:value="formValue.description" type="textarea" placeholder="简短描述该站点" />
        </n-form-item>

        <n-form-item label="排序权重">
          <n-input-number v-model:value="formValue.order" :min="0" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="handleSave">确认保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 分类管理弹窗 -->
    <n-modal v-model:show="showCatModal" preset="card" title="分类管理" style="width: 400px">
      <n-space vertical>
        <n-input-group>
          <n-input v-model:value="newCatName" placeholder="新分类名称" />
          <n-button type="primary" @click="handleAddCat">添加</n-button>
        </n-input-group>
        <n-divider title-placement="left">已有分类</n-divider>
        <n-space v-if="categories.length > 0">
          <n-tag 
            v-for="cat in categories" 
            :key="cat.id" 
            closable 
            @close="deleteCategory(cat.id)"
          >
            {{ cat.name }}
          </n-tag>
        </n-space>
        <div v-else style="text-align: center; color: #999">暂无分类</div>
      </n-space>
    </n-modal>
  </div>
</template>

<style scoped>
.icon-preview-box {
  background: rgba(255, 255, 255, 0.03);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.preview-label {
  font-size: 12px;
  color: #999;
  width: 100%;
}

.preview-content {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-emoji {
  font-size: 32px;
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #666;
  font-size: 10px;
}

.preview-url {
  font-size: 11px;
  color: var(--primary-color);
  opacity: 0.7;
  word-break: break-all;
  text-align: center;
  max-width: 100%;
}
</style>