<script setup lang="ts">
import NovelCard from '@components/novel/NovelCard.vue';
import type { Novel } from '@app-types/novel';

defineProps<{
  novels: Novel[];
  loading: boolean;
  hasMore: boolean;
}>();

const emit = defineEmits<{
  (e: 'load-more'): void;
}>();
</script>

<template>
  <div class="w-full">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      <NovelCard 
        v-for="novel in novels" 
        :key="`${novel.source}-${novel.id}`"
        :novel="novel"
      />
    </div>
    
    <div v-if="loading" class="flex items-center justify-center gap-3 py-12 text-gray-500 dark:text-gray-400">
      <div class="w-6 h-6 border-3 border-gray-200 border-t-primary rounded-full animate-spin dark:border-gray-700"></div>
      <span>加载中...</span>
    </div>
    
    <div v-if="!loading && hasMore" class="flex flex-col items-center gap-3 py-8">
      <span class="text-sm text-gray-500 dark:text-gray-400">已加载 {{ novels.length }} 篇同人文</span>
      <button @click="emit('load-more')" class="btn-primary">
        加载更多
      </button>
    </div>
    
    <div v-if="!loading && !hasMore && novels.length > 0" class="text-center py-8 text-gray-400 text-sm dark:text-gray-500">
      已加载全部 {{ novels.length }} 篇同人文
    </div>
  </div>
</template>

<style scoped>
.border-3 {
  border-width: 3px;
}
</style>
