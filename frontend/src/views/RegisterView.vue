<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../stores/user';

const router = useRouter();
const userStore = useUserStore();

const username = ref('');
const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const localError = ref('');

async function handleRegister() {
  localError.value = '';
  
  if (password.value !== confirmPassword.value) {
    localError.value = '两次输入的密码不一致';
    return;
  }
  
  if (password.value.length < 6) {
    localError.value = '密码长度至少为6位';
    return;
  }
  
  const success = await userStore.register(username.value, email.value, password.value);
  if (success) {
    router.push('/');
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-r from-primary to-secondary p-8">
    <div class="bg-white p-10 rounded-2xl shadow-2xl w-full max-w-md">
      <h1 class="text-center text-2xl font-bold text-gray-800 mb-2">🎸 注册账号</h1>
      <p class="text-center text-gray-600 text-sm mb-8">创建账号以保存收藏和阅读记录</p>
      
      <form @submit.prevent="handleRegister" class="space-y-5">
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
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
          <label for="email" class="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
          <input 
            id="email"
            v-model="email" 
            type="email" 
            placeholder="请输入邮箱"
            required
            class="input"
          />
        </div>
        
        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 mb-2">密码</label>
          <input 
            id="password"
            v-model="password" 
            type="password" 
            placeholder="请输入密码 (至少6位)"
            required
            class="input"
          />
        </div>
        
        <div>
          <label for="confirmPassword" class="block text-sm font-medium text-gray-700 mb-2">确认密码</label>
          <input 
            id="confirmPassword"
            v-model="confirmPassword" 
            type="password" 
            placeholder="请再次输入密码"
            required
            class="input"
          />
        </div>
        
        <div v-if="localError || userStore.error" class="bg-red-50 text-red-500 p-3 rounded-lg text-sm">
          {{ localError || userStore.error }}
        </div>
        
        <button type="submit" class="w-full btn-primary" :disabled="userStore.loading">
          {{ userStore.loading ? '注册中...' : '注册' }}
        </button>
      </form>
      
      <p class="text-center mt-6 text-gray-600">
        已有账号？<router-link to="/login" class="text-primary font-medium hover:underline">立即登录</router-link>
      </p>
    </div>
  </div>
</template>
