import { ref } from "vue";
import type { NovelSource } from "@app-types/novel";
import { tagConfigApi } from "@services/api";
import { useUserStore } from "@stores/user";
import type { NovelSort } from "./pagination";

const TAG_CONFIG_STORAGE_KEY = "soyosaki:tagConfigs";

const commonExclusion = [
  "all祥",
  "祥睦",
  "睦祥",
  "祥希",
  "希祥",
  "要乐奈",
  "素爱",
  "祥爱",
  "爱祥",
  "祥初",
  "祥灯",
  "高松灯",
  "千早爱音",
  "三角初华",
  "海祥",
  "灯祥",
  "初祥",
  "ansy",
  "爱素",
];

const defaultTagsBySource: Record<NovelSource, string[]> = {
  ao3: ["素祥", "祥素", "Nagasaki Soyo/Togawa Sakiko"],
  pixiv: ["素祥", "祥素", "そよさき"],
  lofter: ["素祥"],
  bilibili: ["素祥"],
};

const defaultExcludeTagsBySource: Record<NovelSource, string[]> = {
  ao3: [...commonExclusion],
  pixiv: [...commonExclusion],
  lofter: [...commonExclusion],
  bilibili: [...commonExclusion],
};

export function useNovelQueryConfig(onFetchConfigChanged: () => void) {
  const activeConfigSource = ref<NovelSource>("ao3");
  const selectedSources = ref<NovelSource[]>(["ao3"]);
  const tagsBySource = ref<Record<NovelSource, string[]>>({
    ...defaultTagsBySource,
  });
  const excludeTagsBySource = ref<Record<NovelSource, string[]>>({
    ...defaultExcludeTagsBySource,
  });
  const sortBy = ref<NovelSort>("date");

  async function loadTagConfigs() {
    const userStore = useUserStore();

    if (userStore.isLoggedIn) {
      try {
        const configs = await tagConfigApi.getAll();
        for (const config of configs) {
          const source = config.source as NovelSource;
          if (tagsBySource.value[source] !== undefined) {
            tagsBySource.value[source] = config.tags || [];
            excludeTagsBySource.value[source] = config.exclude_tags || [];
          }
        }
      } catch (error) {
        console.warn("Failed to load tag configs from API:", error);
      }
      return;
    }

    const stored = localStorage.getItem(TAG_CONFIG_STORAGE_KEY);
    if (!stored) return;

    try {
      const parsed = JSON.parse(stored);
      if (parsed.tagsBySource) {
        Object.assign(tagsBySource.value, parsed.tagsBySource);
      }
      if (parsed.excludeTagsBySource) {
        Object.assign(
          excludeTagsBySource.value,
          parsed.excludeTagsBySource,
        );
      }
    } catch (error) {
      console.warn("Failed to parse tag configs from localStorage:", error);
    }
  }

  async function saveTagConfig(source: NovelSource) {
    onFetchConfigChanged();
    const userStore = useUserStore();

    if (userStore.isLoggedIn) {
      try {
        await tagConfigApi.save(
          source,
          tagsBySource.value[source],
          excludeTagsBySource.value[source],
        );
      } catch (error) {
        console.warn("Failed to save tag config to API:", error);
      }
      return;
    }

    localStorage.setItem(
      TAG_CONFIG_STORAGE_KEY,
      JSON.stringify({
        tagsBySource: tagsBySource.value,
        excludeTagsBySource: excludeTagsBySource.value,
      }),
    );
  }

  async function resetToDefaults() {
    const userStore = useUserStore();
    tagsBySource.value = { ...defaultTagsBySource };
    excludeTagsBySource.value = { ...defaultExcludeTagsBySource };
    onFetchConfigChanged();

    if (userStore.isLoggedIn) {
      try {
        await tagConfigApi.reset();
      } catch (error) {
        console.warn("Failed to reset tag configs via API:", error);
      }
      return;
    }

    localStorage.removeItem(TAG_CONFIG_STORAGE_KEY);
  }

  return {
    activeConfigSource,
    selectedSources,
    tagsBySource,
    excludeTagsBySource,
    sortBy,
    loadTagConfigs,
    saveTagConfig,
    resetToDefaults,
  };
}
