import { ref, type Ref } from "vue";
import type {
  NovelListResponse,
  NovelSource,
} from "@app-types/novel";
import { novelApi } from "@services/api";
import {
  createSourceRecord,
  NOVEL_SOURCES,
  type NovelPaginationContext,
} from "./pagination";

const DATE_FETCH_PAGE_SIZE = 30;

type DateCandidate = {
  source: NovelSource;
  response: NovelListResponse | null;
};

export function useNovelDatePager(
  context: NovelPaginationContext,
  datesPerPage: Ref<number>,
) {
  const {
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
  } = context;

  const nextDatePageBySource = ref(createSourceRecord(() => 1));
  let dateSeenIdsBySource = createSourceRecord(() => new Set<string>());
  let currentDateBucket = 0;

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
    currentDateBucket = 0;
    nextDatePageBySource.value = createSourceRecord(() => 1);
    dateSeenIdsBySource = createSourceRecord(() => new Set<string>());
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
        pageSize: DATE_FETCH_PAGE_SIZE,
        sortBy: "date",
      });
      if (activeRequestId !== requestVersion.value) return false;

      nextDatePageBySource.value[source] = page + 1;
      let discoveredNewNovel = false;
      for (const novel of response.novels) {
        const key = `${novel.source}:${novel.id}`;
        if (dateSeenIdsBySource[source].has(key)) continue;
        dateSeenIdsBySource[source].add(key);
        discoveredNewNovel = true;
      }
      hasMoreBySource.value[source] =
        response.has_more && response.novels.length > 0 && discoveredNewNovel;
      return discoveredNewNovel;
    } catch (requestError) {
      if (activeRequestId === requestVersion.value) {
        error.value =
          requestError instanceof Error
            ? requestError.message
            : "获取小说列表失败";
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
    while (activeRequestId === requestVersion.value) {
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
      } catch (requestError) {
        if (activeRequestId === requestVersion.value) {
          error.value =
            requestError instanceof Error
              ? requestError.message
              : "读取本地同人文缓存失败";
          hasMoreBySource.value[source] = false;
        }
        return null;
      }

      const fetched = await fetchNextDatePage(source, activeRequestId);
      if (!fetched && !hasMoreBySource.value[source]) return null;
    }
    return null;
  }

  function collectDateCandidates(
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
    dateBucket: number,
    beforeDate: string,
  ): string | null {
    const resultDate = candidates.reduce<string | null>(
      (latest, candidate) => {
        const candidateDate = candidate.response?.result_date;
        if (!candidateDate) return latest;
        return !latest || candidateDate > latest ? candidateDate : latest;
      },
      null,
    );

    if (!resultDate || resultDate >= beforeDate) {
      hasMore.value = false;
      return null;
    }

    for (const candidate of candidates) {
      novelsBySourceByPage.value[candidate.source][dateBucket] =
        candidate.response?.result_date === resultDate
          ? candidate.response.novels
          : [];
    }

    currentResultDate.value = resultDate;
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
    return resultDate;
  }

  async function loadDateBatch(
    sources: NovelSource[],
    beforeDate: string,
    activeRequestId: number,
    displayPage: number,
    reset: boolean,
  ) {
    const previousTotal = novels.value.length;
    let cursor = beforeDate;
    let loadedDateCount = 0;

    while (
      activeRequestId === requestVersion.value &&
      loadedDateCount < datesPerPage.value
    ) {
      const candidates = await collectDateCandidates(
        sources,
        cursor,
        activeRequestId,
      );
      if (activeRequestId !== requestVersion.value) return false;

      const nextDateBucket = currentDateBucket + 1;
      const resultDate = applyDateCandidates(
        candidates,
        nextDateBucket,
        cursor,
      );
      if (!resultDate) break;

      currentDateBucket = nextDateBucket;
      loadedDateCount += 1;
      cursor = resultDate;
      if (!hasMore.value) break;
    }

    if (loadedDateCount === 0) return false;

    currentPage.value = displayPage;
    rebuildNovels();
    if (
      !reset &&
      novels.value.length > previousTotal &&
      !pageBreaks.value.includes(previousTotal)
    ) {
      pageBreaks.value.push(previousTotal);
    }
    return true;
  }

  async function fetchNovelsByDate(reset = false) {
    if (!reset && currentResultDate.value) {
      await loadMoreByDate();
      return;
    }

    requestVersion.value += 1;
    const activeRequestId = requestVersion.value;
    const sourcesToProcess = selectedSources.value.filter(
      (source) => tagsBySource.value[source].length > 0,
    );

    currentPage.value = 1;
    currentResultDate.value = null;
    pageBreaks.value = [];
    novels.value = [];
    resetDatePaging();
    NOVEL_SOURCES.forEach((source) => {
      novelsBySourceByPage.value[source] = {};
      hasMoreBySource.value[source] = sourcesToProcess.includes(source);
      loadingSources.value[source] = sourcesToProcess.includes(source);
    });

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
      if (activeRequestId !== requestVersion.value) return;

      await loadDateBatch(
        sourcesToProcess,
        getTomorrowDate(),
        activeRequestId,
        1,
        true,
      );
    } finally {
      if (activeRequestId === requestVersion.value) {
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
    ) {
      return;
    }

    requestVersion.value += 1;
    const activeRequestId = requestVersion.value;
    const sourcesToProcess = selectedSources.value.filter(
      (source) => tagsBySource.value[source].length > 0,
    );
    sourcesToProcess.forEach((source) => {
      loadingSources.value[source] = true;
    });
    loading.value = true;
    error.value = null;

    try {
      await loadDateBatch(
        sourcesToProcess,
        currentResultDate.value,
        activeRequestId,
        currentPage.value + 1,
        false,
      );
    } finally {
      if (activeRequestId === requestVersion.value) {
        sourcesToProcess.forEach((source) => {
          loadingSources.value[source] = false;
        });
        loading.value = false;
      }
    }
  }

  return {
    fetchNovelsByDate,
    loadMoreByDate,
    resetDatePaging,
  };
}
