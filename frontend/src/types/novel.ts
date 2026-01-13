export type NovelSource = "ao3" | "pixiv" | "lofter";

export interface Novel {
  id: string;
  source: NovelSource;
  title: string;
  author: string;
  author_url?: string;       // snake_case from backend
  summary: string;
  tags: string[];
  rating?: string;
  word_count?: number;       // snake_case from backend
  chapter_count?: number;    // snake_case from backend
  kudos?: number;
  hits?: number;
  published_at: string;      // snake_case from backend
  updated_at?: string;       // snake_case from backend
  source_url: string;        // snake_case from backend
  cover_image?: string;      // snake_case from backend
  is_complete?: boolean;     // snake_case from backend
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
  page_size: number;  // Backend uses snake_case
  has_more: boolean;  // Backend uses snake_case
}
