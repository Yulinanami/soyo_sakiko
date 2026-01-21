import { defineStore } from 'pinia';
import { ref } from 'vue';
import { favoritesApi } from '../services/api';
import type { Novel } from '../types/novel';
import type { FavoriteItem } from '../types/user_data';
import { useAsyncState } from '../composables/useAsyncState';

// 生成唯一标识
const buildKey = (source: string, novelId: string) => `${source}:${novelId}`;

export const useFavoritesStore = defineStore('favorites', () => {
  const items = ref<FavoriteItem[]>([]);
  const { loading, error, start, stop, setError } = useAsyncState();
  const loaded = ref(false);
  const itemMap = ref<Record<string, FavoriteItem>>({});

  function setItems(list: FavoriteItem[]) {
    // 设置收藏列表
    items.value = list;
    itemMap.value = {};
    list.forEach((item) => {
      itemMap.value[buildKey(item.source, item.novel_id)] = item;
    });
    loaded.value = true;
  }

  async function fetchFavorites(force = false) {
    // 获取收藏列表
    if (loading.value) return;
    if (loaded.value && !force) return;
    start();
    try {
      const data = await favoritesApi.getAll();
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载收藏失败');
    } finally {
      stop();
    }
  }

  function isFavorite(novel: Pick<Novel, 'source' | 'id'>) {
    // 判断是否已收藏
    return Boolean(itemMap.value[buildKey(novel.source, novel.id)]);
  }

  async function addFavorite(novel: Novel) {
    // 添加收藏
    const payload = {
      novel_id: novel.id,
      source: novel.source,
      title: novel.title,
      author: novel.author,
      cover_url: novel.cover_image,
      source_url: novel.source_url,
    };
    const item = await favoritesApi.add(payload);
    items.value = [item, ...items.value.filter((existing) => existing.id !== item.id)];
    itemMap.value[buildKey(item.source, item.novel_id)] = item;
    return item;
  }

  async function removeFavoriteByKey(source: string, novelId: string) {
    // 移除收藏
    const key = buildKey(source, novelId);
    const item = itemMap.value[key];
    if (!item) return;
    await favoritesApi.remove(item.id);
    items.value = items.value.filter((existing) => existing.id !== item.id);
    delete itemMap.value[key];
  }

  async function toggleFavorite(novel: Novel) {
    // 切换收藏状态
    if (!loaded.value) {
      await fetchFavorites();
    }
    const key = buildKey(novel.source, novel.id);
    if (itemMap.value[key]) {
      await removeFavoriteByKey(novel.source, novel.id);
      return false;
    }
    await addFavorite(novel);
    return true;
  }

  function reset() {
    // 清空收藏数据
    items.value = [];
    itemMap.value = {};
    loaded.value = false;
    setError(null);
  }

  return {
    items,
    loading,
    loaded,
    error,
    fetchFavorites,
    isFavorite,
    toggleFavorite,
    removeFavoriteByKey,
    reset,
  };
});
