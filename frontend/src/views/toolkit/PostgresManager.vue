<template>
  <div class="postgres-manager">
    <n-space vertical size="large">
      <n-card>
        <template #header>
          <n-space align="center" justify="space-between" style="width: 100%">
            <n-space align="center" size="large">
              <n-text strong style="font-size: 18px">PostgreSQL 管理</n-text>
              <n-select
                v-model:value="selectedHostId"
                :options="hostOptions"
                placeholder="选择数据库实例"
                style="width: 220px"
                @update:value="handleHostChange"
              />
              <n-button type="primary" secondary @click="showHostModal = true">管理主机</n-button>
            </n-space>
            <n-space>
              <n-button :disabled="!selectedHost" ghost @click="refreshAll" :loading="refreshing">
                全部刷新
              </n-button>
            </n-space>
          </n-space>
        </template>

        <n-tabs v-model:value="activeTab" type="line" animated>
          <n-tab-pane name="data" tab="数据浏览器">
            <table-browser-panel ref="tablePanelRef" :host="selectedHost" />
          </n-tab-pane>

          <n-tab-pane name="databases" tab="数据库列表">
            <database-panel ref="dbPanelRef" :host="selectedHost" />
          </n-tab-pane>

          <n-tab-pane name="users" tab="用户列表">
            <user-panel ref="userPanelRef" :host="selectedHost" />
          </n-tab-pane>
        </n-tabs>
      </n-card>
    </n-space>

    <!-- 模块化弹窗 -->
    <host-manager-modal 
      v-model:show="showHostModal" 
      @refresh="fetchHosts" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { NSpace, NCard, NText, NButton, NSelect, NTabs, NTabPane, useMessage } from 'naive-ui'
import axios from 'axios'

// 导入乐高组件
import TableBrowserPanel from './pgsql/components/TableBrowserPanel.vue'
import DatabasePanel from './pgsql/components/DatabasePanel.vue'
import UserPanel from './pgsql/components/UserPanel.vue'
import HostManagerModal from './pgsql/components/HostManagerModal.vue'

const message = useMessage()
const hosts = ref<any[]>([])
const selectedHostId = ref<string | null>(null)
const activeTab = ref('data')
const refreshing = ref(false)
const showHostModal = ref(false)

const tablePanelRef = ref()
const dbPanelRef = ref()
const userPanelRef = ref()

const hostOptions = computed(() => hosts.value.map(h => ({ label: h.name, value: h.id })))
const selectedHost = computed(() => hosts.value.find(h => h.id === selectedHostId.value))

const fetchHosts = async () => {
  try {
    const res = await axios.get('/api/pgsql/hosts')
    hosts.value = res.data
    if (hosts.value.length > 0 && !selectedHostId.value) {
      selectedHostId.value = hosts.value[0].id
    }
  } catch (e) {
    message.error('加载主机列表失败')
  }
}

const handleHostChange = () => {
  // 子组件通过 watch host prop 会自动处理刷新
}

const refreshAll = async () => {
  if (!selectedHost.value) return
  refreshing.value = true
  await Promise.all([
    tablePanelRef.value?.refresh(),
    dbPanelRef.value?.refresh(),
    userPanelRef.value?.refresh()
  ])
  refreshing.value = false
}

onMounted(fetchHosts)
</script>
