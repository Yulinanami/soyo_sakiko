<script setup lang="ts">
import { ref, watch } from 'vue';
import { useUserStore } from './stores/user';
import { useFavoritesStore } from './stores/favorites';
import { useRouter } from 'vue-router';
import ao3Logo from './assets/ao3.png';
import pixivLogo from './assets/pixiv.png';
import lofterLogo from './assets/lofter.png';
import { Home, Heart, BookOpen, Settings, Menu, Moon, Sun } from 'lucide-vue-next';

const userStore = useUserStore();
const favoritesStore = useFavoritesStore();
const router = useRouter();
const sidebarOpen = ref(true);

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value;
}

function handleLogout() {
  userStore.logout();
  router.push('/');
}

watch(
  () => userStore.isLoggedIn,
  (loggedIn) => {
    if (loggedIn) {
      favoritesStore.fetchFavorites();
    } else {
      favoritesStore.reset();
    }
  },
  { immediate: true }
);
</script>

<template>
  <div id="app" class="min-h-screen flex bg-gray-50 dark:bg-gray-900 dark:text-gray-100 transition-colors duration-300">
    <!-- 左侧边栏 - 祥子淡蓝色 -->
    <aside 
      :class="[
        'fixed left-0 top-0 h-full bg-sakiko-dark dark:bg-slate-900 text-white z-40 transition-all duration-300 flex flex-col shadow-2xl',
        sidebarOpen ? 'w-56' : 'w-0'
      ]"
    >
      <div class="p-4 flex items-center gap-3 border-b border-sakiko dark:border-gray-700">
        <button @click="toggleSidebar" class="text-xl hover:text-white transition-colors">
          <Menu class="w-6 h-6" />
        </button>
        <router-link v-if="sidebarOpen" to="/" class="text-xl font-bold text-white no-underline">
          🎸 SoyoSaki
        </router-link>
      </div>
      
      <nav v-if="sidebarOpen" class="flex-1 p-4 space-y-2">
        <router-link 
          to="/" 
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-sakiko dark:hover:bg-gray-800 no-underline text-white transition-colors"
        >
          <Home class="w-5 h-5" />
          <span>首页</span>
        </router-link>
        
        <router-link 
          to="/favorites" 
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-sakiko dark:hover:bg-gray-800 no-underline text-white transition-colors"
        >
          <Heart class="w-5 h-5" />
          <span>收藏</span>
          <span v-if="!userStore.isLoggedIn" class="text-xs text-white/70">请登录</span>
        </router-link>
        <router-link
          to="/history"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-sakiko dark:hover:bg-gray-800 no-underline text-white transition-colors"
        >
          <BookOpen class="w-5 h-5" />
          <span>阅读记录</span>
          <span v-if="!userStore.isLoggedIn" class="text-xs text-white/70">请登录</span>
        </router-link>

        <router-link
          to="/settings"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-sakiko dark:hover:bg-gray-800 no-underline text-white transition-colors"
        >
          <Settings class="w-5 h-5" />
          <span>设置</span>
        </router-link>

        <button
          @click="userStore.toggleDarkMode()"
          class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-sakiko dark:hover:bg-gray-800 text-white transition-colors text-left cursor-pointer"
        >
          <Moon v-if="!userStore.darkMode" class="w-5 h-5" />
          <Sun v-else class="w-5 h-5" />
          <span>{{ userStore.darkMode ? '切换浅色模式' : '切换深色模式' }}</span>
        </button>
        
        <div class="border-t border-sakiko dark:border-gray-700 my-4"></div>
        
        <div class="text-xs text-sakiko-pale uppercase tracking-wide px-3 mb-2">数据源</div>
        <a href="https://archiveofourown.org/" target="_blank" class="flex items-center gap-3 px-3 py-2.5 text-sm text-white/80 hover:text-white hover:bg-sakiko dark:hover:bg-gray-800 rounded-lg transition-colors no-underline">
          <img :src="ao3Logo" alt="AO3" class="w-5 h-5 object-contain" />
          <span>AO3</span>
        </a>
        <a href="https://www.pixiv.net/" target="_blank" class="flex items-center gap-3 px-3 py-2.5 text-sm text-white/80 hover:text-white hover:bg-sakiko dark:hover:bg-gray-800 rounded-lg transition-colors no-underline">
          <img :src="pixivLogo" alt="Pixiv" class="w-5 h-5 object-contain" />
          <span>Pixiv</span>
        </a>
        <a href="https://www.lofter.com/" target="_blank" class="flex items-center gap-3 px-3 py-2.5 text-sm text-white/80 hover:text-white hover:bg-sakiko dark:hover:bg-gray-800 rounded-lg transition-colors no-underline">
          <img :src="lofterLogo" alt="Lofter" class="w-5 h-5 object-contain" />
          <span>Lofter</span>
        </a>
      </nav>
      
      <!-- 用户区域 -->
      <div v-if="sidebarOpen" class="p-4 border-t border-sakiko dark:border-gray-700">
        <template v-if="userStore.isLoggedIn">
          <div class="flex items-center justify-between">
            <span class="text-sm">{{ userStore.user?.username }}</span>
            <button 
              @click="handleLogout" 
              class="text-xs px-2 py-1 bg-transparent border border-sakiko rounded hover:border-red-400 hover:text-red-400 transition-all"
            >
              登出
            </button>
          </div>
        </template>
        <template v-else>
          <div class="flex gap-2">
            <router-link 
              to="/login" 
              class="flex-1 text-center text-sm py-2 border border-sakiko rounded hover:bg-sakiko no-underline text-white transition-colors"
            >
              登录
            </router-link>
            <router-link 
              to="/register" 
              class="flex-1 text-center text-sm py-2 bg-soyo rounded no-underline text-white hover:bg-soyo-dark transition-colors"
            >
              注册
            </router-link>
          </div>
        </template>
      </div>
    </aside>
    
    <!-- 侧边栏收起时显示的小按钮 -->
    <button 
      v-if="!sidebarOpen"
      @click="toggleSidebar" 
      class="fixed left-0 top-4 z-50 bg-sakiko-dark text-white p-3 rounded-r-lg hover:bg-sakiko transition-colors"
    >
      <Menu class="w-6 h-6" />
    </button>
    
    <!-- 主内容区域 -->
    <main 
      :class="[
        'flex-1 transition-all duration-300',
        sidebarOpen ? 'ml-56' : 'ml-0'
      ]"
    >
      <router-view />
    </main>
  </div>
</template>
