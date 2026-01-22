<script setup lang="ts">
import { ref } from 'vue'
import { 
  NModal, NForm, NFormItem, NInput, NInputNumber, 
  NSelect, NButton, NSpace, NInputGroup, NIcon, NAvatar, NUpload, useMessage
} from 'naive-ui'
import { 
  AutoFixHighOutlined as MagicIcon, 
  LanguageOutlined as WebIcon,
  FileUploadOutlined as UploadIcon
} from '@vicons/material'
import { SiteNav, Category } from '../useSiteNav'

const props = defineProps<{
  show: boolean
  editingSite: Partial<SiteNav> | null
  categories: Category[]
  fetchingIcon: boolean
}>()

const emit = defineEmits(['update:show', 'save', 'fetchIcon'])
const message = useMessage()

const handleUploadFinish = ({ event }: { event: any }) => {
  try {
    const res = JSON.parse(event.target.response)
    if (res.icon && props.editingSite) {
      props.editingSite.icon = res.icon
      message.success('图标上传成功')
    }
  } catch (e) {
    message.error('解析上传结果失败')
  }
}

const isEmoji = (str: string) => {
  if (!str) return false
  if (str.includes('/') || str.includes('.')) return false
  return /\p{Emoji}/u.test(str) && str.length <= 4
}
</script>

<template>
  <n-modal :show="show" @update:show="val => emit('update:show', val)" preset="card" :title="editingSite?.id ? '编辑站点' : '添加新站点'" style="width: 500px">
    <n-form v-if="editingSite" :model="editingSite" label-placement="left" label-width="80">
      <n-form-item label="访问链接">
        <n-input-group>
          <n-input v-model:value="editingSite.url" placeholder="http://..." />
          <n-button type="primary" secondary :loading="fetchingIcon" @click="emit('fetchIcon')">
            <template #icon><n-icon><MagicIcon /></n-icon></template>
          </n-button>
        </n-input-group>
      </n-form-item>
      
      <n-form-item label="站点名称">
        <n-input v-model:value="editingSite.title" placeholder="例如：Emby" />
      </n-form-item>

      <n-form-item label="所属分类">
        <n-select v-model:value="editingSite.category_id" :options="categories.map(c => ({label: c.name, value: c.id}))" placeholder="请选择分类" />
      </n-form-item>

      <n-form-item label="图标地址">
        <n-space vertical style="width: 100%">
          <n-input-group>
            <n-input v-model:value="editingSite.icon" placeholder="URL 或 Emoji" />
            <n-button type="primary" secondary :loading="fetchingIcon" @click="emit('fetchIcon')">
              <template #icon><n-icon><MagicIcon /></n-icon></template>
            </n-button>
          </n-input-group>
          
          <n-upload
            action="/api/navigation/upload-icon"
            :show-file-list="false"
            @finish="handleUploadFinish"
          >
            <n-button block type="info" secondary dashed size="small">
              <template #icon><n-icon><UploadIcon /></n-icon></template>
              上传本地图标 (PNG/JPG/SVG/ICO)
            </n-button>
          </n-upload>

          <div class="mini-preview">
            <template v-if="editingSite.icon">
              <div v-if="isEmoji(editingSite.icon)" class="preview-emoji">{{ editingSite.icon }}</div>
              <img v-else :src="editingSite.icon" class="preview-img" />
            </template>
            <n-icon v-else size="20"><WebIcon /></n-icon>
          </div>
        </n-space>
      </n-form-item>

      <n-form-item label="站点描述">
        <n-input v-model:value="editingSite.description" type="textarea" placeholder="简短描述" />
      </n-form-item>

      <n-form-item label="排序权重">
        <n-input-number v-model:value="editingSite.order" :min="0" />
      </n-form-item>
    </n-form>
    <template #footer>
      <n-space justify="end">
        <n-button @click="emit('update:show', false)">取消</n-button>
        <n-button type="primary" @click="emit('save')">确认保存</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<style scoped>
.mini-preview {
  height: 44px;
  width: 44px;
  background: rgba(255,255,255,0.1);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.preview-img { width: 100%; height: 100%; object-fit: cover; }
.preview-emoji { font-size: 24px; }
</style>
