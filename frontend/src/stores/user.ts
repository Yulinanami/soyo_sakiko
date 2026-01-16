import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '../types/user';
import { authApi, setAuthToken } from '../services/api';
import type { AxiosError } from 'axios';

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null);
  const token = ref<string | null>(readToken());
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Computed
  const isLoggedIn = computed(() => !!token.value);

  // Actions
  async function login(username: string, password: string) {
    loading.value = true;
    error.value = null;

    try {
      const response = await authApi.login({ username, password });
      if (!response.accessToken) {
        error.value = '登录失败，请重试';
        return false;
      }
      token.value = response.accessToken;
      user.value = response.user;
      localStorage.setItem('token', response.accessToken);
      localStorage.setItem('user', JSON.stringify(response.user));
      setAuthToken(response.accessToken);
      return true;
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      error.value = axiosError.response?.data?.detail || '登录失败';
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function register(username: string, password: string) {
    loading.value = true;
    error.value = null;

    try {
      const response = await authApi.register({ username, password });
      if (!response.accessToken) {
        error.value = '注册失败，请重试';
        return false;
      }
      token.value = response.accessToken;
      user.value = response.user;
      localStorage.setItem('token', response.accessToken);
      localStorage.setItem('user', JSON.stringify(response.user));
      setAuthToken(response.accessToken);
      return true;
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      error.value = axiosError.response?.data?.detail || '注册失败';
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
    localStorage.removeItem('user');
    setAuthToken(null);
  }

  function syncFromStorage() {
    token.value = readToken();
    const storedUser = readUser();
    if (storedUser) {
      user.value = storedUser;
    }
    setAuthToken(token.value);
  }

  // Initialize: fetch profile if token exists
  if (token.value) {
    const storedUser = readUser();
    if (storedUser) {
      user.value = storedUser;
    }
    setAuthToken(token.value);
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
    syncFromStorage,
  };
});

function readToken(): string | null {
  const stored = localStorage.getItem('token');
  if (!stored || stored === 'undefined' || stored === 'null') {
    localStorage.removeItem('token');
    return null;
  }
  return stored;
}

function readUser(): User | null {
  const stored = localStorage.getItem('user');
  if (!stored) return null;
  try {
    return JSON.parse(stored) as User;
  } catch {
    localStorage.removeItem('user');
    return null;
  }
}
