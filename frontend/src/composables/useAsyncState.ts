import { ref } from 'vue';

export function useAsyncState(initialError: string | null = null) {
  // 创建通用状态
  const loading = ref(false);
  const error = ref<string | null>(initialError);

  function start() {
    // 开始加载
    loading.value = true;
    error.value = null;
  }

  function stop() {
    // 结束加载
    loading.value = false;
  }

  function setError(message: string | null) {
    // 记录错误信息
    error.value = message;
  }

  return {
    loading,
    error,
    start,
    stop,
    setError,
  };
}
