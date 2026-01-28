<template>
  <n-modal v-model:show="show" preset="card" :title="'文件管理器: ' + currentPath" style="width: 90vw; max-width: 1100px">
    <n-space vertical size="large">
      <n-breadcrumb>
        <n-breadcrumb-item @click="browse('/')">根目录</n-breadcrumb-item>
        <n-breadcrumb-item v-for="(part, index) in pathParts" :key="index" @click="jumpTo(index)">
          {{ part }}
        </n-breadcrumb-item>
      </n-breadcrumb>
      
      <n-list hoverable clickable bordered style="max-height: 60vh; overflow-y: auto">
        <n-list-item v-if="currentPath !== '/'" @click="browse(getParentPath(currentPath))">
          <n-text depth="3">.. (返回上级)</n-text>
        </n-list-item>
        
        <n-list-item v-for="item in items" :key="item.path" @click="item.is_dir ? browse(item.path) : viewFile(item.path)">
          <template #prefix>
            <n-icon size="24" :color="item.is_dir ? '#fadb14' : '#8c8c8c'">
              <folder-icon v-if="item.is_dir" />
              <file-icon v-else />
            </n-icon>
          </template>
          
          <n-text :strong="item.is_dir" style="font-size: 15px">{{ item.name }}</n-text>
          
          <template #suffix>
            <n-space>
              <n-button size="small" secondary @click.stop="openPermissionModal(item)">权限/属性</n-button>
              <n-button 
                v-if="item.is_dir && isSelected(item.path)"
                size="small" type="error" quaternary @click.stop="$emit('remove', item.path)"
              >
                取消扫描
              </n-button>
              <n-button 
                v-else-if="item.is_dir"
                size="small" type="primary" quaternary @click.stop="$emit('select', item.path)"
              >
                设为扫描路径
              </n-button>

              <n-button 
                v-if="item.is_dir"
                size="small" type="info" quaternary @click.stop="createBackup(item)"
              >
                设为SSH备份
              </n-button>

              <n-button v-if="!item.is_dir" size="small" tertiary @click.stop="viewFile(item.path)">查看</n-button>
            </n-space>
          </template>
        </n-list-item>
      </n-list>
    </n-space>
  </n-modal>

  <!-- 权限修改弹窗 (1Panel 风格) -->
  <n-modal v-model:show="showPermissionModal" preset="dialog" title="设置权限与所有者" style="width: 500px">
    <n-form label-placement="top" style="margin-top: 10px">
      <n-form-item label="当前路径">
        <n-text depth="3" code>{{ permissionForm.path }}</n-text>
      </n-form-item>
      
      <!-- 权限矩阵 -->
      <n-table :bordered="false" :single-column="false" size="small">
        <thead>
          <tr>
            <th>对象</th>
            <th>读取</th>
            <th>写入</th>
            <th>执行</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="role in ['owner', 'group', 'public']" :key="role">
            <td>{{ role === 'owner' ? '所有者' : role === 'group' ? '用户组' : '公共' }}</td>
            <td><n-checkbox v-model:checked="permMatrix[role].read" @update:checked="calcMode" /></td>
            <td><n-checkbox v-model:checked="permMatrix[role].write" @update:checked="calcMode" /></td>
            <td><n-checkbox v-model:checked="permMatrix[role].execute" @update:checked="calcMode" /></td>
          </tr>
        </tbody>
      </n-table>

      <n-grid :cols="2" :x-gap="12" style="margin-top: 15px">
        <n-gi>
          <n-form-item label="权限代码">
            <n-input v-model:value="permissionForm.mode" placeholder="0755" />
          </n-form-item>
        </n-gi>
        <n-gi>
          <n-form-item label="所有者:用户组">
            <n-input-group>
              <n-input v-model:value="permissionForm.owner" placeholder="root" />
              <n-input-group-label>:</n-input-group-label>
              <n-input v-model:value="permissionForm.group" placeholder="root" />
            </n-input-group>
          </n-form-item>
        </n-gi>
      </n-grid>

      <n-form-item v-if="permissionForm.is_dir">
        <n-checkbox v-model:checked="permissionForm.recursive">递归应用到子项</n-checkbox>
      </n-form-item>
    </n-form>
    <template #action>
      <n-button @click="showPermissionModal = false">取消</n-button>
      <n-button type="primary" @click="submitPermissions">确定应用</n-button>
    </template>
  </n-modal>

  <!-- 文件查看弹窗 -->
  <n-modal v-model:show="showFileContent" preset="card" :title="'查看文件: ' + viewingFileName" style="width: 80vw">
    <pre class="file-viewer">{{ fileContent }}</pre>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch, computed, reactive } from 'vue'
