import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Novel, NovelSearchParams, NovelSource } from '@app-types/novel';
import { novelApi } from '@services/api';

export const useNovelsStore = defineStore('novels', () => {
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
    bilibili: [],
  });
  const hasMoreBySource = ref<Record<NovelSource, boolean>>({
    ao3: false,
    pixiv: false,
    lofter: false,
    bilibili: false,
  });
  const loadingSources = ref<Record<NovelSource, boolean>>({
    ao3: false,
    pixiv: false,
    lofter: false,
    bilibili: false,
  });
  let requestId = 0;

  const selectedSources = ref<NovelSource[]>(['ao3']);
  const selectedTags = ref<string[]>(['素祥', '祥素']);
  const excludeTags = ref<string[]>([
    'all祥', '祥睦', '睦祥', '祥希', '希祥', '要乐奈', 
    '素爱', '祥爱', '爱祥', '祥初', '祥灯', '高松灯', 
    '千早爱音', '三角初华', '海祥', '灯祥', '初祥', 'ansy', '爱素'
  ]);
  const sortBy = ref<'date' | 'kudos' | 'hits' | 'wordCount'>('date');

  // 判断是否为空
  const isEmpty = computed(() => novels.value.length === 0 && !loading.value);

  async function fetchNovels(reset = false) {
    // 获取小说列表
    requestId += 1;
    const activeRequestId = requestId;

    if (reset) {
      currentPage.value = 1;
      novels.value = [];
      selectedSources.value.forEach(source => {
        novelsBySource.value[source] = [];
        hasMoreBySource.value[source] = false;
      });
    }

    if (selectedSources.value.length === 0) {
      error.value = null;
      hasMore.value = false;
      loading.value = false;
      loadingSources.value = { ao3: false, pixiv: false, lofter: false, bilibili: false };
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
      // 更新合并结果
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
    // 加载更多
    if (loading.value || !hasMore.value || selectedSources.value.length === 0) return;
    currentPage.value++;
    await fetchNovels(false);
  }

  async function fetchSourcesWithCache() {
    // 补齐来源结果
    rebuildNovels();
    
    const sourcesToFetch = selectedSources.value.filter(
      source => novelsBySource.value[source].length === 0
    );
    
    if (sourcesToFetch.length === 0) {
      hasMore.value = selectedSources.value.some(source => hasMoreBySource.value[source]);
      return;
    }
    
    sourcesToFetch.forEach(source => {
      loadingSources.value[source] = true;
    });
    loading.value = true;
    
    const baseParams = {
      tags: selectedTags.value,
      excludeTags: excludeTags.value,
      page: 1,
      pageSize,
      sortBy: sortBy.value,
    };
    
    await Promise.allSettled(
      sourcesToFetch.map(async (source) => {
        try {
          const response = await novelApi.search({
            ...baseParams,
            sources: [source],
          });
          const filtered = response.novels.filter(n => n.source === source);
          novelsBySource.value[source] = filtered;
          hasMoreBySource.value[source] = response.has_more;
          rebuildNovels();
        } catch (err) {
          error.value = err instanceof Error ? err.message : '获取小说列表失败';
        } finally {
          loadingSources.value[source] = false;
          loading.value = selectedSources.value.some(s => loadingSources.value[s]);
          hasMore.value = selectedSources.value.some(s => hasMoreBySource.value[s]);
        }
      })
    );
  }

  function retry() {
    // 重试加载
    error.value = null;
    fetchNovels(false);
  }

  function rebuildNovels() {
    // 重新组合列表
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
    novels,
    loading,
    error,
    currentPage,
    hasMore,
    selectedSources,
    selectedTags,
    excludeTags,
    sortBy,
    loadingSources,
    isEmpty,
    fetchNovels,
    fetchSourcesWithCache,
    loadMore,
    retry,
  };
});
