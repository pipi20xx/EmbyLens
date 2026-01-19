import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('../views/Layout.vue'),
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('../views/Dashboard.vue'),
        },
        {
          path: 'dedupe',
          name: 'Dedupe',
          component: () => import('../views/Dedupe.vue'),
        },
        {
          path: 'toolkit/type-manager',
          name: 'TypeManager',
          component: () => import('../views/toolkit/TypeManager.vue'),
        },
        {
          path: 'toolkit/cleanup',
          name: 'Cleanup',
          component: () => import('../views/toolkit/CleanupTools.vue'),
        },
        {
          path: 'toolkit/lock-manager',
          name: 'LockManager',
          component: () => import('../views/toolkit/LockManager.vue'),
        },
        {
          path: 'toolkit/docker-manager',
          name: 'DockerManager',
          component: () => import('../views/toolkit/DockerManager.vue'),
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('../views/Settings.vue'),
        }
      ]
    }
  ]
})

export default router
