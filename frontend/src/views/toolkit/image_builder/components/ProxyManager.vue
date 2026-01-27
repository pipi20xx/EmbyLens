<template>
  <div class="proxy-manager">
    <n-card title="构建代理设置" size="small">
      <template #header-extra>
        <n-button size="small" type="primary" @click="showModal = true">添加代理</n-button>
      </template>
      <n-text depth="3">配置 HTTP/HTTPS 代理，用于在构建过程中加速下载基础镜像或依赖包。</n-text>
      <div style="margin-top: 12px">
        <n-data-table :columns="columns" :data="proxies" size="small" />
      </div>
    </n-card>

    <n-modal v-model:show="showModal" preset="card" title="添加代理" style="width: 450px">
      <n-form :model="form" label-placement="left" label-width="100">
        <n-form-item label="名称">
          <n-input v-model:value="form.name" placeholder="例如: Clash" />
        </n-form-item>
        <n-form-item label="代理地址">
          <n-input v-model:value="form.url" placeholder="例如: http://192.168.1.5:7890" />
        </n-form-item>
        <n-form-item label="用户名">
          <n-input v-model:value="form.username" placeholder="可选" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="form.password" type="password" show-password-on="click" placeholder="可选" />
        </n-form-item>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="saveProxy">保存</n-button>
        </n-space>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { 
  NCard, NButton, NDataTable, NModal, NForm, NFormItem, 
  NInput, NSpace, NText, useMessage 
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()

const proxies = ref([])
const showModal = ref(false)
const form = ref({
  name: '',
  url: ''
})

const columns = [
  { title: '名称', key: 'name' },
  { title: '代理地址', key: 'url' },
  {
    title: '操作',
    key: 'actions',
    render(row: any) {
      return h(NButton, { size: 'small', type: 'error', ghost: true, onClick: () => deleteProxy(row.id) }, { default: () => '删除' })
    }
  }
]

const fetchProxies = async () => {
  try {
    const res = await axios.get('/api/image-builder/proxies')
    proxies.value = res.data
  } catch (e) {}
}

const saveProxy = async () => {
  try {
    await axios.post('/api/image-builder/proxies', form.value)
    message.success('已保存')
    showModal.value = false
    fetchProxies()
  } catch (e) {
    message.error('保存失败')
  }
}

const deleteProxy = async (id: string) => {
  try {
    await axios.delete(`/api/image-builder/proxies/${id}`)
    fetchProxies()
  } catch (e) {}
}

onMounted(fetchProxies)
</script>
