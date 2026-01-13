<script setup lang="ts">
import { ref } from 'vue';
import { useUserStore } from './stores/user';
import { useRouter } from 'vue-router';

const userStore = useUserStore();
const router = useRouter();
const sidebarOpen = ref(true);

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value;
}

function handleLogout() {
  userStore.logout();
  router.push('/');
}
</script>

<template>
  <div id="app" class="min-h-screen flex bg-gray-50">
    <!-- 左侧边栏 - 祥子淡蓝色 -->
    <aside 
      :class="[
        'fixed left-0 top-0 h-full bg-sakiko-dark text-white z-40 transition-all duration-300 flex flex-col',
        sidebarOpen ? 'w-56' : 'w-0'
      ]"
    >
      <div class="p-4 flex items-center gap-3 border-b border-sakiko">
        <button @click="toggleSidebar" class="text-xl hover:text-white transition-colors">
          ☰
        </button>
        <router-link v-if="sidebarOpen" to="/" class="text-xl font-bold text-white no-underline">
          🎸 SoyoSaki
        </router-link>
      </div>
      
      <nav v-if="sidebarOpen" class="flex-1 p-4 space-y-2">
        <router-link 
          to="/" 
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-sakiko no-underline text-white transition-colors"
        >
          <span>🏠</span>
          <span>首页</span>
        </router-link>
        
        <template v-if="userStore.isLoggedIn">
          <router-link 
            to="/favorites" 
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-sakiko no-underline text-white transition-colors"
          >
            <span>❤️</span>
            <span>我的收藏</span>
          </router-link>
        </template>
        
        <div class="border-t border-sakiko my-4"></div>
        
        <div class="text-xs text-sakiko-pale uppercase tracking-wide px-3 mb-2">数据源</div>
        <div class="flex items-center gap-3 px-3 py-2 text-sm text-white/80">
          <span>📚</span>
          <span>AO3</span>
        </div>
        <div class="flex items-center gap-3 px-3 py-2 text-sm text-white/80">
          <span>🎨</span>
          <span>Pixiv</span>
        </div>
        <div class="flex items-center gap-3 px-3 py-2 text-sm text-white/50">
          <span>📝</span>
          <span>Lofter (开发中)</span>
        </div>
      </nav>
      
      <!-- 用户区域 -->
      <div v-if="sidebarOpen" class="p-4 border-t border-sakiko">
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
      ☰
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
