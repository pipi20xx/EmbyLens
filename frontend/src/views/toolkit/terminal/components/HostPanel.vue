<template>
  <div class="host-panel">
    <div class="panel-header">
      <span class="title">主机列表</span>
      <n-button quaternary circle size="tiny" @click="openModal()">
        <template #icon><n-icon :component="AddIcon" /></template>
      </n-button>
    </div>
    <n-scrollbar>
      <div class="host-list">
        <div 
          class="host-item" 
          :class="{ active: modelValue === 0 }"
          @click="$emit('update:modelValue', 0)"
        >
          <n-icon :component="LocalIcon" />
          <span class="name">本地 Shell</span>
        </div>
        <div 
          v-for="h in hosts" 
          :key="h.id" 
          class="host-item"
          :class="{ active: modelValue === h.id }"
          @click="$emit('update:modelValue', h.id)"
        >
          <n-icon :component="HostIcon" />
          <span class="name" :title="h.host">{{ h.name }}</span>
          <div class="actions">
            <n-button text size="tiny" @click.stop="openModal(h)"><n-icon :component="EditIcon" /></n-button>
            <n-popconfirm 
              @positive-click="handleDelete(h.id)"
              positive-text="确定删除"
              negative-text="我再想想"
            >
              <template #trigger>
                <n-button text size="tiny" type="error" @click.stop><n-icon :component="DeleteIcon" /></n-button>
              </template>
              确定要删除主机「{{ h.name }}」吗？此操作不可撤销。
            </n-popconfirm>
          </div>
        </div>
      </div>
    </n-scrollbar>

    <!-- 主机配置弹窗 -->
    <n-modal v-model:show="showModal" preset="card" :title="editingId ? '编辑主机' : '新增主机'" style="width: 480px">
      <n-form :model="form" label-placement="left" label-width="90">
        <n-form-item label="名称"><n-input v-model:value="form.name" placeholder="例如：我的服务器" /></n-form-item>
        <n-form-item label="连接地址">
          <n-input-group>
            <n-input v-model:value="form.host" placeholder="IP/域名" style="width: 70%" />
            <n-input-number v-model:value="form.port" :show-button="false" placeholder="22" style="width: 30%" />
          </n-input-group>
        </n-form-item>
        <n-form-item label="登录用户"><n-input v-model:value="form.username" placeholder="root" /></n-form-item>
        <n-form-item label="认证方式">
          <n-radio-group v-model:value="form.auth_type">
            <n-radio-button value="password">密码认证</n-radio-button>
            <n-radio-button value="key">密钥认证</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item v-if="form.auth_type === 'password'" label="登录密码">
          <n-input type="password" v-model:value="form.password" show-password-on="click" />
        </n-form-item>
        <template v-else>
          <n-form-item label="私钥内容">
            <n-input type="textarea" v-model:value="form.private_key" :autosize="{ minRows: 3, maxRows: 6 }" placeholder="-----BEGIN RSA PRIVATE KEY-----" />
          </n-form-item>
          <n-form-item label="私钥密码">
            <n-input type="password" v-model:value="form.private_key_password" placeholder="可选，若私钥已加密请填写" show-password-on="click" />
          </n-form-item>
        </template>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="handleSave">保存配置</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { 
  NButton, NIcon, NScrollbar, NModal, NForm, NFormItem, 
  NInput, NInputNumber, NRadioGroup, NRadioButton, NSpace, NInputGroup,
  NPopconfirm
} from 'naive-ui';
import { 
  AddCircleOutlineOutlined as AddIcon,
  EditOutlined as EditIcon,
  DeleteOutlineOutlined as DeleteIcon,
  ComputerOutlined as LocalIcon,
  DnsOutlined as HostIcon
} from '@vicons/material';

const props = defineProps<{ modelValue: number }>();
const emit = defineEmits(['update:modelValue', 'change']);

const hosts = ref<any[]>([]);
const showModal = ref(false);
const editingId = ref<number | null>(null);
const form = ref({ 
  name: '', host: '', port: 22, username: 'root', 
  auth_type: 'password', password: '', private_key: '', private_key_password: '' 
});

const fetchHosts = async () => {
  const res = await axios.get('/api/terminal/hosts');
  hosts.value = res.data;
};

const openModal = (host?: any) => {
  if (host) {
    editingId.value = host.id;
    form.value = { ...host };
  } else {
    editingId.value = null;
    form.value = { 
      name: '', host: '', port: 22, username: 'root', 
      auth_type: 'password', password: '', private_key: '', private_key_password: '' 
    };
  }
  showModal.value = true;
};

const handleSave = async () => {
  if (editingId.value) {
    await axios.put(`/api/terminal/hosts/${editingId.value}`, form.value);
  } else {
    await axios.post('/api/terminal/hosts', form.value);
  }
  showModal.value = false;
  fetchHosts();
};

const handleDelete = async (id: number) => {
  await axios.delete(`/api/terminal/hosts/${id}`);
  if (props.modelValue === id) emit('update:modelValue', 0);
  fetchHosts();
};

onMounted(fetchHosts);
defineExpose({ fetchHosts });
</script>

<style scoped>
.host-panel { height: 100%; display: flex; flex-direction: column; background: var(--sidebar-bg-color); }
.panel-header { padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); }
.panel-header .title { font-weight: bold; color: var(--text-color); opacity: 0.6; font-size: 12px; text-transform: uppercase; }
.host-list { padding: 8px; }
.host-item { display: flex; align-items: center; padding: 10px 12px; border-radius: 6px; cursor: pointer; color: var(--text-color); opacity: 0.8; transition: 0.2s; margin-bottom: 4px; position: relative; }
.host-item:hover { background: rgba(255, 255, 255, 0.05); opacity: 1; }
.host-item.active { background: var(--primary-color); color: #fff; opacity: 1; }
.host-item .name { margin-left: 10px; font-size: 13px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.host-item .actions { display: none; gap: 4px; }
.host-item:hover .actions { display: flex; }
</style>