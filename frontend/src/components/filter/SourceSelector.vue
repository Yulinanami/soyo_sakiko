<script setup lang="ts">
import { useSourcesStore } from '../../stores/sources';

const sourcesStore = useSourcesStore();

const emit = defineEmits<{
  (e: 'change'): void;
}>();

function toggle(name: string) {
  sourcesStore.toggleSource(name);
  emit('change');
}
</script>

<template>
  <div class="flex items-center gap-3">
    <span class="font-medium text-gray-700 whitespace-nowrap">数据源:</span>
    <div class="flex gap-2 flex-wrap">
      <button
        v-for="source in sourcesStore.sources"
        :key="source.name"
        :class="[
          'flex items-center gap-1.5 px-3 py-2 border-2 rounded-lg cursor-pointer transition-all text-sm',
          source.enabled 
            ? 'border-primary bg-gradient-to-r from-primary to-secondary text-white' 
            : 'border-gray-200 bg-white hover:border-primary',
          source.requiresAuth && !source.enabled ? 'opacity-60' : ''
        ]"
        @click="toggle(source.name)"
        :title="source.requiresAuth ? '需要配置账号' : ''"
      >
        <span class="text-base">{{ source.icon }}</span>
        <span>{{ source.displayName }}</span>
        <span v-if="source.requiresAuth && !source.enabled" class="text-xs">🔒</span>
      </button>
    </div>
  </div>
</template>
