import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '../types/user';
import { authApi } from '../services/api';

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem('token'));
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Computed
  const isLoggedIn = computed(() => !!token.value && !!user.value);

  // Actions
  async function login(username: string, password: string) {
    loading.value = true;
    error.value = null;

    try {
      const response = await authApi.login({ username, password });
      token.value = response.accessToken;
      user.value = response.user;
      localStorage.setItem('token', response.accessToken);
      return true;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '登录失败';
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function register(username: string, email: string, password: string) {
    loading.value = true;
    error.value = null;

    try {
      const response = await authApi.register({ username, email, password });
      token.value = response.accessToken;
      user.value = response.user;
      localStorage.setItem('token', response.accessToken);
      return true;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '注册失败';
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function fetchProfile() {
    if (!token.value) return;

    try {
      user.value = await authApi.getProfile();
    } catch {
      logout();
    }
  }

  function logout() {
    token.value = null;
    user.value = null;
    localStorage.removeItem('token');
  }

  // Initialize: fetch profile if token exists
  if (token.value) {
    fetchProfile();
  }

  return {
    // State
    user,
    token,
    loading,
    error,
    // Computed
    isLoggedIn,
    // Actions
    login,
    register,
    logout,
    fetchProfile,
  };
});
