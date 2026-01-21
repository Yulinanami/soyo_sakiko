import { createRouter, createWebHistory } from 'vue-router';
import { useUserStore } from '../stores/user';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
    },
    {
      path: '/novel/:source/:id',
      name: 'reader',
      component: () => import('../views/ReaderView.vue'),
      props: true,
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
    },
    {
      path: '/favorites',
      name: 'favorites',
      component: () => import('../views/FavoritesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('../views/HistoryView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
    },
  ],
  scrollBehavior(_to, _from, savedPosition) {
    // 处理滚动位置
    if (savedPosition) {
      return savedPosition;
    }
    return { left: 0, top: 0 };
  },
});

function authGuard(to: any) {
  // 判断是否允许进入
  const userStore = useUserStore();
  if (!userStore.token) {
    userStore.syncFromStorage();
  }
  if (to.meta.requiresAuth && !userStore.token) {
    const reason =
      to.name === 'favorites' ? 'favorites' : to.name === 'history' ? 'history' : '';
    return { name: 'login', query: { redirect: to.fullPath, reason } };
  }
  return true;
}

// 注册进入检查
router.beforeEach((to) => authGuard(to));

export default router;
