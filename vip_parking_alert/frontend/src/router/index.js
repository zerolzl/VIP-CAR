import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '仪表盘' } },
  { path: '/spots', name: 'Spots', component: () => import('../views/Spots.vue'), meta: { title: '车位管理' } },
  { path: '/spots/:id', name: 'SpotDetail', component: () => import('../views/SpotDetail.vue'), meta: { title: '车位详情' } },
  { path: '/contacts', name: 'Contacts', component: () => import('../views/Contacts.vue'), meta: { title: '通讯录' } },
  { path: '/alerts', name: 'Alerts', component: () => import('../views/AlertLogs.vue'), meta: { title: '告警日志' } },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue'), meta: { title: '系统设置' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  document.title = `${to.meta.title} - VIP车位告警系统`
})

export default router
