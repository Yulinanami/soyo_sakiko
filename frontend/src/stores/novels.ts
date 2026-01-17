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
  const pageSize = 30;
  const hasMore = ref(true);
  const novelsBySource = ref<Record<NovelSource, Novel[]>>({
    ao3: [],
    pixiv: [],
    lofter: [],
  });
  const hasMoreBySource = ref<Record<NovelSource, boolean>>({
    ao3: false,
    pixiv: false,
    lofter: false,
  });
  const loadingSources = ref<Record<NovelSource, boolean>>({
    ao3: false,
    pixiv: false,
    lofter: false,
  });
  let requestId = 0;

  // Filters
  const selectedSources = ref<NovelSource[]>(['ao3']);
  const selectedTags = ref<string[]>(['素祥', '祥素']);
  const excludeTags = ref<string[]>(['爱素', '愛素', '素爱', '素愛']);  // Default exclude tags
  const sortBy = ref<'date' | 'kudos' | 'hits' | 'wordCount'>('date');

  // Computed
  const isEmpty = computed(() => novels.value.length === 0 && !loading.value);

  // Actions
  async function fetchNovels(reset = false) {
    requestId += 1;
    const activeRequestId = requestId;

    if (reset) {
      currentPage.value = 1;
      novels.value = [];
      novelsBySource.value = { ao3: [], pixiv: [], lofter: [] };
      hasMoreBySource.value = { ao3: false, pixiv: false, lofter: false };
    }

    if (selectedSources.value.length === 0) {
      error.value = null;
      hasMore.value = false;
      loading.value = false;
      loadingSources.value = { ao3: false, pixiv: false, lofter: false };
      return;
    }

    if (selectedTags.value.length === 0) {
      error.value = '请先选择至少一个标签';
      hasMore.value = false;
      loading.value = false;
      novels.value = [];
      selectedSources.value.forEach((source) => {
        loadingSources.value[source] = false;
      });
      return;
    }

    selectedSources.value.forEach(source => {
      loadingSources.value[source] = true;
    });
    loading.value = true;
    error.value = null;

    const updateAggregates = () => {
      rebuildNovels();
      hasMore.value = selectedSources.value.some(source => hasMoreBySource.value[source]);
      loading.value = selectedSources.value.some(source => loadingSources.value[source]);
    };

    try {
      const baseParams: Omit<NovelSearchParams, 'sources'> = {
        tags: selectedTags.value,
        excludeTags: excludeTags.value,
        page: currentPage.value,
        pageSize,
        sortBy: sortBy.value,
      };

      await Promise.allSettled(
        selectedSources.value.map(async (source) => {
          const params: NovelSearchParams = {
            ...baseParams,
            sources: [source],
          };

          try {
            const response = await novelApi.search(params);
            if (activeRequestId !== requestId) {
              return;
            }
            const filtered = response.novels.filter(n => n.source === source);
            if (reset) {
              novelsBySource.value[source] = filtered;
            } else {
              const existingIds = new Set(
                novelsBySource.value[source].map(n => `${n.source}:${n.id}`)
              );
              const newNovels = filtered.filter(n => !existingIds.has(`${n.source}:${n.id}`));
              novelsBySource.value[source].push(...newNovels);
            }
            hasMoreBySource.value[source] = response.has_more;
            updateAggregates();
          } catch (err) {
            if (activeRequestId === requestId) {
              error.value = err instanceof Error ? err.message : '获取小说列表失败';
            }
          } finally {
            if (activeRequestId === requestId) {
              loadingSources.value[source] = false;
              updateAggregates();
            }
          }
        })
      );
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取小说列表失败';
    } finally {
      if (activeRequestId === requestId) {
        selectedSources.value.forEach((source) => {
          loadingSources.value[source] = false;
        });
        loading.value = false;
      }
    }
  }

  async function loadMore() {
    if (loading.value || !hasMore.value || selectedSources.value.length === 0) return;
    currentPage.value++;
    await fetchNovels(false);
  }

  function rebuildNovels() {
    const combined: Novel[] = [];
    const seen = new Set<string>();
    const sourceOrder = selectedSources.value.length
      ? selectedSources.value
      : (Object.keys(novelsBySource.value) as NovelSource[]);
    const maxLen = Math.max(
      0,
      ...sourceOrder.map(source => novelsBySource.value[source]?.length || 0)
    );
    for (let i = 0; i < maxLen; i += 1) {
      for (const source of sourceOrder) {
        const list = novelsBySource.value[source] || [];
        if (i >= list.length) continue;
        const novel = list[i];
        if (!novel) continue;
        const key = `${novel.source}:${novel.id}`;
        if (seen.has(key)) continue;
        seen.add(key);
        combined.push(novel);
      }
    }
    novels.value = combined;
  }

  return {
    // State
    novels,
    loading,
    error,
    currentPage,
    hasMore,
    selectedSources,
    selectedTags,
    excludeTags,  // Export for UI
    sortBy,
    loadingSources,
    // Computed
    isEmpty,
    // Actions
    fetchNovels,
    loadMore,
  };
});
