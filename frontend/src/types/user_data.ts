export interface FavoriteItem {
  id: number;
  novel_id: string;
  source: string;
  title: string;
  author?: string;
  cover_url?: string;
  source_url?: string;
  created_at: string;
}

export interface HistoryItem {
  id: number;
  novel_id: string;
  source: string;
  title?: string;
  author?: string;
  cover_url?: string;
  source_url?: string;
  last_read_at: string;
  last_chapter?: number;
  progress?: number;
}
