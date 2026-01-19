<template>
  <n-modal v-model:show="show" preset="card" title="Docker 主机管理" style="width: 600px">
    <n-space vertical>
      <n-button type="primary" block @click="handleAddHost">添加新主机</n-button>
      <n-list bordered>
        <n-list-item v-for="host in hosts" :key="host.id">
          <n-space justify="space-between" align="center">
            <div>
              <n-text strong>{{ host.name }}</n-text>
              <n-tag size="small" type="warning" style="margin-left: 8px">SSH 远程</n-tag>
            </div>
            <n-space>
              <n-button size="small" @click="testConnection(host.id)">测试</n-button>
              <n-button size="small" @click="handleEditHost(host)">编辑</n-button>
              <n-button size="small" type="error" ghost @click="deleteHost(host.id)">删除</n-button>
            </n-space>
          </n-space>
        </n-list-item>
      </n-list>
    </n-space>
  </n-modal>

  <!-- 编辑弹窗 -->
  <n-modal v-model:show="showEditModal" preset="card" :title="editHostForm.id ? '编辑主机' : '添加主机'" style="width: 500px">
    <n-form :model="editHostForm" label-placement="left" label-width="100">
      <n-form-item label="名称"><n-input v-model:value="editHostForm.name" /></n-form-item>
      <n-form-item label="连接类型">
        <n-select v-model:value="editHostForm.type" :options="[{ label: '远程 Docker (SSH)', value: 'ssh' }]" />
      </n-form-item>
      <n-form-item label="SSH 地址"><n-input v-model:value="editHostForm.ssh_host" placeholder="127.0.0.1" /></n-form-item>
      <n-form-item label="SSH 端口"><n-input-number v-model:value="editHostForm.ssh_port" style="width: 100%" /></n-form-item>
      <n-form-item label="SSH 用户"><n-input v-model:value="editHostForm.ssh_user" /></n-form-item>
      <n-form-item label="SSH 密码"><n-input v-model:value="editHostForm.ssh_pass" type="password" show-password-on="mousedown" /></n-form-item>
      <n-form-item label="扫描路径"><n-input v-model:value="editHostForm.compose_scan_paths" type="textarea" placeholder="逗号分隔" /></n-form-item>
      <n-space justify="end">
        <n-button @click="showEditModal = false">取消</n-button>
        <n-button type="primary" @click="saveHost">保存</n-button>
      </n-space>
    </n-form>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { NModal, NSpace, NButton, NList, NListItem, NText, NTag, NForm, NFormItem, NInput, NInputNumber, NSelect, useMessage } from 'naive-ui'
import axios from 'axios'

const props = defineProps<{
  show: boolean
  hosts: any[]
}>()

const emit = defineEmits(['update:show', 'refresh'])

const message = useMessage()
const show = ref(props.show)
const showEditModal = ref(false)
const editHostForm = ref<any>({})

watch(() => props.show, (val) => show.value = val)
watch(() => show.value, (val) => emit('update:show', val))

const handleAddHost = () => { editHostForm.value = { type: 'ssh', ssh_port: 22, ssh_user: 'root' }; showEditModal.value = true }
const handleEditHost = (h: any) => { editHostForm.value = { ...h }; showEditModal.value = true }
const saveHost = async () => {
  if (editHostForm.value.id) await axios.put(`/api/docker/hosts/${editHostForm.value.id}`, editHostForm.value)
  else await axios.post('/api/docker/hosts', editHostForm.value)
  showEditModal.value = false; emit('refresh')
}
const deleteHost = async (id: string) => { await axios.delete(`/api/docker/hosts/${id}`); emit('refresh') }
const testConnection = async (id: string) => {
  const res = await axios.post(`/api/docker/${id}/test`)
  message.info(res.data.status === 'ok' ? '连接正常' : '连接失败')
}
</script>
