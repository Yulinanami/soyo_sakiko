export type NovelSource = "ao3" | "pixiv" | "lofter";

export interface Novel {
  id: string;
  source: NovelSource;
  title: string;
  author: string;
  authorUrl?: string;
  summary: string;
  tags: string[];
  rating?: string;
  wordCount?: number;
  chapterCount?: number;
  kudos?: number;
  hits?: number;
  publishedAt: string;
  updatedAt?: string;
  sourceUrl: string;
  coverImage?: string;
  isComplete?: boolean;
}

export interface NovelSearchParams {
  sources: NovelSource[];
  tags: string[];
  page?: number;
  pageSize?: number;
  sortBy?: "date" | "kudos" | "hits" | "wordCount";
  sortOrder?: "asc" | "desc";
}

export interface NovelListResponse {
  novels: Novel[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}
