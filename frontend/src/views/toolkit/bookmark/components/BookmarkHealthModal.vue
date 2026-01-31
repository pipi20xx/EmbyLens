<template>
  <n-modal 
    :show="show" 
    @update:show="$emit('update:show', $event)" 
    preset="card" 
    title="书签体检中心" 
    style="width: 1000px; height: 90vh;" 
    class="standard-modal"
    :bordered="false"
    content-style="padding: 0; display: flex; flex-direction: column; overflow: hidden;"
  >
    <div class="health-modal-body">
      <n-tabs 
        type="line" 
        animated 
        justify-content="space-evenly"
        class="custom-tabs"
        pane-class="custom-tab-pane"
      >
        <n-tab-pane name="duplicate" tab="重复检测">
          <DuplicateScanner 
            :duplicates="duplicates"
            :loading-duplicates="loadingDuplicates"
            :bookmarks="bookmarks"
            @scanDuplicates="$emit('scanDuplicates')"
            @mergeDuplicate="(g, id) => $emit('mergeDuplicate', g, id)"
            @mergeAllDuplicates="$emit('mergeAllDuplicates')"
          />
        </n-tab-pane>

        <n-tab-pane name="health" tab="无效链接诊断">
          <DeadLinkScanner 
            :health-results="healthResults"
            :health-progress="healthProgress"
            :is-scanning-health="isScanningHealth"
            :bookmarks="bookmarks"
            @scanHealth="$emit('scanHealth')"
            @stopScan="$emit('stopScan')"
            @deleteDead="(id) => $emit('deleteDead', id)"
            @deleteBatchDead="(codes) => $emit('deleteBatchDead', codes)"
          />
        </n-tab-pane>
      </n-tabs>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import DuplicateScanner from './DuplicateScanner.vue'
import DeadLinkScanner from './DeadLinkScanner.vue'

defineProps<{
  show: boolean
  activeTab: string
  duplicates: any[]
  loadingDuplicates: boolean
  healthResults: any[]
  healthProgress: number
  isScanningHealth: boolean
  bookmarks: any[]
}>()

defineEmits([
  'update:show',
  'update:activeTab',
  'scanDuplicates',
  'deleteGroup',
  'mergeDuplicate',
  'mergeAllDuplicates',
  'scanHealth',
  'stopScan',
  'deleteDead',
  'deleteBatchDead'
])
</script>

<style scoped>
.health-modal-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 0;
  background-color: var(--card-bg-color);
}

.custom-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.n-tabs-nav) {
  background: rgba(255, 255, 255, 0.01);
  padding: 0 20px;
  border-bottom: 1px solid var(--border-color);
}

:deep(.n-tabs-tab) {
  font-weight: 700;
  font-size: 15px;
  padding: 12px 24px;
}

:deep(.n-tabs-pane-wrapper) {
  flex: 1;
  height: 0;
}

:deep(.custom-tab-pane) {
  height: 100%;
  padding: 0 !important;
}

.standard-modal {
  border-radius: 16px;
}
</style>