export type NovelSource = "ao3" | "pixiv" | "lofter" | "bilibili";

export interface Novel {
  id: string;
  source: NovelSource;
  title: string;
  author: string;
  author_url?: string;
  summary: string;
  tags: string[];
  rating?: string;
  word_count?: number;
  chapter_count?: number;
  kudos?: number;
  hits?: number;
  published_at: string;
  updated_at?: string;
  source_url: string;
  cover_image?: string;
  is_complete?: boolean;
}

export interface NovelSearchParams {
  sources: NovelSource[];
  tags: string[];
  excludeTags?: string[];
  page?: number;
  pageSize?: number;
  sortBy?: "date" | "kudos" | "hits" | "wordCount";
}

export interface NovelListResponse {
  novels: Novel[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}
