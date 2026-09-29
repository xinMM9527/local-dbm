import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/workbench',
    },
    {
      path: '/connections',
      name: 'Connections',
      component: () => import('@/views/ConnectionManager.vue'),
    },
    {
      path: '/workbench',
      name: 'Workbench',
      component: () => import('@/views/SqlWorkbench.vue'),
    },
  ],
})

export default router
