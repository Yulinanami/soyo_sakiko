import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type {
  Novel,
  NovelFetchMode,
  NovelSource,
} from "@app-types/novel";
import { useNovelDatePager } from "./novels/datePager";
import {
  createSourceRecord,
  mergeNovelPages,
  NOVEL_SOURCES,
  readStoredInteger,
  type NovelPagesBySource,
  type NovelPaginationContext,
} from "./novels/pagination";
import { useNovelQueryConfig } from "./novels/queryConfig";
import { useNovelQuantityPager } from "./novels/quantityPager";

const FETCH_MODE_STORAGE_KEY = "soyosaki:novelFetchMode";
const QUANTITY_PAGE_SIZE_STORAGE_KEY = "soyosaki:quantityPageSize";
const DATES_PER_PAGE_STORAGE_KEY = "soyosaki:datesPerPage";

export const useNovelsStore = defineStore("novels", () => {
  const novels = ref<Novel[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const currentPage = ref(1);
  const hasMore = ref(false);
  const hasFetched = ref(false);
  const currentResultDate = ref<string | null>(null);
  const pageBreaks = ref<number[]>([]);
  const novelsBySourceByPage = ref<NovelPagesBySource>(
    createSourceRecord(() => ({})),
  );
  const hasMoreBySource = ref(
    createSourceRecord(() => false),
  );
  const loadingSources = ref(
    createSourceRecord(() => false),
  );
  const requestVersion = { value: 0 };

  const storedFetchMode = localStorage.getItem(FETCH_MODE_STORAGE_KEY);
  const fetchMode = ref<NovelFetchMode>(
    storedFetchMode === "date" ? "date" : "quantity",
  );
  const quantityPageSize = ref(
    readStoredInteger(QUANTITY_PAGE_SIZE_STORAGE_KEY, 30, 1, 100),
  );
  const datesPerPage = ref(
    readStoredInteger(DATES_PER_PAGE_STORAGE_KEY, 1, 1, 30),
  );

  const isEmpty = computed(() => novels.value.length === 0 && !loading.value);

  function markFetchConfigChanged() {
    // 保留当前列表，但在重新获取前禁止继续混入旧配置的分页
    hasMore.value = false;
  }

  const {
    activeConfigSource,
    selectedSources,
    tagsBySource,
    excludeTagsBySource,
    sortBy,
    loadTagConfigs,
    saveTagConfig,
    resetToDefaults,
  } = useNovelQueryConfig(markFetchConfigChanged);

  function rebuildNovels() {
    novels.value = mergeNovelPages(
      novelsBySourceByPage.value,
      selectedSources.value,
    );
  }

  const paginationContext: NovelPaginationContext = {
    novels,
    loading,
    error,
    currentPage,
    hasMore,
    currentResultDate,
    pageBreaks,
    novelsBySourceByPage,
    hasMoreBySource,
    loadingSources,
    selectedSources,
    tagsBySource,
    excludeTagsBySource,
    sortBy,
    requestVersion,
    rebuildNovels,
  };

  const { fetchNovelsByQuantity } = useNovelQuantityPager(
    paginationContext,
    quantityPageSize,
  );
  const { fetchNovelsByDate, loadMoreByDate, resetDatePaging } =
    useNovelDatePager(paginationContext, datesPerPage);

  async function fetchNovels(reset = false, specificSources?: NovelSource[]) {
    hasFetched.value = true;
    if (fetchMode.value === "date") {
      await fetchNovelsByDate(reset || Boolean(specificSources));
      return;
    }
    await fetchNovelsByQuantity(reset, specificSources);
  }

  async function loadMoreByQuantity() {
    if (loading.value || !hasMore.value || selectedSources.value.length === 0) {
      return;
    }
    currentPage.value += 1;
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
    error.value = null;
    fetchNovels(true);
  }

  function setQuantityPageSize(value: number | undefined) {
    if (typeof value !== "number" || !Number.isFinite(value)) return;
    const nextValue = Math.min(100, Math.max(1, Math.round(value)));
    if (quantityPageSize.value === nextValue) return;
    quantityPageSize.value = nextValue;
    localStorage.setItem(QUANTITY_PAGE_SIZE_STORAGE_KEY, String(nextValue));
    markFetchConfigChanged();
  }

  function setDatesPerPage(value: number | undefined) {
    if (typeof value !== "number" || !Number.isFinite(value)) return;
    const nextValue = Math.min(30, Math.max(1, Math.round(value)));
    if (datesPerPage.value === nextValue) return;
    datesPerPage.value = nextValue;
    localStorage.setItem(DATES_PER_PAGE_STORAGE_KEY, String(nextValue));
    markFetchConfigChanged();
  }

  function setFetchMode(mode: NovelFetchMode) {
    // 保存获取方式，等待用户手动开始获取
    if (fetchMode.value === mode) return;
    requestVersion.value += 1;
    fetchMode.value = mode;
    localStorage.setItem(FETCH_MODE_STORAGE_KEY, mode);
    novels.value = [];
    currentPage.value = 1;
    currentResultDate.value = null;
    pageBreaks.value = [];
    hasMore.value = false;
    hasFetched.value = false;
    error.value = null;
    resetDatePaging();
    NOVEL_SOURCES.forEach((source) => {
      novelsBySourceByPage.value[source] = {};
      hasMoreBySource.value[source] = false;
      loadingSources.value[source] = false;
    });
    loading.value = false;
  }

  return {
    novels,
    loading,
    error,
    currentPage,
    hasMore,
    hasFetched,
    fetchMode,
    quantityPageSize,
    datesPerPage,
    currentResultDate,
    pageBreaks,
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
    setQuantityPageSize,
    setDatesPerPage,
    loadTagConfigs,
    saveTagConfig,
    resetToDefaults,
  };
});
