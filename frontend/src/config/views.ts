import { defineAsyncComponent } from 'vue'

export const viewMap: Record<string, any> = {
  DashboardView: defineAsyncComponent(() => import('../views/Dashboard.vue')),
  SettingsView: defineAsyncComponent(() => import('../views/Settings.vue')),
  TypeManagerView: defineAsyncComponent(() => import('../views/toolkit/TypeManager.vue')),
  CleanupToolsView: defineAsyncComponent(() => import('../views/toolkit/CleanupTools.vue')),
  LockManagerView: defineAsyncComponent(() => import('../views/toolkit/LockManager.vue')),
  EmbyItemQueryView: defineAsyncComponent(() => import('../views/toolkit/EmbyItemQuery.vue')),
  TmdbReverseLookupView: defineAsyncComponent(() => import('../views/toolkit/TmdbReverseLookup.vue')),
  TmdbIdSearchView: defineAsyncComponent(() => import('../views/toolkit/TmdbIdSearch.vue')),
  TmdbLabView: defineAsyncComponent(() => import('../views/toolkit/TmdbLab.vue')),
  BangumiLabView: defineAsyncComponent(() => import('../views/toolkit/BangumiLab.vue')),
  ActorLabView: defineAsyncComponent(() => import('../views/toolkit/ActorLab.vue')),
  ActorManagerView: defineAsyncComponent(() => import('../views/toolkit/ActorManager.vue')),
  WebhookReceiverView: defineAsyncComponent(() => import('../views/toolkit/WebhookReceiver.vue')),
  DedupeView: defineAsyncComponent(() => import('../views/Dedupe.vue')),
  AutoTagsView: defineAsyncComponent(() => import('../views/toolkit/autotags/AutoTagsManager.vue')),
  DockerManagerView: defineAsyncComponent(() => import('../views/toolkit/DockerManager.vue')),
  PostgresManagerView: defineAsyncComponent(() => import('../views/toolkit/PostgresManager.vue')),
  BackupManagerView: defineAsyncComponent(() => import('../views/toolkit/BackupManager.vue')),
  NotificationManagerView: defineAsyncComponent(() => import('../views/toolkit/NotificationManager.vue')),
  ExternalControlView: defineAsyncComponent(() => import('../views/toolkit/ExternalControl.vue')),
  AccountManagerView: defineAsyncComponent(() => import('../views/toolkit/AccountManager.vue')),
  SiteNavView: defineAsyncComponent(() => import('../views/toolkit/sitenav/SiteNav.vue'))
}
