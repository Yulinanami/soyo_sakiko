import type { Ref } from "vue";
import type { NovelSearchParams, NovelSource } from "@app-types/novel";
import { novelApi } from "@services/api";
import {
  createSourceRecord,
  type NovelPaginationContext,
} from "./pagination";

export function useNovelQuantityPager(
  context: NovelPaginationContext,
  quantityPageSize: Ref<number>,
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

  async function fetchNovelsByQuantity(
    reset = false,
    specificSources?: NovelSource[],
  ) {
    requestVersion.value += 1;
    const activeRequestId = requestVersion.value;
    const sourcesToProcess = specificSources || selectedSources.value;

    if (reset) {
      currentPage.value = 1;
      currentResultDate.value = null;
      pageBreaks.value = [];
      if (!specificSources) novels.value = [];
      sourcesToProcess.forEach((source) => {
        novelsBySourceByPage.value[source] = {};
        hasMoreBySource.value[source] = false;
      });
    }

    const previousTotal = novels.value.length;
    if (sourcesToProcess.length === 0) {
      error.value = null;
      hasMore.value = false;
      loading.value = false;
      loadingSources.value = createSourceRecord(() => false);
      return;
    }

    const sourcesWithNoTags = sourcesToProcess.filter(
      (source) => tagsBySource.value[source].length === 0,
    );
    if (sourcesWithNoTags.length === sourcesToProcess.length) {
      error.value = "请先选择至少一个标签";
      hasMore.value = false;
      loading.value = false;
      if (!specificSources) novels.value = [];
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
      rebuildNovels();
      if (
        !reset &&
        novels.value.length > previousTotal &&
        !pageBreaks.value.includes(previousTotal)
      ) {
        pageBreaks.value.push(previousTotal);
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
            pageSize: quantityPageSize.value,
            sortBy: sortBy.value,
          };

          try {
            const response = await novelApi.search(params);
            if (activeRequestId !== requestVersion.value) return;

            novelsBySourceByPage.value[source][currentPage.value] =
              response.novels.filter((novel) => novel.source === source);
            hasMoreBySource.value[source] = response.has_more;
            updateAggregates();
          } catch (requestError) {
            if (activeRequestId === requestVersion.value) {
              error.value =
                requestError instanceof Error
                  ? requestError.message
                  : "获取小说列表失败";
            }
          } finally {
            if (activeRequestId === requestVersion.value) {
              loadingSources.value[source] = false;
              updateAggregates();
            }
          }
        }),
      );
    } catch (requestError) {
      error.value =
        requestError instanceof Error
          ? requestError.message
          : "获取小说列表失败";
    } finally {
      if (activeRequestId === requestVersion.value) {
        sourcesToProcess.forEach((source) => {
          loadingSources.value[source] = false;
        });
        loading.value = false;
      }
    }
  }

  return { fetchNovelsByQuantity };
}
