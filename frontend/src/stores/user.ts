import { defineStore } from 'pinia';
import { computed, ref, watch } from 'vue';
import type { User } from '@app-types/user';
import { authApi, setAuthToken } from '@services/api';
import type { AxiosError } from 'axios';
import { useAsyncState } from '@composables/useAsyncState';

export const useUserStore = defineStore('user', () => {
  // 用户状态
  const user = ref<User | null>(null);
  const token = ref<string | null>(readToken());
  const darkMode = ref<boolean>(readDarkMode());
  const { loading, error, start, stop, setError } = useAsyncState();

  // 登录状态
  const isLoggedIn = computed(() => !!token.value);

  async function login(username: string, password: string) {
    // 执行登录
    start();

    try {
      const response = await authApi.login({ username, password });
      if (!response.accessToken) {
        setError('登录失败，请重试');
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
      setError(axiosError.response?.data?.detail || '登录失败');
      return false;
    } finally {
      stop();
    }
  }

  async function register(username: string, password: string) {
    // 执行注册
    start();

    try {
      const response = await authApi.register({ username, password });
      if (!response.accessToken) {
        setError('注册失败，请重试');
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
      setError(axiosError.response?.data?.detail || '注册失败');
      return false;
    } finally {
      stop();
    }
  }

  async function fetchProfile() {
    // 获取用户信息
    if (!token.value) return;

    try {
      user.value = await authApi.getProfile();
    } catch {
      logout();
    }
  }

  function logout() {
    // 退出登录
    token.value = null;
    user.value = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setAuthToken(null);
  }

  function syncFromStorage() {
    // 读取本地保存的数据
    token.value = readToken();
    const storedUser = readUser();
    if (storedUser) {
      user.value = storedUser;
    }
    setAuthToken(token.value);
  }

  // 有登录信息时补齐数据
  if (token.value) {
    // 根据本地信息补全状态
    const storedUser = readUser();
    if (storedUser) {
      user.value = storedUser;
    }
    setAuthToken(token.value);
    fetchProfile();
  }

  // 监听外观变化
  watch(
    darkMode,
    (isDark) => {
      // 应用外观变化
      if (isDark) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('darkMode', '1');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.removeItem('darkMode');
      }
    },
    { immediate: true }
  );

  function toggleDarkMode() {
    // 切换外观
    darkMode.value = !darkMode.value;
  }

  return {
    user,
    token,
    darkMode,
    loading,
    error,
    isLoggedIn,
    login,
    register,
    logout,
    fetchProfile,
    syncFromStorage,
    toggleDarkMode,
  };
});

function readToken(): string | null {
  // 读取本地登录信息
  const stored = localStorage.getItem('token');
  if (!stored || stored === 'undefined' || stored === 'null') {
    localStorage.removeItem('token');
    return null;
  }
  return stored;
}

function readUser(): User | null {
  // 读取本地用户信息
  const stored = localStorage.getItem('user');
  if (!stored) return null;
  try {
    return JSON.parse(stored) as User;
  } catch {
    localStorage.removeItem('user');
    return null;
  }
}

function readDarkMode(): boolean {
  // 读取外观设置
  return localStorage.getItem('darkMode') === '1';
}
