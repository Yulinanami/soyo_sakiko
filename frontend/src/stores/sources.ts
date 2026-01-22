import { defineStore } from "pinia";
import { ref } from "vue";
import type { SourceConfig } from "@app-types/source";
import { DEFAULT_SOURCES } from "@app-types/source";

export const useSourcesStore = defineStore("sources", () => {
  const sources = ref<SourceConfig[]>(DEFAULT_SOURCES);

  function toggleSource(name: string) {
    // 切换来源开关
    const source = sources.value.find((s) => s.name === name);
    if (source) {
      source.enabled = !source.enabled;
    }
  }

  function getSourceDisplayName(name: string) {
    // 获取来源显示名称
    return sources.value.find((s) => s.name === name)?.displayName || name;
  }

  function getEnabledSourceNames() {
    // 获取已开启的来源
    return sources.value.filter((s) => s.enabled).map((s) => s.name);
  }

  return {
    sources,
    toggleSource,
    getEnabledSourceNames,
    getSourceDisplayName,
  };
});
