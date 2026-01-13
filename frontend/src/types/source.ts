import type { NovelSource } from './novel';

export interface SourceConfig {
  name: NovelSource;
  displayName: string;
  icon: string;
  enabled: boolean;
  requiresAuth: boolean;
  searchTags: string[];
}

export const DEFAULT_SOURCES: SourceConfig[] = [
  {
    name: 'ao3',
    displayName: 'Archive of Our Own',
    icon: '📚',
    enabled: true,
    requiresAuth: false,
    searchTags: ['Nagasaki Soyo/Toyokawa Sakiko', 'Toyokawa Sakiko/Nagasaki Soyo', '素祥', '祥素'],
  },
  {
    name: 'pixiv',
    displayName: 'Pixiv',
    icon: '🎨',
    enabled: false,
    requiresAuth: true,
    searchTags: ['素祥', '祥素', '長崎そよ×豊川祥子'],
  },
  {
    name: 'lofter',
    displayName: 'Lofter',
    icon: '📝',
    enabled: false,
    requiresAuth: true,
    searchTags: ['素祥', '祥素'],
  },
];
