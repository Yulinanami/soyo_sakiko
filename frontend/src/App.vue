<script setup lang="ts">
import { useUserStore } from './stores/user';
import { useRouter } from 'vue-router';

const userStore = useUserStore();
const router = useRouter();

function handleLogout() {
  userStore.logout();
  router.push('/');
}
</script>

<template>
  <div id="app" class="min-h-screen">
    <!-- Global Navigation -->
    <nav class="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <router-link to="/" class="text-xl font-bold text-soyo-dark no-underline">
          🎸 SoyoSaki
        </router-link>
        
        <div class="flex items-center gap-6">
          <router-link 
            to="/" 
            class="text-gray-600 font-medium hover:text-primary transition-colors no-underline"
          >
            首页
          </router-link>
          
          <template v-if="userStore.isLoggedIn">
            <router-link 
              to="/favorites" 
              class="text-gray-600 font-medium hover:text-primary transition-colors no-underline"
            >
              收藏
            </router-link>
            <div class="flex items-center gap-4">
              <span class="text-gray-600">{{ userStore.user?.username }}</span>
              <button 
                @click="handleLogout" 
                class="px-3 py-1.5 bg-transparent border border-gray-300 rounded-md text-sm cursor-pointer 
                       hover:border-red-500 hover:text-red-500 transition-all"
              >
                登出
              </button>
            </div>
          </template>
          
          <template v-else>
            <router-link 
              to="/login" 
              class="text-gray-600 font-medium hover:text-primary transition-colors no-underline"
            >
              登录
            </router-link>
            <router-link 
              to="/register" 
              class="px-4 py-2 bg-soyo text-white font-medium rounded-lg no-underline hover:bg-soyo-dark transition-colors"
            >
              注册
            </router-link>
          </template>
        </div>
      </div>
    </nav>
    
    <!-- Main Content -->
    <router-view />
  </div>
</template>

