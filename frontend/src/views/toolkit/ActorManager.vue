<template>
  <div class="toolkit-container">
    <n-space vertical size="large">
      <div class="page-header">
        <n-h2 prefix="bar" align-text><n-text type="primary">演员信息多端同步</n-text></n-h2>
        <n-text depth="3">独立检索 Emby 库内资料与 TMDB 官方数据，支持双向比对与元数据对齐。</n-text>
      </div>

      <n-grid :cols="2" :x-gap="16" item-responsive responsive="screen">
        <!-- 1. 左侧：Emby 库内检索 -->
        <n-gi span="2 m:1">
          <n-card title="Emby 本地检索" size="small" segmented>
            <n-input-group>
              <n-select v-model:value="embyMode" :options="searchModes" style="width: 110px" />
              <n-input v-model:value="embyQuery" :placeholder="embyMode === 'id' ? '输入 TMDB ID' : '输入姓名'" @keyup.enter="handleEmbySearch" />
              <n-button type="primary" secondary @click="handleEmbySearch" :loading="embyLoading">搜索</n-button>
            </n-input-group>

            <n-scrollbar style="max-height: 450px; margin-top: 12px">
              <n-list v-if="embyResults.length > 0" hoverable clickable>
                <n-list-item 
                  v-for="person in embyResults" 
                  :key="person.Id" 
                  :class="{ 'selected-item': selectedEmby?.Id === person.Id }"
                  @click="selectedEmby = person"
                >
                  <template #prefix>
                    <n-avatar round size="large" :src="getEmbyAvatar(person)" />
                  </template>
                  <n-thing :title="person.Name">
                    <template #description>
                      <n-space>
                        <n-tag size="tiny" tertiary>EMBY: {{ person.Id }}</n-tag>
                        <n-tag v-if="person.ProviderIds?.Tmdb" size="tiny" type="info" quaternary>TMDB: {{ person.ProviderIds.Tmdb }}</n-tag>
                      </n-space>
                    </template>
                  </n-thing>
                  <template #suffix>
                    <n-button secondary circle size="tiny" type="primary" @click.stop="showJson(person)">
                      <template #icon><n-icon color="#bb86fc"><CodeIcon /></n-icon></template>
                    </n-button>
                  </template>
                </n-list-item>
              </n-list>
              <n-empty v-else description="无结果" />
            </n-scrollbar>
          </n-card>
        </n-gi>

        <!-- 2. 右侧：TMDB 官方检索 -->
        <n-gi span="2 m:1">
          <n-card title="TMDB 云端检索" size="small" segmented>
            <n-input-group>
              <n-select v-model:value="tmdbMode" :options="searchModes" style="width: 110px" />
              <n-input v-model:value="tmdbQuery" :placeholder="tmdbMode === 'id' ? '输入 TMDB ID' : '输入姓名'" @keyup.enter="handleTmdbSearch" />
              <n-button type="info" secondary @click="handleTmdbSearch" :loading="tmdbLoading">搜索</n-button>
            </n-input-group>

            <n-scrollbar style="max-height: 450px; margin-top: 12px">
              <n-list v-if="tmdbResults.length > 0" hoverable clickable>
                <n-list-item 
                  v-for="person in tmdbResults" 
                  :key="person.id"
                  :class="{ 'selected-item': selectedTmdb?.id === person.id }"
                  @click="selectedTmdb = person"
                >
                  <template #prefix>
                    <n-avatar round size="large" :src="person.profile_path ? `https://image.tmdb.org/t/p/w200${person.profile_path}` : ''" />
                  </template>
                  <n-thing :title="person.name">
                    <template #description>
                      <n-text depth="3">TMDB ID: {{ person.id }}</n-text>
                    </template>
                  </n-thing>
                  <template #suffix>
                    <n-button secondary circle size="tiny" type="info" @click.stop="showJson(person)">
                      <template #icon><n-icon color="#bb86fc"><CodeIcon /></n-icon></template>
                    </n-button>
                  </template>
                </n-list-item>
              </n-list>
              <n-empty v-else description="无结果" />
            </n-scrollbar>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 3. 对齐与同步 -->
      <n-card v-if="selectedEmby || selectedTmdb" title="对齐同步预览" size="small">
        <n-grid :cols="2" :x-gap="24">
          <n-gi>
            <n-descriptions label-placement="top" title="Emby 本地项" :column="1">
              <n-descriptions-item label="显示姓名 (可编辑)">
                <n-input-group>
                  <n-input v-model:value="editName" size="small" />
                  <n-button type="primary" secondary size="small" @click="handleUpdateName" :loading="nameLoading">修改</n-button>
                </n-input-group>
              </n-descriptions-item>
            </n-descriptions>
          </n-gi>
          <n-gi>
            <n-descriptions label-placement="top" title="TMDB 参考项" :column="1">
              <n-descriptions-item label="官方姓名">
                <n-space align="center">
                  <n-text strong>{{ selectedTmdb?.name || '-' }}</n-text>
                  <n-button v-if="selectedTmdb" quaternary size="tiny" type="primary" @click="editName = selectedTmdb.name">引用此名</n-button>
                </n-space>
              </n-descriptions-item>
            </n-descriptions>
          </n-gi>
        </n-grid>
        <template #footer>
          <n-space justify="end">
            <n-button type="primary" :disabled="!selectedEmby || !selectedTmdb" @click="handleSync" :loading="syncLoading">
              全量同步至本地库
            </n-button>
          </n-space>
        </template>
      </n-card>

      <!-- JSON 弹窗 -->
      <n-modal v-model:show="jsonModal.show" preset="card" style="width: 800px" title="演员元数据 JSON 审计">
        <div class="json-code-wrapper">
          <n-code :code="JSON.stringify(jsonModal.data, null, 2)" language="json" word-wrap />
        </div>
        <template #footer>
          <n-button block type="primary" secondary @click="copyRawJson">复制 JSON 数据</n-button>
        </template>
      </n-modal>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { 
  useMessage, NSpace, NH2, NText, NCard, NInput, NButton, NInputGroup, 
  NList, NListItem, NAvatar, NThing, NScrollbar, NEmpty, NGi, NGrid, 
  NDescriptions, NDescriptionsItem, NCode, NTag, NSelect, NModal, NIcon 
} from 'naive-ui'
import { TerminalOutlined as CodeIcon } from '@vicons/material'
import axios from 'axios'

