import { defineStore } from 'pinia';
import { ref } from 'vue';
import { favoritesApi } from '../services/api';
import type { Novel } from '../types/novel';

interface FavoriteItem {
  id: number;
  novel_id: string;
  source: string;
  title: string;
  author?: string;
  cover_url?: string;
  source_url?: string;
  created_at: string;
}

const buildKey = (source: string, novelId: string) => `${source}:${novelId}`;

export const useFavoritesStore = defineStore('favorites', () => {
  const items = ref<FavoriteItem[]>([]);
  const loading = ref(false);
  const loaded = ref(false);
  const error = ref<string | null>(null);
  const itemMap = ref<Record<string, FavoriteItem>>({});

  function setItems(list: FavoriteItem[]) {
    items.value = list;
    itemMap.value = {};
    list.forEach((item) => {
      itemMap.value[buildKey(item.source, item.novel_id)] = item;
    });
    loaded.value = true;
  }

  async function fetchFavorites(force = false) {
    if (loading.value) return;
    if (loaded.value && !force) return;
    loading.value = true;
    error.value = null;
    try {
      const data = await favoritesApi.getAll();
      setItems(data);
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载收藏失败';
    } finally {
      loading.value = false;
    }
  }

  function isFavorite(novel: Pick<Novel, 'source' | 'id'>) {
    return Boolean(itemMap.value[buildKey(novel.source, novel.id)]);
  }

  async function addFavorite(novel: Novel) {
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
    const key = buildKey(source, novelId);
    const item = itemMap.value[key];
    if (!item) return;
    await favoritesApi.remove(item.id);
    items.value = items.value.filter((existing) => existing.id !== item.id);
    delete itemMap.value[key];
  }

  async function toggleFavorite(novel: Novel) {
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
    items.value = [];
    itemMap.value = {};
    loaded.value = false;
    error.value = null;
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
