import type { NovelSource } from '@app-types/novel';

export interface SourceConfig {
  name: NovelSource;
  displayName: string;
  icon: string;
  enabled: boolean;
  requiresAuth: boolean;
}

export const DEFAULT_SOURCES: SourceConfig[] = [
  {
    name: 'ao3',
    displayName: 'Archive of Our Own',
    icon: '📚',
    enabled: true,
    requiresAuth: false,
  },
  {
    name: 'bilibili',
    displayName: 'Bilibili',
    icon: '📺',
    enabled: false,
    requiresAuth: false,
  },
  {
    name: 'pixiv',
    displayName: 'Pixiv',
    icon: '🎨',
    enabled: false,
    requiresAuth: true,
  },
  {
    name: 'lofter',
    displayName: 'Lofter',
    icon: '📝',
    enabled: false,
    requiresAuth: true,
  },
];

export interface CredentialState {
  state: string;
  message: string;
  configured: boolean;
}
