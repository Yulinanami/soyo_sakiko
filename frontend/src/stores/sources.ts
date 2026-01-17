import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { SourceConfig } from '../types/source';
import { DEFAULT_SOURCES } from '../types/source';

export const useSourcesStore = defineStore('sources', () => {
  // State
  const sources = ref<SourceConfig[]>(DEFAULT_SOURCES);

  // Actions
  function toggleSource(name: string) {
    const source = sources.value.find(s => s.name === name);
    if (source) {
      source.enabled = !source.enabled;
    }
  }

  function getEnabledSourceNames() {
    return sources.value.filter(s => s.enabled).map(s => s.name);
  }

  return {
    sources,
    toggleSource,
    getEnabledSourceNames,
  };
});
