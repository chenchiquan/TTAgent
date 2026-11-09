import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // 登录页（不走 UserLayout）
  { path: '/login', name: 'login', component: () => import('../views/user/LoginView.vue') },
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    redirect: '/admin/guns',
    children: [
      { path: 'guns', name: 'guns', component: () => import('../views/admin/GunManage.vue') },
      { path: 'ammo', name: 'ammo', component: () => import('../views/admin/AmmoManage.vue') },
      { path: 'attachments', name: 'attachments', component: () => import('../views/admin/AttachmentManage.vue') },
      { path: 'gun-attachments', name: 'gun-attachments', component: () => import('../views/admin/GunAttachmentManage.vue') },
      { path: 'prices', name: 'prices', component: () => import('../views/admin/PriceManage.vue') },
    ]
  },
  {
    path: '/',
    component: () => import('../views/user/UserLayout.vue'),
    redirect: '/',
    children: [
      { path: '', name: 'data', component: () => import('../views/user/DataView.vue') },
      { path: 'chat', name: 'chat', component: () => import('../views/user/ChatView.vue') },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局守卫：未登录跳 /login（登录页本身放行）
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path === '/login') return next()
  if (!token) return next('/login')
  next()
})

export default router
