import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type {
  Novel,
  NovelFetchMode,
  NovelListResponse,
  NovelSearchParams,
  NovelSource,
} from "@app-types/novel";
import { novelApi, tagConfigApi } from "@services/api";
import { useUserStore } from "@stores/user";

export const useNovelsStore = defineStore("novels", () => {
  const novels = ref<Novel[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const currentPage = ref(1);
  const pageSize = 30;
  const hasMore = ref(false);
  const hasFetched = ref(false);
  const fetchModeStorageKey = "soyosaki:novelFetchMode";
  const storedFetchMode = localStorage.getItem(fetchModeStorageKey);
  const fetchMode = ref<NovelFetchMode>(
    storedFetchMode === "date" ? "date" : "quantity",
  );
  const currentResultDate = ref<string | null>(null);
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
  const nextDatePageBySource = ref<Record<NovelSource, number>>({
    ao3: 1,
    pixiv: 1,
    lofter: 1,
    bilibili: 1,
  });
  let dateSeenIdsBySource: Record<NovelSource, Set<string>> = {
    ao3: new Set(),
    pixiv: new Set(),
    lofter: new Set(),
    bilibili: new Set(),
  };
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

  async function fetchNovelsByQuantity(
    reset = false,
    specificSources?: NovelSource[],
  ) {
    // 获取小说列表
    requestId += 1;
    const activeRequestId = requestId;

    const sourcesToProcess = specificSources || selectedSources.value;

    if (reset) {
      currentPage.value = 1;
      currentResultDate.value = null;
      pageBreaks.value = []; // 重置时清空分页记录
      if (!specificSources) {
        novels.value = [];
      }
      sourcesToProcess.forEach((source) => {
        novelsBySourceByPage.value[source] = {};
        hasMoreBySource.value[source] = false;
      });
    }

    // 记录加载前的数量，用于判断是否真的加载到了新内容
    const previousTotal = novels.value.length;

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

      // 如果是非重置加载，且列表长度增加了，才记录分页点
      if (!reset && novels.value.length > previousTotal) {
        if (!pageBreaks.value.includes(previousTotal)) {
          pageBreaks.value.push(previousTotal);
        }
      }

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

  type DateCandidate = {
    source: NovelSource;
    response: NovelListResponse | null;
  };

  function formatLocalDate(value: Date) {
    const year = value.getFullYear();
    const month = String(value.getMonth() + 1).padStart(2, "0");
    const day = String(value.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function getTomorrowDate() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return formatLocalDate(tomorrow);
  }

  function resetDatePaging() {
    nextDatePageBySource.value = {
      ao3: 1,
      pixiv: 1,
      lofter: 1,
      bilibili: 1,
    };
    dateSeenIdsBySource = {
      ao3: new Set(),
      pixiv: new Set(),
      lofter: new Set(),
      bilibili: new Set(),
    };
  }

  async function fetchNextDatePage(
    source: NovelSource,
    activeRequestId: number,
  ) {
    const page = nextDatePageBySource.value[source];
    try {
      const response = await novelApi.search({
        sources: [source],
        tags: tagsBySource.value[source],
        excludeTags: excludeTagsBySource.value[source],
        page,
        pageSize,
        sortBy: "date",
      });
      if (activeRequestId !== requestId) return false;

      nextDatePageBySource.value[source] = page + 1;
      let discoveredNewNovel = false;
      for (const novel of response.novels) {
        const key = `${novel.source}:${novel.id}`;
        if (!dateSeenIdsBySource[source].has(key)) {
          dateSeenIdsBySource[source].add(key);
          discoveredNewNovel = true;
        }
      }
      hasMoreBySource.value[source] =
        response.has_more && response.novels.length > 0 && discoveredNewNovel;
      return discoveredNewNovel;
    } catch (err) {
      if (activeRequestId === requestId) {
        error.value = err instanceof Error ? err.message : "获取小说列表失败";
        hasMoreBySource.value[source] = false;
      }
      return false;
    }
  }

  async function ensureDateCandidate(
    source: NovelSource,
    beforeDate: string,
    activeRequestId: number,
  ): Promise<NovelListResponse | null> {
    while (activeRequestId === requestId) {
      try {
        const response = await novelApi.getCachedByDate({
          source,
          tags: tagsBySource.value[source],
          excludeTags: excludeTagsBySource.value[source],
          beforeDate,
          sortBy: sortBy.value,
        });
        if (response.result_date) return response;
        if (!hasMoreBySource.value[source]) return response;
      } catch (err) {
        if (activeRequestId === requestId) {
          error.value =
            err instanceof Error ? err.message : "读取本地同人文缓存失败";
          hasMoreBySource.value[source] = false;
        }
        return null;
      }

      const fetched = await fetchNextDatePage(source, activeRequestId);
      if (!fetched && !hasMoreBySource.value[source]) return null;
    }
    return null;
  }

  async function collectDateCandidates(
    sources: NovelSource[],
    beforeDate: string,
    activeRequestId: number,
  ): Promise<DateCandidate[]> {
    return Promise.all(
      sources.map(async (source) => ({
        source,
        response: await ensureDateCandidate(
          source,
          beforeDate,
          activeRequestId,
        ),
      })),
    );
  }

  function applyDateCandidates(
    candidates: DateCandidate[],
    displayPage: number,
    reset: boolean,
  ) {
    const datedCandidates = candidates.filter(
      (candidate) => candidate.response?.result_date,
    );
    const resultDate = datedCandidates.reduce<string | null>(
      (latest, candidate) => {
        const candidateDate = candidate.response?.result_date;
        if (!candidateDate) return latest;
        return !latest || candidateDate > latest ? candidateDate : latest;
      },
      null,
    );

    if (!resultDate) {
      hasMore.value = false;
      return false;
    }

    const previousTotal = novels.value.length;
    for (const candidate of candidates) {
      novelsBySourceByPage.value[candidate.source][displayPage] =
        candidate.response?.result_date === resultDate
          ? candidate.response.novels
          : [];
    }

    currentResultDate.value = resultDate;
    currentPage.value = displayPage;
    rebuildNovels();
    if (!reset && novels.value.length > previousTotal) {
      pageBreaks.value.push(previousTotal);
    }

    const cachedOlderDate = candidates.some((candidate) => {
      const candidateDate = candidate.response?.result_date;
      return Boolean(
        candidateDate &&
          (candidateDate < resultDate || candidate.response?.has_more),
      );
    });
    const sourceCanFetchMore = selectedSources.value.some(
      (source) => hasMoreBySource.value[source],
    );
    hasMore.value = cachedOlderDate || sourceCanFetchMore;
    return true;
  }

  async function fetchNovelsByDate(reset = false) {
    if (!reset && currentResultDate.value) {
      await loadMoreByDate();
      return;
    }

    requestId += 1;
    const activeRequestId = requestId;
    const sourcesToProcess = selectedSources.value.filter(
      (source) => tagsBySource.value[source].length > 0,
    );

    currentPage.value = 1;
    currentResultDate.value = null;
    pageBreaks.value = [];
    novels.value = [];
    resetDatePaging();
    (Object.keys(novelsBySourceByPage.value) as NovelSource[]).forEach(
      (source) => {
        novelsBySourceByPage.value[source] = {};
        hasMoreBySource.value[source] = sourcesToProcess.includes(source);
        loadingSources.value[source] = sourcesToProcess.includes(source);
      },
    );

    if (sourcesToProcess.length === 0) {
      error.value = "请先选择至少一个标签";
      hasMore.value = false;
      loading.value = false;
      return;
    }

    loading.value = true;
    error.value = null;
    try {
      await Promise.all(
        sourcesToProcess.map((source) =>
          fetchNextDatePage(source, activeRequestId),
        ),
      );
      if (activeRequestId !== requestId) return;

      const candidates = await collectDateCandidates(
        sourcesToProcess,
        getTomorrowDate(),
        activeRequestId,
      );
      if (activeRequestId === requestId) {
        applyDateCandidates(candidates, 1, true);
      }
    } finally {
      if (activeRequestId === requestId) {
        sourcesToProcess.forEach((source) => {
          loadingSources.value[source] = false;
        });
        loading.value = false;
      }
    }
  }

  async function loadMoreByDate() {
    if (
      loading.value ||
      !hasMore.value ||
      !currentResultDate.value ||
      selectedSources.value.length === 0
    )
      return;

    requestId += 1;
    const activeRequestId = requestId;
    const sourcesToProcess = selectedSources.value.filter(
      (source) => tagsBySource.value[source].length > 0,
    );
    sourcesToProcess.forEach((source) => {
      loadingSources.value[source] = true;
    });
    loading.value = true;
    error.value = null;
    try {
      const candidates = await collectDateCandidates(
        sourcesToProcess,
        currentResultDate.value,
        activeRequestId,
      );
      if (activeRequestId === requestId) {
        applyDateCandidates(candidates, currentPage.value + 1, false);
      }
    } finally {
      if (activeRequestId === requestId) {
        sourcesToProcess.forEach((source) => {
          loadingSources.value[source] = false;
        });
        loading.value = false;
      }
    }
  }

  async function fetchNovels(reset = false, specificSources?: NovelSource[]) {
    hasFetched.value = true;
    if (fetchMode.value === "date") {
      await fetchNovelsByDate(reset || Boolean(specificSources));
      return;
    }
    await fetchNovelsByQuantity(reset, specificSources);
  }

  async function loadMoreByQuantity() {
    // 加载更多
    if (loading.value || !hasMore.value || selectedSources.value.length === 0)
      return;
    currentPage.value++;
    await fetchNovels(false);
  }

  async function loadMore() {
    if (fetchMode.value === "date") {
      await loadMoreByDate();
      return;
    }
    await loadMoreByQuantity();
  }

  function retry() {
    // 按当前配置从第一页重新获取
    error.value = null;
    fetchNovels(true);
  }

  function markFetchConfigChanged() {
    // 保留当前列表，但在重新获取前禁止继续混入旧配置的分页
    hasMore.value = false;
  }

  function setFetchMode(mode: NovelFetchMode) {
    // 保存获取方式，等待用户手动开始获取
    if (fetchMode.value === mode) return;
    requestId += 1;
    fetchMode.value = mode;
    localStorage.setItem(fetchModeStorageKey, mode);
    novels.value = [];
    currentPage.value = 1;
    currentResultDate.value = null;
    pageBreaks.value = [];
    hasMore.value = false;
    hasFetched.value = false;
    error.value = null;
    resetDatePaging();
    (Object.keys(novelsBySourceByPage.value) as NovelSource[]).forEach(
      (source) => {
        novelsBySourceByPage.value[source] = {};
        hasMoreBySource.value[source] = false;
        loadingSources.value[source] = false;
      },
    );
    loading.value = false;
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
    markFetchConfigChanged();
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
    markFetchConfigChanged();

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
    hasFetched,
    fetchMode,
    currentResultDate,
    pageBreaks, // 导出分页位置
    activeConfigSource,
    selectedSources,
    tagsBySource,
    excludeTagsBySource,
    sortBy,
    loadingSources,
    isEmpty,
    fetchNovels,
    loadMore,
    retry,
    markFetchConfigChanged,
    setFetchMode,
    loadTagConfigs,
    saveTagConfig,
    resetToDefaults,
  };
});
