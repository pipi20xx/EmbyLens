import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, uiAuthEnabled } from '@/store/navigationStore'
import { authApi } from '@/api/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
    },
    {
      path: '/dedupe',
      name: 'Dedupe',
      component: () => import('../views/Dedupe.vue'),
    },
    {
      path: '/toolkit/type-manager',
      name: 'TypeManager',
      component: () => import('../views/toolkit/TypeManager.vue'),
    },
    {
      path: '/toolkit/cleanup',
      name: 'Cleanup',
      component: () => import('../views/toolkit/CleanupTools.vue'),
    },
    {
      path: '/toolkit/lock-manager',
      name: 'LockManager',
      component: () => import('../views/toolkit/LockManager.vue'),
    },
    {
      path: '/toolkit/docker-manager',
      name: 'DockerManager',
      component: () => import('../views/toolkit/DockerManager.vue'),
    },
    {
      path: '/toolkit/image-builder',
      name: 'ImageBuilderView',
      component: () => import('../views/toolkit/ImageBuilder.vue'),
    },
    {
      path: '/toolkit/tmdb-lab',
      name: 'TmdbLab',
      component: () => import('../views/toolkit/TmdbLab.vue'),
    },
    {
      path: '/toolkit/bangumi-lab',
      name: 'BangumiLab',
      component: () => import('../views/toolkit/BangumiLab.vue'),
    },
    {
      path: '/toolkit/actor-lab',
      name: 'ActorLab',
      component: () => import('../views/toolkit/ActorLab.vue'),
    },
    {
      path: '/toolkit/terminal',
      name: 'TerminalManager',
      component: () => import('../views/toolkit/terminal/TerminalManager.vue'),
      meta: { title: '终端管理', icon: 'TerminalOutlined' }
    },
    {
      path: '/toolkit/actor-manager',
      name: 'ActorManager',
      component: () => import('../views/toolkit/ActorManager.vue'),
    },
    {
      path: '/toolkit/webhook-receiver',
      name: 'WebhookReceiver',
      component: () => import('../views/toolkit/WebhookReceiver.vue'),
    },
    {
      path: '/toolkit/autotags',
      name: 'AutoTags',
      component: () => import('../views/toolkit/autotags/AutoTagsManager.vue'),
    },
    {
      path: '/toolkit/postgres-manager',
      name: 'PostgresManager',
      component: () => import('../views/toolkit/PostgresManager.vue'),
    },
    {
      path: '/toolkit/backup-manager',
      name: 'BackupManager',
      component: () => import('../views/toolkit/BackupManager.vue'),
    },
    {
      path: '/toolkit/notification-manager',
      name: 'NotificationManager',
      component: () => import('../views/toolkit/NotificationManager.vue'),
    },
    {
      path: '/toolkit/site-nav',
      name: 'SiteNav',
      component: () => import('../views/toolkit/sitenav/SiteManager.vue'),
    },
    {
      path: '/toolkit/bookmark-manager',
      name: 'BookmarkManagerView',
      component: () => import('../views/toolkit/BookmarkManager.vue'),
    },
    {
      path: '/toolkit/external-control',
      name: 'ExternalControl',
      component: () => import('../views/toolkit/ExternalControl.vue'),
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue'),
    }
  ]
})

// 导航守卫
router.beforeEach(async (to, from, next) => {
  // 1. 检查服务器认证状态
  try {
    const data: any = await authApi.getStatus()
    uiAuthEnabled.value = data.ui_auth_enabled === true || data.ui_auth_enabled === 'true'
  } catch (err) { }

  // 2. 鉴权逻辑
  if (uiAuthEnabled.value && !isLoggedIn.value && !to.meta.public) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && (isLoggedIn.value || !uiAuthEnabled.value)) {
    // 如果已经在登录页，但认证已关闭或已登录，则跳回首页
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
