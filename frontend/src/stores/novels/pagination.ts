import type { Ref } from "vue";
import type {
  Novel,
  NovelSearchParams,
  NovelSource,
} from "@app-types/novel";

export const NOVEL_SOURCES: NovelSource[] = [
  "ao3",
  "pixiv",
  "lofter",
  "bilibili",
];

export type NovelSort = NonNullable<NovelSearchParams["sortBy"]>;
export type NovelPagesBySource = Record<
  NovelSource,
  Record<number, Novel[]>
>;

export interface RequestVersion {
  value: number;
}

export interface NovelPaginationContext {
  novels: Ref<Novel[]>;
  loading: Ref<boolean>;
  error: Ref<string | null>;
  currentPage: Ref<number>;
  hasMore: Ref<boolean>;
  currentResultDate: Ref<string | null>;
  pageBreaks: Ref<number[]>;
  novelsBySourceByPage: Ref<NovelPagesBySource>;
  hasMoreBySource: Ref<Record<NovelSource, boolean>>;
  loadingSources: Ref<Record<NovelSource, boolean>>;
  selectedSources: Ref<NovelSource[]>;
  tagsBySource: Ref<Record<NovelSource, string[]>>;
  excludeTagsBySource: Ref<Record<NovelSource, string[]>>;
  sortBy: Ref<NovelSort>;
  requestVersion: RequestVersion;
  rebuildNovels: () => void;
}

export function createSourceRecord<T>(
  createValue: (source: NovelSource) => T,
): Record<NovelSource, T> {
  return Object.fromEntries(
    NOVEL_SOURCES.map((source) => [source, createValue(source)]),
  ) as Record<NovelSource, T>;
}

export function readStoredInteger(
  key: string,
  fallback: number,
  min: number,
  max: number,
) {
  const storedValue = localStorage.getItem(key);
  if (storedValue === null) return fallback;
  const parsedValue = Number(storedValue);
  if (!Number.isInteger(parsedValue)) return fallback;
  return Math.min(max, Math.max(min, parsedValue));
}

export function mergeNovelPages(
  pagesBySource: NovelPagesBySource,
  selectedSources: NovelSource[],
) {
  const sourceOrder = selectedSources.length ? selectedSources : NOVEL_SOURCES;
  const pageNumbers = new Set<number>();

  for (const source of sourceOrder) {
    Object.keys(pagesBySource[source]).forEach((page) => {
      pageNumbers.add(Number(page));
    });
  }

  const combined: Novel[] = [];
  const seen = new Set<string>();
  const sortedPages = Array.from(pageNumbers).sort((a, b) => a - b);

  for (const page of sortedPages) {
    const pageLists = sourceOrder.map(
      (source) => pagesBySource[source][page] ?? [],
    );
    const maxLength = Math.max(0, ...pageLists.map((list) => list.length));

    for (let index = 0; index < maxLength; index += 1) {
      for (const list of pageLists) {
        const novel = list[index];
        if (!novel) continue;
        const key = `${novel.source}:${novel.id}`;
        if (seen.has(key)) continue;
        seen.add(key);
        combined.push(novel);
      }
    }
  }

  return combined;
}