import { 
  NModal, NSpace, NBreadcrumb, NBreadcrumbItem, NList, NListItem, NText, NButton, 
  NIcon, NForm, NFormItem, NInput, NCheckbox, NTable, NGrid, NGi, NInputGroup, NInputGroupLabel, useMessage, useDialog 
} from 'naive-ui'
import { 
  FolderOutlined as FolderIcon,
  InsertDriveFileOutlined as FileIcon
} from '@vicons/material'
import axios from 'axios'

const props = defineProps<{
  show: boolean
  hostId: string
  selectedPaths: string[]
  initialPath?: string
}>()

const emit = defineEmits(['update:show', 'select', 'remove'])

const message = useMessage()
const dialog = useDialog()
const items = ref<any[]>([])
const currentPath = ref('/')
const show = ref(props.show)

// 文件查看
const showFileContent = ref(false)
const fileContent = ref('')
const viewingFileName = ref('')

// 权限管理
const showPermissionModal = ref(false)
const permissionForm = reactive({
  path: '',
  mode: '0755',
  owner: 'root',
  group: 'root',
  is_dir: false,
  recursive: false
})

const createBackup = (item: any) => {
  dialog.info({
    title: '创建 SSH 备份',
    content: `确定要为文件夹 ${item.name} 创建一个 SSH 自动备份任务吗？`,
    positiveText: '确认创建',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await axios.post(`/api/docker/compose/${props.hostId}/create-folder-backup`, { 
          path: item.path 
        })
        message.success('备份任务已创建')
      } catch (e: any) {
        message.error('创建失败: ' + (e.response?.data?.detail || '未知错误'))
      }
    }
  })
}

const permMatrix = reactive({
  owner: { read: true, write: true, execute: true },
  group: { read: true, write: false, execute: true },
  public: { read: true, write: false, execute: true }
})

const pathParts = computed(() => currentPath.value.split('/').filter(p => p))

watch(() => props.show, (val) => { 
  show.value = val; 
  if(val) browse(props.initialPath || currentPath.value || '/') 
})
watch(() => show.value, (val) => emit('update:show', val))

const browse = async (path: string) => {
  if (!props.hostId) return
  try {
    const res = await axios.get(`/api/docker/compose/${props.hostId}/ls`, { params: { path } })
    currentPath.value = res.data.current_path
    items.value = res.data.items
  } catch (e) {
    message.error('读取目录失败')
  }
}

const jumpTo = (index: number) => {
  const target = '/' + pathParts.value.slice(0, index + 1).join('/')
  browse(target)
}

const calcMode = () => {
  const getVal = (role: 'owner' | 'group' | 'public') => {
    let val = 0
    if (permMatrix[role].read) val += 4
    if (permMatrix[role].write) val += 2
    if (permMatrix[role].execute) val += 1
    return val
  }
  permissionForm.mode = `0${getVal('owner')}${getVal('group')}${getVal('public')}`
}

const openPermissionModal = (item: any) => {
  permissionForm.path = item.path
  permissionForm.is_dir = item.is_dir
  permissionForm.recursive = false
  // 初始化矩阵 (根据 0755 或 0644)
  const defaultMode = item.is_dir ? '755' : '644'
  permissionForm.mode = '0' + defaultMode
  
  const setFromCode = (code: string) => {
    const parse = (char: string) => {
      const n = parseInt(char)
      return { read: !!(n & 4), write: !!(n & 2), execute: !!(n & 1) }
    }
    permMatrix.owner = parse(code[0])
    permMatrix.group = parse(code[1])
    permMatrix.public = parse(code[2])
  }
  setFromCode(defaultMode)
  showPermissionModal.value = true
}

const submitPermissions = async () => {
  try {
    await axios.post(`/api/docker/compose/${props.hostId}/chmod`, {
      path: permissionForm.path,
      mode: permissionForm.mode.startsWith('0') ? permissionForm.mode.substring(1) : permissionForm.mode,
      owner: permissionForm.owner,
      group: permissionForm.group,
      recursive: permissionForm.recursive
    })
    message.success('属性更新成功')
    showPermissionModal.value = false
  } catch (e) {
    message.error('更新失败: ' + (e.response?.data?.detail || '未知错误'))
  }
}

const viewFile = async (path: string) => {
  if (!props.hostId) return
  viewingFileName.value = path.split('/').pop() || ''
  try {
    const res = await axios.get(`/api/docker/compose/${props.hostId}/projects/file`, {
      params: { path: path, name: 'temp' }
    })
    fileContent.value = res.data.content
    showFileContent.value = true
  } catch (e) {
    message.error('无法读取文件内容')
  }
}

const getParentPath = (path: string) => path.substring(0, path.lastIndexOf('/')) || '/'
const isSelected = (path: string) => props.selectedPaths.includes(path)
</script>

<style scoped>
.file-viewer {
  background: #1e1e1e; color: #dcdcdc; padding: 15px; border-radius: 4px;
  max-height: 70vh; overflow: auto; font-family: monospace; white-space: pre-wrap;
}
</style>
