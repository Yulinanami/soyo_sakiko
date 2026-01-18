<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '../stores/user';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const username = ref('');
const password = ref('');
const loginReason = computed(() => {
  if (route.query.reason === 'favorites') {
    return '请登录以查看收藏';
  }
  if (route.query.reason === 'history') {
    return '请登录以查看阅读记录';
  }
  return '';
});


async function handleLogin() {
  const success = await userStore.login(username.value, password.value);
  if (success) {
    const redirect = route.query.redirect as string || '/';
    router.push(redirect);
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-linear-to-r from-primary to-secondary p-8 dark:from-gray-900 dark:to-gray-800 transition-colors duration-300">
    <div class="bg-white p-10 rounded-2xl shadow-2xl w-full max-w-md dark:bg-gray-800 dark:shadow-none transition-colors duration-300">
      <h1 class="text-center text-2xl font-bold text-gray-800 mb-2 dark:text-white">🎸 登录</h1>
      <p class="text-center text-gray-600 text-sm mb-4 dark:text-gray-400">登录以使用收藏和阅读记录功能</p>
      <p v-if="loginReason" class="text-center text-sm text-orange-600 mb-6 dark:text-orange-400">
        {{ loginReason }}
      </p>
      
      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700 mb-2 dark:text-gray-300">用户名</label>
          <input 
            id="username"
            v-model="username" 
            type="text" 
            placeholder="请输入用户名"
            required
            class="input"
          />
        </div>
        
        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 mb-2 dark:text-gray-300">密码</label>
          <input 
            id="password"
            v-model="password" 
            type="password" 
            placeholder="请输入密码"
            required
            class="input"
          />
        </div>
        
        <div v-if="userStore.error" class="bg-red-50 text-red-500 p-3 rounded-lg text-sm dark:bg-red-900/20 dark:text-red-400">
          {{ userStore.error }}
        </div>
        
        <button type="submit" class="w-full btn-primary" :disabled="userStore.loading">
          {{ userStore.loading ? '登录中...' : '登录' }}
        </button>
      </form>
      
      <p class="text-center mt-6 text-gray-600 dark:text-gray-400">
        还没有账号？<router-link to="/register" class="text-primary font-medium hover:underline dark:text-primary-light">立即注册</router-link>
      </p>
    </div>
  </div>
</template>
