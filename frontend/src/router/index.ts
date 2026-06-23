import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

import LoginView from '@/views/LoginView.vue'
import MenuView from '@/views/MenuView.vue'
import OrderSearchView from '@/views/OrderSearchView.vue'
import OrderDetailView from '@/views/OrderDetailView.vue'
import QuoteOrderView from '@/views/QuoteOrderView.vue'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
  { path: '/', name: 'menu', component: MenuView },
  { path: '/order-search', name: 'order-search', component: OrderSearchView },
  { path: '/order-detail/:orderId', name: 'order-detail', component: OrderDetailView },
  { path: '/quote-order', name: 'quote-order', component: QuoteOrderView },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// 路由守卫：未登录访问受保护页 -> 登录页（等价各 PHP 页的 session 检查）
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) {
    return { name: 'login' }
  }
  if (to.name === 'login' && auth.isLoggedIn) {
    return { name: 'menu' }
  }
  return true
})

export default router
