import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { Novel, NovelSearchParams, NovelSource } from "@app-types/novel";
import { novelApi, tagConfigApi } from "@services/api";
import { useUserStore } from "@stores/user";

export const useNovelsStore = defineStore("novels", () => {
  const novels = ref<Novel[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const currentPage = ref(1);
  const pageSize = 30;
  const hasMore = ref(true);
  // 记录每一页的起始位置（用于显示分隔线）
  const pageBreaks = ref<number[]>([]);
  // 按页存储每个源的结果，解决多源分页交叉问题
  const novelsBySourceByPage = ref<
    Record<NovelSource, Record<number, Novel[]>>
  >({
    ao3: {},
    pixiv: {},
    lofter: {},
    bilibili: {},
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

  const activeConfigSource = ref<NovelSource>("ao3");
  const selectedSources = ref<NovelSource[]>(["ao3"]);

  // 每个源独立的标签配置
  const commonExclusion = [
    "all祥",
    "祥睦",
    "睦祥",
    "祥希",
    "希祥",
    "要乐奈",
    "素爱",
    "祥爱",
    "爱祥",
    "祥初",
    "祥灯",
    "高松灯",
    "千早爱音",
    "三角初华",
    "海祥",
    "灯祥",
    "初祥",
    "ansy",
    "爱素",
  ];

  // 默认标签配置（用于重置）
  const defaultTagsBySource: Record<NovelSource, string[]> = {
    ao3: ["素祥", "祥素", "Nagasaki Soyo/Togawa Sakiko"],
    pixiv: ["素祥", "祥素", "そよさき"],
    lofter: ["素祥"],
    bilibili: ["素祥"],
  };

  const defaultExcludeTagsBySource: Record<NovelSource, string[]> = {
    ao3: [...commonExclusion],
    pixiv: [...commonExclusion],
    lofter: [...commonExclusion],
    bilibili: [...commonExclusion],
  };

  const tagsBySource = ref<Record<NovelSource, string[]>>({
    ...defaultTagsBySource,
  });

  const excludeTagsBySource = ref<Record<NovelSource, string[]>>({
    ...defaultExcludeTagsBySource,
  });

  const sortBy = ref<"date" | "kudos" | "hits" | "wordCount">("date");

  // 判断是否为空
  const isEmpty = computed(() => novels.value.length === 0 && !loading.value);

  async function fetchNovels(reset = false, specificSources?: NovelSource[]) {
    // 获取小说列表
    requestId += 1;
    const activeRequestId = requestId;

    const sourcesToProcess = specificSources || selectedSources.value;

    if (reset) {
      currentPage.value = 1;
      pageBreaks.value = []; // 重置时清空分页记录
      if (!specificSources) {
        novels.value = [];
      }
      sourcesToProcess.forEach((source) => {
        novelsBySourceByPage.value[source] = {};
        hasMoreBySource.value[source] = false;
      });
    } else {
      // 加载更多时，记录当前位置作为新页的起点
      const currentCount = novels.value.length;
      if (currentCount > 0 && !pageBreaks.value.includes(currentCount)) {
        pageBreaks.value.push(currentCount);
      }
    }

    if (sourcesToProcess.length === 0) {
      error.value = null;
      hasMore.value = false;
      loading.value = false;
      loadingSources.value = {
        ao3: false,
        pixiv: false,
        lofter: false,
        bilibili: false,
      };
      return;
    }

    // 检查处理的源是否有标签
    const sourcesWithNoTags = sourcesToProcess.filter(
      (s) => tagsBySource.value[s].length === 0,
    );
    if (sourcesWithNoTags.length === sourcesToProcess.length) {
      error.value = "请先选择至少一个标签";
      hasMore.value = false;
      loading.value = false;
      if (!specificSources) {
        novels.value = [];
      }
      sourcesToProcess.forEach((source) => {
        loadingSources.value[source] = false;
      });
      return;
    }

    sourcesToProcess.forEach((source) => {
      loadingSources.value[source] = true;
    });
    loading.value = true;
    error.value = null;

    const updateAggregates = () => {
      // 更新合并结果
      rebuildNovels();
      hasMore.value = selectedSources.value.some(
        (source) => hasMoreBySource.value[source],
      );
      loading.value = selectedSources.value.some(
        (source) => loadingSources.value[source],
      );
    };

    try {
      await Promise.allSettled(
        sourcesToProcess.map(async (source) => {
          const params: NovelSearchParams = {
            sources: [source],
            tags: tagsBySource.value[source],
            excludeTags: excludeTagsBySource.value[source],
            page: currentPage.value,
            pageSize,
            sortBy: sortBy.value,
          };

          try {
            const response = await novelApi.search(params);
            if (activeRequestId !== requestId) {
              return;
            }
            const filtered = response.novels.filter((n) => n.source === source);
            // 按页存储结果，确保每页独立交叉
            const page = currentPage.value;
            novelsBySourceByPage.value[source][page] = filtered;
            hasMoreBySource.value[source] = response.has_more;
            updateAggregates();
          } catch (err) {
            if (activeRequestId === requestId) {
              error.value =
                err instanceof Error ? err.message : "获取小说列表失败";
            }
          } finally {
            if (activeRequestId === requestId) {
              loadingSources.value[source] = false;
              updateAggregates();
            }
          }
        }),
      );
    } catch (err) {
      error.value = err instanceof Error ? err.message : "获取小说列表失败";
    } finally {
      if (activeRequestId === requestId) {
        sourcesToProcess.forEach((source) => {
          loadingSources.value[source] = false;
        });
        loading.value = false;
      }
    }
  }

  async function loadMore() {
    // 加载更多
    if (loading.value || !hasMore.value || selectedSources.value.length === 0)
      return;
    currentPage.value++;
    await fetchNovels(false);
  }

  async function fetchSourcesWithCache() {
    // 补齐来源结果
    rebuildNovels();

    const sourcesToFetch = selectedSources.value.filter(
      (source) => Object.keys(novelsBySourceByPage.value[source]).length === 0,
    );

    if (sourcesToFetch.length === 0) {
      hasMore.value = selectedSources.value.some(
        (source) => hasMoreBySource.value[source],
      );
      return;
    }

    sourcesToFetch.forEach((source) => {
      loadingSources.value[source] = true;
    });
    loading.value = true;

    await Promise.allSettled(
      sourcesToFetch.map(async (source) => {
        try {
          const response = await novelApi.search({
            sources: [source],
            tags: tagsBySource.value[source],
            excludeTags: excludeTagsBySource.value[source],
            page: 1,
            pageSize,
            sortBy: sortBy.value,
          });
          const filtered = response.novels.filter((n) => n.source === source);
          // 按页存储，新源从第1页开始
          novelsBySourceByPage.value[source][1] = filtered;
          hasMoreBySource.value[source] = response.has_more;
          rebuildNovels();
        } catch (err) {
          error.value = err instanceof Error ? err.message : "获取小说列表失败";
        } finally {
          loadingSources.value[source] = false;
          loading.value = selectedSources.value.some(
            (s) => loadingSources.value[s],
          );
          hasMore.value = selectedSources.value.some(
            (s) => hasMoreBySource.value[s],
          );
        }
      }),
    );
  }

  function retry() {
    // 重试加载
    error.value = null;
    fetchNovels(false);
  }

  function rebuildNovels() {
    // 按页交叉排列，解决多源分页交叉问题
    const combined: Novel[] = [];
    const seen = new Set<string>();
    const sourceOrder = selectedSources.value.length
      ? selectedSources.value
      : (Object.keys(novelsBySourceByPage.value) as NovelSource[]);

    // 获取所有页码并排序
    const allPages = new Set<number>();
    for (const source of sourceOrder) {
      const pages = novelsBySourceByPage.value[source];
      if (pages) {
        Object.keys(pages).forEach((p) => allPages.add(Number(p)));
      }
    }
    const sortedPages = Array.from(allPages).sort((a, b) => a - b);

    // 逐页交叉排列
    for (const page of sortedPages) {
      // 获取当前页每个源的结果
      const pageData: Record<NovelSource, Novel[]> = {} as any;
      let maxLen = 0;
      for (const source of sourceOrder) {
        const novels = novelsBySourceByPage.value[source]?.[page] || [];
        pageData[source] = novels;
        if (novels.length > maxLen) maxLen = novels.length;
      }

      // 在当前页内交叉排列
      for (let i = 0; i < maxLen; i += 1) {
        for (const source of sourceOrder) {
          const list = pageData[source];
          if (i >= list.length) continue;
          const novel = list[i];
          if (!novel) continue;
          const key = `${novel.source}:${novel.id}`;
          if (seen.has(key)) continue;
          seen.add(key);
          combined.push(novel);
        }
      }
    }
    novels.value = combined;
  }

  const TAG_CONFIG_STORAGE_KEY = "soyosaki:tagConfigs";

  async function loadTagConfigs() {
    // 加载标签配置（已登录用 API，未登录用 localStorage）
    const userStore = useUserStore();

    if (userStore.isLoggedIn) {
      try {
        const configs = await tagConfigApi.getAll();
        for (const config of configs) {
          const source = config.source as NovelSource;
          if (tagsBySource.value[source] !== undefined) {
            tagsBySource.value[source] = config.tags || [];
            excludeTagsBySource.value[source] = config.exclude_tags || [];
          }
        }
      } catch (e) {
        console.warn("Failed to load tag configs from API:", e);
      }
    } else {
      // 从 localStorage 加载
      const stored = localStorage.getItem(TAG_CONFIG_STORAGE_KEY);
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (parsed.tagsBySource) {
            Object.assign(tagsBySource.value, parsed.tagsBySource);
          }
          if (parsed.excludeTagsBySource) {
            Object.assign(
              excludeTagsBySource.value,
              parsed.excludeTagsBySource,
            );
          }
        } catch (e) {
          console.warn("Failed to parse tag configs from localStorage:", e);
        }
      }
    }
  }

  async function saveTagConfig(source: NovelSource) {
    // 保存某个数据源的标签配置
    const userStore = useUserStore();

    if (userStore.isLoggedIn) {
      try {
        await tagConfigApi.save(
          source,
          tagsBySource.value[source],
          excludeTagsBySource.value[source],
        );
      } catch (e) {
        console.warn("Failed to save tag config to API:", e);
      }
    } else {
      // 保存到 localStorage
      const data = {
        tagsBySource: tagsBySource.value,
        excludeTagsBySource: excludeTagsBySource.value,
      };
      localStorage.setItem(TAG_CONFIG_STORAGE_KEY, JSON.stringify(data));
    }
  }

  async function resetToDefaults() {
    // 重置所有标签配置为默认值
    const userStore = useUserStore();

    // 恢复默认值
    tagsBySource.value = { ...defaultTagsBySource };
    excludeTagsBySource.value = { ...defaultExcludeTagsBySource };

    if (userStore.isLoggedIn) {
      try {
        await tagConfigApi.reset();
      } catch (e) {
        console.warn("Failed to reset tag configs via API:", e);
      }
    } else {
      localStorage.removeItem(TAG_CONFIG_STORAGE_KEY);
    }
  }

  return {
    novels,
    loading,
    error,
    currentPage,
    hasMore,
    pageBreaks, // 导出分页位置
    activeConfigSource,
    selectedSources,
    tagsBySource,
    excludeTagsBySource,
    sortBy,
    loadingSources,
    isEmpty,
    fetchNovels,
    fetchSourcesWithCache,
    loadMore,
    retry,
    loadTagConfigs,
    saveTagConfig,
    resetToDefaults,
  };
});
