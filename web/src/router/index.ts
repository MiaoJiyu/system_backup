import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/',
    component: AppLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: '仪表盘', requiresAuth: true },
      },
      {
        path: 'clients',
        name: 'Clients',
        component: () => import('@/views/ClientsView.vue'),
        meta: { title: '客户端管理', requiresAuth: true },
      },
      {
        path: 'clients/:id',
        name: 'ClientDetail',
        component: () => import('@/views/ClientDetailView.vue'),
        meta: { title: '客户端详情', requiresAuth: true },
      },
      {
        path: 'groups',
        name: 'Groups',
        component: () => import('@/views/GroupsView.vue'),
        meta: { title: '分组管理', requiresAuth: true },
      },
      {
        path: 'policies',
        name: 'Policies',
        component: () => import('@/views/PoliciesView.vue'),
        meta: { title: '策略模板', requiresAuth: true },
      },
      {
        path: 'storages',
        name: 'Storages',
        component: () => import('@/views/StoragesView.vue'),
        meta: { title: '存储后端', requiresAuth: true },
      },
      {
        path: 'versions',
        name: 'Versions',
        component: () => import('@/views/VersionsView.vue'),
        meta: { title: '版本管理', requiresAuth: true },
      },
      {
        path: 'system',
        name: 'System',
        component: () => import('@/views/SystemView.vue'),
        meta: { title: '系统设置', requiresAuth: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
