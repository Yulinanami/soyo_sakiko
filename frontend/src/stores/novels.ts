import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Novel, NovelSearchParams, NovelSource } from '../types/novel';
import { novelApi } from '../services/api';

export const useNovelsStore = defineStore('novels', () => {
  // State
  const novels = ref<Novel[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const currentPage = ref(1);
  const pageSize = ref(30);
  const total = ref(0);
  const hasMore = ref(true);

  // Filters
  const selectedSources = ref<NovelSource[]>(['ao3']);
  const selectedTags = ref<string[]>(['素祥', '祥素']);
  const excludeTags = ref<string[]>(['爱素', '愛素', '素爱', '素愛']);  // Default exclude tags
  const sortBy = ref<'date' | 'kudos' | 'hits' | 'wordCount'>('date');
  const sortOrder = ref<'asc' | 'desc'>('desc');

  // Computed
  const isEmpty = computed(() => novels.value.length === 0 && !loading.value);

  // Actions
  async function fetchNovels(reset = false) {
    if (reset) {
      currentPage.value = 1;
      novels.value = [];
    }

    if (selectedSources.value.length === 0) {
      error.value = null;
      total.value = 0;
      hasMore.value = false;
      loading.value = false;
      return;
    }

    if (selectedTags.value.length === 0) {
      error.value = '请先选择至少一个标签';
      total.value = 0;
      hasMore.value = false;
      loading.value = false;
      novels.value = [];
      return;
    }

    loading.value = true;
    error.value = null;

    try {
      const params: NovelSearchParams = {
        sources: selectedSources.value,
        tags: selectedTags.value,
        excludeTags: excludeTags.value,
        page: currentPage.value,
        pageSize: pageSize.value,
        sortBy: sortBy.value,
        sortOrder: sortOrder.value,
      };

      const response = await novelApi.search(params);
      const allowedSources = new Set(selectedSources.value);
      const filteredNovels = response.novels.filter(n => allowedSources.has(n.source));
      
      if (reset) {
        novels.value = filteredNovels;
      } else {
        // Deduplicate: only add novels that don't already exist
        const existingIds = new Set(novels.value.map(n => `${n.source}:${n.id}`));
        const newNovels = filteredNovels.filter(n => !existingIds.has(`${n.source}:${n.id}`));
        novels.value.push(...newNovels);
      }
      
      total.value = response.total;
      hasMore.value = response.has_more;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取小说列表失败';
    } finally {
      loading.value = false;
    }
  }

  async function loadMore() {
    if (loading.value || !hasMore.value) return;
    currentPage.value++;
    await fetchNovels(false);
  }

  function setFilters(sources: NovelSource[], tags: string[]) {
    selectedSources.value = sources;
    selectedTags.value = tags;
    fetchNovels(true);
  }

  function setSort(by: typeof sortBy.value, order: typeof sortOrder.value) {
    sortBy.value = by;
    sortOrder.value = order;
    fetchNovels(true);
  }

  return {
    // State
    novels,
    loading,
    error,
    currentPage,
    total,
    hasMore,
    selectedSources,
    selectedTags,
    excludeTags,  // Export for UI
    sortBy,
    sortOrder,
    // Computed
    isEmpty,
    // Actions
    fetchNovels,
    loadMore,
    setFilters,
    setSort,
  };
});
