import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { SourceConfig } from '../types/source';
import { DEFAULT_SOURCES } from '../types/source';

export const useSourcesStore = defineStore('sources', () => {
  // State
  const sources = ref<SourceConfig[]>(DEFAULT_SOURCES);
  const loading = ref(false);

  // Actions
  function toggleSource(name: string) {
    const source = sources.value.find(s => s.name === name);
    if (source) {
      source.enabled = !source.enabled;
    }
  }

  function enableSource(name: string) {
    const source = sources.value.find(s => s.name === name);
    if (source) {
      source.enabled = true;
    }
  }

  function disableSource(name: string) {
    const source = sources.value.find(s => s.name === name);
    if (source) {
      source.enabled = false;
    }
  }

  function getEnabledSources() {
    return sources.value.filter(s => s.enabled);
  }

  function getEnabledSourceNames() {
    return sources.value.filter(s => s.enabled).map(s => s.name);
  }

  return {
    sources,
    loading,
    toggleSource,
    enableSource,
    disableSource,
    getEnabledSources,
    getEnabledSourceNames,
  };
});