const message = useMessage()
const searchModes = [{ label: '按名称', value: 'name' }, { label: '按 ID', value: 'id' }]

// 状态
const embyMode = ref('name'); const embyQuery = ref(''); const embyLoading = ref(false); const embyResults = ref<any[]>([])
const tmdbMode = ref('name'); const tmdbQuery = ref(''); const tmdbLoading = ref(false); const tmdbResults = ref<any[]>([])
const selectedEmby = ref<any>(null); const selectedTmdb = ref<any>(null)
const editName = ref(''); const nameLoading = ref(false); const syncLoading = ref(false)
const jsonModal = reactive({ show: false, data: {} as any })

watch(selectedEmby, (val) => { if (val) editName.value = val.Name })

const showJson = (item: any) => { jsonModal.data = item; jsonModal.show = true; }
const copyRawJson = () => {
  const text = JSON.stringify(jsonModal.data, null, 2)
  const textArea = document.createElement("textarea")
  textArea.value = text; document.body.appendChild(textArea); textArea.select()
  document.execCommand('copy'); document.body.removeChild(textArea)
  message.success('已复制到剪贴板')
}

const handleEmbySearch = async () => {
  if (!embyQuery.value) return
  embyLoading.value = true
  try {
    const res = await axios.get('/api/actors/search-emby', { params: { query: embyQuery.value }})
    embyResults.value = res.data.results
  } catch (e) { message.error('Emby 检索失败') }
  finally { embyLoading.value = false }
}

const handleTmdbSearch = async () => {
  if (!tmdbQuery.value) return
  tmdbLoading.value = true
  try {
    const res = await axios.get('/api/actors/search-tmdb', { params: { query: tmdbQuery.value }})
    tmdbResults.value = res.data.results
  } catch (e) { message.error('TMDB 检索失败') }
  finally { tmdbLoading.value = false }
}

const getEmbyAvatar = (person: any) => {
  if (!person.PrimaryImageTag) return ''
  return `/api/system/img-proxy?id=${person.Id}&tag=${person.PrimaryImageTag}` 
}

const handleUpdateName = async () => {
  if (!selectedEmby.value || !editName.value) return
  nameLoading.value = true
  try {
    await axios.post('/api/actors/update-actor-name', { emby_id: selectedEmby.value.Id, new_name: editName.value })
    message.success('姓名已更新'); selectedEmby.value.Name = editName.value
  } catch (e) { message.error('更新失败') }
  finally { nameLoading.value = false }
}

const handleSync = async () => {
  if (!selectedEmby.value || !selectedTmdb.value) return
  syncLoading.value = true
  try {
    await axios.post('/api/actors/update-emby-actor', {
      emby_id: selectedEmby.value.Id,
      data: { Name: editName.value, ProviderIds: { ...selectedEmby.value.ProviderIds, Tmdb: selectedTmdb.value.id.toString() } }
    })
    message.success('同步成功'); handleEmbySearch()
  } catch (e) { message.error('同步失败') }
  finally { syncLoading.value = false }
}
</script>

<style scoped>
.toolkit-container { max-width: 1400px; margin: 0 auto; }
.selected-item { background-color: rgba(187, 134, 252, 0.1) !important; border-left: 4px solid #bb86fc; }
.json-code-wrapper { background: #050505; padding: 16px; border-radius: 8px; max-height: 60vh; overflow-y: auto; border: 1px solid #333; }
</style>