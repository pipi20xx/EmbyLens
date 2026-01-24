<template>
  <div class="terminal-manager-view">
    <!-- 顶部状态栏 -->
    <div class="terminal-top-bar">
      <div class="bar-left">
        <n-button quaternary circle size="small" @click="collapsedSider = !collapsedSider">
          <template #icon><n-icon :component="MenuIcon" /></template>
        </n-button>
        <n-divider vertical />
        <n-breadcrumb>
          <n-breadcrumb-item>终端管理</n-breadcrumb-item>
          <n-breadcrumb-item><n-text strong>{{ currentHostName }}</n-text></n-breadcrumb-item>
        </n-breadcrumb>
        <n-tag :type="activeSessionConnected ? 'success' : 'error'" size="small" round class="status-dot">
          {{ activeSessionConnected ? '已连接' : '已断开' }}
        </n-tag>
      </div>
      <div class="bar-right">
        <n-space>
          <n-button quaternary circle size="small" @click="clearActiveTerm" title="清屏">
            <template #icon><n-icon :component="ClearIcon" /></template>
          </n-button>
          <n-button quaternary circle size="small" @click="reconnectActiveTerm" title="重连">
            <template #icon><n-icon :component="RefreshIcon" /></template>
          </n-button>
        </n-space>
      </div>
    </div>

    <n-layout has-sider class="main-layout">
      <!-- 主机列表 -->
      <n-layout-sider
        bordered
        collapse-mode="width"
        :collapsed-width="0"
        :width="220"
        :collapsed="collapsedSider"
      >
        <HostPanel 
          :model-value="activeHostId" 
          @update:model-value="handleHostSelect" 
        />
      </n-layout-sider>

      <!-- 多会话终端容器 -->
      <n-layout-content class="terminal-workspace">
        <!-- 循环渲染所有已打开的会话，使用 v-show 保持连接 -->
        <TerminalInstance
          v-for="session in openSessions"
          :key="session.id"
          :ref="(el) => setInstanceRef(session.id, el)"
          :host-id="session.id"
          :host-name="session.name"
          :visible="activeHostId === session.id"
          @connected="session.connected = true"
          @disconnected="session.connected = false"
        />
        <div v-if="openSessions.length === 0" class="empty-terminal">
          正在初始化终端会话...
        </div>
      </n-layout-content>

      <!-- 快速命令 -->
      <n-layout-sider bordered :width="240">
        <CommandPanel @send="sendToActiveTerm" />
      </n-layout-sider>
    </n-layout>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue';
import { 
  NLayout, NLayoutSider, NLayoutContent, NButton, NSpace, NTag, 
  NDivider, NBreadcrumb, NBreadcrumbItem, NText, NIcon 
} from 'naive-ui';
import { 
  MenuOpenOutlined as MenuIcon,
  RefreshOutlined as RefreshIcon,
  AutoDeleteOutlined as ClearIcon
} from '@vicons/material';

import HostPanel from './components/HostPanel.vue';
import CommandPanel from './components/CommandPanel.vue';
import TerminalInstance from './components/TerminalInstance.vue';

interface Session {
  id: number;
  name: string;
  connected: boolean;
}

const collapsedSider = ref(false);
const activeHostId = ref(0);
const openSessions = ref<Session[]>([
  { id: 0, name: '本地 Shell', connected: false }
]);

// 存储各个终端实例的引用
const instanceRefs = new Map<number, any>();
const setInstanceRef = (id: number, el: any) => {
  if (el) instanceRefs.set(id, el);
};

const activeSessionConnected = computed(() => {
  return openSessions.value.find(s => s.id === activeHostId.value)?.connected || false;
});

const currentHostName = computed(() => {
  return openSessions.value.find(s => s.id === activeHostId.value)?.name || '未知主机';
});

// 处理主机切换逻辑
const handleHostSelect = (id: number) => {
  activeHostId.value = id;
  
  // 如果会话列表中没有，则添加并初始化
  if (!openSessions.value.some(s => s.id === id)) {
    // 这里需要获取主机名称，如果是从 HostPanel 传过来更好
    // 暂时先起个名，后续可以从 HostPanel 的列表里取
    openSessions.value.push({
      id: id,
      name: `主机 ${id}`,
      connected: false
    });
  }
};

const sendToActiveTerm = (cmd: string, autoEnter: boolean) => {
  const instance = instanceRefs.get(activeHostId.value);
  if (instance) {
    instance.send(cmd + (autoEnter ? '\n' : ''));
    instance.focus();
  }
};

const clearActiveTerm = () => instanceRefs.get(activeHostId.value)?.clear();
const reconnectActiveTerm = () => instanceRefs.get(activeHostId.value)?.reconnect();

onMounted(() => {
  // 默认开启本地终端
});
</script>

<style scoped>
.terminal-manager-view { 
  height: 100%; 
  display: flex; 
  flex-direction: column; 
  background: var(--app-bg-color); 
  overflow: hidden; 
}
.terminal-top-bar { 
  height: 42px; 
  flex-shrink: 0;
  background: var(--card-bg-color); 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  padding: 0 12px; 
  border-bottom: 1px solid var(--border-color); 
}
.bar-left { display: flex; align-items: center; gap: 8px; }
.main-layout { flex: 1; overflow: hidden; }
.terminal-workspace { 
  background: #000; /* 终端核心区建议保持纯黑或极深色，但容器可随主题 */
  padding: 0; 
  position: relative; 
  height: 100%;
}
.empty-terminal { height: 100%; display: flex; align-items: center; justify-content: center; color: var(--text-color); opacity: 0.5; }
</style>