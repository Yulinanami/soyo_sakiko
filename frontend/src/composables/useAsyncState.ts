import { ref } from 'vue';

export function useAsyncState(initialError: string | null = null) {
  const loading = ref(false);
  const error = ref<string | null>(initialError);

  function start() {
    loading.value = true;
    error.value = null;
  }

  function stop() {
    loading.value = false;
  }

  function setError(message: string | null) {
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
