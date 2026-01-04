<template>
  <div class="dedupe-container p-4">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">媒体查重与智能清理</h1>
      <div class="space-x-2">
        <button 
          @click="syncMedia" 
          :disabled="syncing"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50 transition-colors"
        >
          <i class="fas fa-sync-alt mr-2" :class="{'animate-spin': syncing}"></i>
          {{ syncing ? '正在同步...' : '同步 Emby 媒体' }}
        </button>
        <button 
          @click="fetchDuplicates" 
          class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
        >
          <i class="fas fa-search mr-2"></i>
          查找重复项
        </button>
      </div>
    </div>

    <!-- 进度显示 -->
    <div v-if="syncing" class="mb-4 p-4 bg-blue-50 border border-blue-200 rounded text-blue-700">
      正在从 Emby 获取全量媒体数据并更新本地索引，请稍候...
    </div>

    <!-- 统计摘要 -->
    <div v-if="duplicateGroups.length > 0" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div class="p-4 bg-white rounded shadow border-l-4 border-yellow-500">
        <div class="text-gray-500 text-sm">重复资源组</div>
        <div class="text-2xl font-bold">{{ duplicateGroups.length }}</div>
      </div>
      <div class="p-4 bg-white rounded shadow border-l-4 border-red-500">
        <div class="text-gray-500 text-sm">待清理项目 (建议)</div>
        <div class="text-2xl font-bold">{{ suggestedCount }}</div>
      </div>
      <div class="p-4 bg-white rounded shadow border-l-4 border-blue-500">
        <div class="text-gray-500 text-sm">选中的项目</div>
        <div class="text-2xl font-bold">{{ selectedIds.length }}</div>
      </div>
    </div>

    <!-- 操作栏 -->
    <div v-if="duplicateGroups.length > 0" class="mb-4 flex items-center justify-between bg-gray-100 p-3 rounded">
      <div class="flex items-center space-x-4">
        <button @click="autoSelect" class="text-sm px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700">
          智能选中
        </button>
        <button @click="selectedIds = []" class="text-sm px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600">
          全不选
        </button>
      </div>
      <button 
        @click="confirmDelete" 
        :disabled="selectedIds.length === 0"
        class="px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 font-bold"
      >
        删除选中项 ({{ selectedIds.length }})
      </button>
    </div>

    <!-- 重复项列表 -->
    <div v-if="duplicateGroups.length > 0" class="space-y-6">
      <div v-for="group in duplicateGroups" :key="group.tmdb_id" class="bg-white rounded shadow overflow-hidden">
        <div class="bg-gray-50 p-3 border-b flex justify-between items-center">
          <span class="font-bold text-gray-700">
            TMDB ID: {{ group.tmdb_id }} - {{ group.items[0].name }}
          </span>
          <span class="text-xs text-gray-400">{{ group.items.length }} 个副本</span>
        </div>
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-gray-100 text-xs uppercase text-gray-600">
              <th class="p-3 w-10">选</th>
              <th class="p-3">名称 / 路径</th>
              <th class="p-3">类型</th>
              <th class="p-3">规格</th>
              <th class="p-3">编码</th>
              <th class="p-3">动态范围</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in group.items" :key="item.emby_id" 
                class="border-t hover:bg-blue-50 transition-colors"
                :class="{'bg-red-50': selectedIds.includes(item.emby_id)}">
              <td class="p-3 text-center">
                <input type="checkbox" :value="item.emby_id" v-model="selectedIds" class="w-4 h-4" />
              </td>
              <td class="p-3">
                <div class="font-medium text-sm">{{ item.name }}</div>
                <div class="text-xs text-gray-400 font-mono truncate max-w-md">{{ item.path }}</div>
              </td>
              <td class="p-3 text-xs">{{ item.type }}</td>
              <td class="p-3"><span class="px-2 py-0.5 bg-gray-200 rounded text-xs">{{ item.display_title }}</span></td>
              <td class="p-3 text-xs">{{ item.video_codec }}</td>
              <td class="p-3 text-xs">
                <span v-if="item.video_range && item.video_range !== 'SDR'" class="px-2 py-0.5 bg-orange-100 text-orange-700 rounded">{{ item.video_range }}</span>
                <span v-else class="text-gray-400">{{ item.video_range }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 无数据展示 -->
    <div v-else-if="!syncing" class="flex flex-col items-center justify-center py-20 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200 text-gray-400">
      <i class="fas fa-copy text-5xl mb-4"></i>
      <p>暂无重复项数据</p>
      <p class="text-sm">点击上方“同步”或“查找重复项”开始</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

const syncing = ref(false);
const duplicateGroups = ref<any[]>([]);
const selectedIds = ref<string[]>([]);
const suggestedCount = ref(0);

const fetchDuplicates = async () => {
  try {
    const res = await axios.get('/api/dedupe/duplicates');
    duplicateGroups.value = res.data;
    selectedIds.value = []; // 重置选中
  } catch (error) {
    alert('获取重复项失败');
  }
};

const syncMedia = async () => {
  if (!confirm('全量同步可能需要一些时间（取决于媒体库大小），确定开始吗？')) return;
  syncing.value = true;
  try {
    await axios.post('/api/dedupe/sync', { item_types: ['Movie', 'Series'] });
    alert('同步完成');
    await fetchDuplicates();
  } catch (error) {
    alert('同步失败');
  } finally {
    syncing.value = false;
  }
};

const autoSelect = async () => {
  if (duplicateGroups.value.length === 0) return;
  
  // 展平所有 item
  const allItems = duplicateGroups.value.flatMap(g => g.items);
  try {
    const res = await axios.post('/api/dedupe/smart-select', { items: allItems });
    selectedIds.value = res.data.to_delete;
    suggestedCount.value = selectedIds.value.length;
  } catch (error) {
    alert('智能选中算法执行失败');
  }
};

const confirmDelete = async () => {
  if (!confirm(`确定要永久删除选中的 ${selectedIds.value.length} 个项目吗？此操作无法撤销，文件将从磁盘移除。`)) return;
  
  try {
    const res = await axios.delete('/api/dedupe/items', { data: { item_ids: selectedIds.value } });
    alert(`清理完成: 成功 ${res.data.success}, 失败 ${res.data.total - res.data.success}`);
    await fetchDuplicates();
  } catch (error) {
    alert('删除请求执行失败');
  }
};

onMounted(() => {
  fetchDuplicates();
});
</script>

<style scoped>
.dedupe-container {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
