import type { NovelSource } from "@app-types/novel";

export interface SourceConfig {
  name: NovelSource;
  displayName: string;
  enabled: boolean;
  requiresAuth: boolean;
}

export const DEFAULT_SOURCES: SourceConfig[] = [
  {
    name: "ao3",
    displayName: "Archive of Our Own",
    enabled: true,
    requiresAuth: false,
  },
  {
    name: "bilibili",
    displayName: "Bilibili",
    enabled: false,
    requiresAuth: false,
  },
  {
    name: "pixiv",
    displayName: "Pixiv",
    enabled: false,
    requiresAuth: true,
  },
  {
    name: "lofter",
    displayName: "Lofter",
    enabled: false,
    requiresAuth: true,
  },
];

export interface CredentialState {
  state: string;
  message: string;
  configured: boolean;
}
