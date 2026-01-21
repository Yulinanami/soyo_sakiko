import { defineStore } from 'pinia';
import { ref } from 'vue';
import { historyApi } from '../services/api';
import type { HistoryItem } from '../types/user_data';
import { useAsyncState } from '../composables/useAsyncState';

type RecordOptions = {
  silent?: boolean;
};

export const useHistoryStore = defineStore('history', () => {
  const items = ref<HistoryItem[]>([]);
  const { loading, error, start, stop, setError } = useAsyncState();
  const loaded = ref(false);

  function setItems(list: HistoryItem[]) {
    // 设置阅读记录
    items.value = list;
    loaded.value = true;
  }

  async function fetchHistory(force = false) {
    // 获取阅读记录
    if (loading.value) return;
    if (loaded.value && !force) return;
    start();
    try {
      const data = await historyApi.getAll();
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载阅读记录失败');
    } finally {
      stop();
    }
  }

  async function recordHistory(payload: Record<string, any>, options: RecordOptions = {}) {
    // 记录阅读进度
    try {
      const item = await historyApi.record(payload);
      if (loaded.value && item) {
        items.value = [
          item,
          ...items.value.filter((existing) => existing.id !== item.id),
        ];
      }
      return item;
    } catch (err) {
      if (!options.silent) {
        setError(err instanceof Error ? err.message : '记录阅读进度失败');
      }
      return null;
    }
  }

  async function removeHistory(id: number, options: RecordOptions = {}) {
    // 删除阅读记录
    try {
      await historyApi.remove(id);
      items.value = items.value.filter((item) => item.id !== id);
    } catch (err) {
      if (!options.silent) {
        setError(err instanceof Error ? err.message : '移除记录失败');
      }
    }
  }

  return {
    items,
    loading,
    error,
    loaded,
    fetchHistory,
    recordHistory,
    removeHistory,
  };
});
