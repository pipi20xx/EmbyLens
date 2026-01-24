<template>
  <div class="command-panel">
    <div class="panel-header">
      <n-text strong>快速命令</n-text>
      <n-button quaternary circle size="tiny" @click="openModal()">
        <template #icon><n-icon :component="AddIcon" /></template>
      </n-button>
    </div>
    <div class="panel-toolbar">
      <n-checkbox v-model:checked="autoEnter">点击即执行</n-checkbox>
    </div>
    <n-scrollbar>
      <div class="command-container">
        <div 
          v-for="cmd in commands" 
          :key="cmd.id" 
          class="command-card"
          @click="$emit('send', cmd.command, autoEnter)"
        >
          <div class="card-header">
            <span class="cmd-title">{{ cmd.title }}</span>
                            <n-space :size="4">
                              <n-button quaternary circle size="tiny" @click.stop="openModal(cmd)">
                                <template #icon><n-icon :component="EditIcon" /></template>
                              </n-button>
                  <n-popconfirm 
                    @positive-click="handleDelete(cmd.id)"
                    positive-text="确定删除"
                    negative-text="取消"
                  >
                    <template #trigger>
                      <n-button quaternary circle size="tiny" type="error" @click.stop>
                        <template #icon><n-icon :component="DeleteIcon" /></template>
                      </n-button>
                    </template>
                    确定要删除快速命令「{{ cmd.title }}」吗？
                  </n-popconfirm>
                </n-space>
              </div>
              <div class="cmd-preview">{{ cmd.command }}</div>
            </div>
          </div>
        </n-scrollbar>

    <!-- 命令弹窗 -->
    <n-modal v-model:show="showModal" preset="card" :title="editingId ? '编辑命令' : '新建命令'" style="width: 400px">
      <n-form :model="form" label-placement="top">
        <n-form-item label="标题"><n-input v-model:value="form.title" placeholder="例如：查看日志" /></n-form-item>
        <n-form-item label="命令"><n-input type="textarea" v-model:value="form.command" placeholder="tail -f /app/logs/app.log" /></n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="handleSave">保存</n-button>
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
  NInput, NSpace, NText, NCheckbox, NEmpty, NPopconfirm 
} from 'naive-ui';
import { 
  AddCircleOutlineOutlined as AddIcon,
  EditOutlined as EditIcon,
  DeleteOutlineOutlined as DeleteIcon
} from '@vicons/material';

defineEmits(['send']);

const commands = ref<any[]>([]);
const autoEnter = ref(false);
const showModal = ref(false);
const editingId = ref<number | null>(null);
const form = ref({ title: '', command: '' });

const fetchCommands = async () => {
  const res = await axios.get('/api/terminal/commands');
  commands.value = res.data;
};

const openModal = (cmd?: any) => {
  if (cmd) {
    editingId.value = cmd.id;
    form.value = { ...cmd };
  } else {
    editingId.value = null;
    form.value = { title: '', command: '' };
  }
  showModal.value = true;
};

const handleSave = async () => {
  if (editingId.value) {
    await axios.put(`/api/terminal/commands/${editingId.value}`, form.value);
  } else {
    await axios.post('/api/terminal/commands', form.value);
  }
  showModal.value = false;
  fetchCommands();
};

const handleDelete = async (id: number) => {
  await axios.delete(`/api/terminal/commands/${id}`);
  fetchCommands();
};

onMounted(fetchCommands);
</script>

<style scoped>
.command-panel { height: 100%; display: flex; flex-direction: column; background: var(--sidebar-bg-color); }
.panel-header { padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); }
.panel-toolbar { padding: 8px 16px; border-bottom: 1px solid var(--border-color); }
.command-container { padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.command-card { background: var(--card-bg-color); border: 1px solid var(--border-color); border-radius: 6px; padding: 10px; cursor: pointer; transition: 0.2s; }
.command-card:hover { border-color: var(--primary-color); background: rgba(255, 255, 255, 0.03); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.cmd-title { font-weight: 600; font-size: 13px; color: var(--text-color); }
.cmd-preview { font-family: monospace; font-size: 11px; color: var(--text-color); opacity: 0.5; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
