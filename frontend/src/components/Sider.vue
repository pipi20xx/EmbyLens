<template>
  <aside class="embylens-sider" :class="{ 'is-collapsed': collapsed }">
    <!-- 1. Logo 区域 -->
    <div class="logo-box">
      <n-icon size="32" color="#705df2"><LensIcon /></n-icon>
      <div v-if="!collapsed" class="logo-info">
        <span class="logo-text">EmbyLens</span>
        <span class="version-badge">v1.0.0</span>
      </div>
    </div>

    <!-- 2. 强可见控制台 (设置与日志) - 自定义按钮样式 -->
    <div class="sider-toolbar">
      <div class="toolbar-inner" :class="{ 'is-vertical': collapsed }">
        <!-- 系统设置按钮 -->
        <div 
          class="custom-icon-btn" 
          :class="{ 'is-active': $route.name === 'Settings' }"
          @click="$router.push({ name: 'Settings' })"
          title="系统设置"
        >
          <n-icon size="22"><SettingsIcon /></n-icon>
        </div>

        <!-- 实时日志按钮 -->
        <div 
          class="custom-icon-btn log-btn" 
          @click="$emit('show-log')"
          title="实时日志"
        >
          <n-icon size="22"><TerminalIcon /></n-icon>
        </div>
      </div>
    </div>

    <div class="nav-divider"></div>

    <!-- 3. 业务功能菜单 -->
    <nav class="nav-list">
      <router-link 
        v-for="item in menuItems" 
        :key="item.key" 
        :to="{ name: item.key }"
        class="nav-item"
        :title="collapsed ? item.label : ''"
      >
        <n-icon size="22" class="nav-icon"><component :is="item.icon" /></n-icon>
        <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- 4. 底部收缩开关 -->
    <div class="sider-bottom" @click="toggleCollapse">
      <n-icon size="20">
        <ChevronLeft v-if="!collapsed" />
        <ChevronRight v-else />
      </n-icon>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  DashboardRound as DashboardIcon,
  AutoDeleteRound as DedupeIcon,
  SettingsRound as SettingsIcon,
  CameraRound as LensIcon,
  EditNoteRound as MetadataIcon,
  PeopleRound as ActorIcon,
  ChevronLeftRound as ChevronLeft,
  ChevronRightRound as ChevronRight,
  TerminalRound as TerminalIcon
} from '@vicons/material'

defineEmits(['show-log'])

const collapsed = ref(false)
const toggleCollapse = () => {
  collapsed.value = !collapsed.value
}

const menuItems = [
  { label: '管理仪表盘', key: 'Dashboard', icon: DashboardIcon },
  { label: '重复项清理', key: 'Dedupe', icon: DedupeIcon },
  { label: '类型映射管理', key: 'TypeManager', icon: MetadataIcon },
  { label: '媒体净化清理', key: 'Cleanup', icon: ActorIcon },
  { label: '元数据锁定器', key: 'LockManager', icon: ActorIcon }
]
</script>

<style scoped>
.embylens-sider {
  width: 240px;
  background-color: #18181c;
  border-right: 1px solid #333;
  height: 100vh;
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  z-index: 1000;
}

.embylens-sider.is-collapsed {
  width: 70px;
}

.logo-box {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 19px;
  gap: 12px;
}

.logo-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.logo-text {
  font-size: 19px;
  font-weight: bold;
  color: #705df2;
  line-height: 1.2;
}

.version-badge {
  font-size: 10px;
  color: #555;
  font-family: monospace;
  margin-top: -2px;
}

/* 核心工具栏：强制显色 */
.sider-toolbar {
  padding: 16px 0;
  display: flex;
  justify-content: center;
}

.toolbar-inner {
  display: flex;
  gap: 20px;
}

.toolbar-inner.is-vertical {
  flex-direction: column;
  gap: 12px;
}

/* 自定义图标按钮样式 - 确保绝对可见 */
.custom-icon-btn {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #26262a;
  border: 1px solid #3f3f46;
  border-radius: 10px;
  color: #a1a1aa;
  cursor: pointer;
  transition: all 0.2s;
}

.custom-icon-btn:hover {
  border-color: #705df2;
  color: #fff;
  background-color: #2d2d31;
}

.custom-icon-btn.is-active {
  background-color: rgba(112, 93, 242, 0.2);
  border-color: #705df2;
  color: #705df2;
}

.log-btn {
  color: #705df2; /* 日志按钮默认紫色，增加辨识度 */
}

.nav-divider {
  height: 1px;
  background-color: #333;
  margin: 0 20px 10px 20px;
}

.nav-list {
  padding: 0 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  border-radius: 8px;
  color: #aaa;
  text-decoration: none;
  height: 48px;
  transition: all 0.2s;
}

.nav-item:hover { background: rgba(255, 255, 255, 0.05); color: #fff; }
.nav-item.router-link-active { background: rgba(112, 93, 242, 0.15); color: #705df2; }

.nav-label { margin-left: 12px; font-size: 14px; white-space: nowrap; }

.is-collapsed .nav-item { justify-content: center; padding: 0; }
.is-collapsed .nav-label { display: none; }

.sider-bottom {
  height: 50px;
  border-top: 1px solid #333;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #555;
}
.sider-bottom:hover { color: #705df2; }
</style>