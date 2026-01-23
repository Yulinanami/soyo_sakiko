<script setup lang="ts">
import NovelCard from '@components/novel/NovelCard.vue';
import type { Novel } from '@app-types/novel';

const props = defineProps<{
  novels: Novel[];
  loading: boolean;
  hasMore: boolean;
  pageBreaks: number[];  // 分页位置数组
}>();

const emit = defineEmits<{
  (e: 'load-more'): void;
}>();

// 计算哪个位置是哪一页的起点
function getPageNumber(index: number): number | null {
  const breakIndex = props.pageBreaks.indexOf(index);
  if (breakIndex !== -1) {
    return breakIndex + 2;  // 第一次加载更多是第2页
  }
  return null;
}
</script>

<template>
  <div class="w-full">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      <template v-for="(novel, index) in novels" :key="`${novel.source}-${novel.id}`">
        <!-- 分页分隔线 -->
        <div v-if="getPageNumber(index)" class="col-span-full flex items-center gap-4 py-4 my-2">
          <div class="flex-1 h-px bg-linear-to-r from-transparent via-sakiko/30 to-transparent dark:via-sakiko/20">
          </div>
          <span
            class="text-sm font-medium text-sakiko dark:text-sakiko-pale px-3 py-1 rounded-full bg-sakiko/10 dark:bg-sakiko/5">
            第 {{ getPageNumber(index) }} 页
          </span>
          <div class="flex-1 h-px bg-linear-to-r from-transparent via-sakiko/30 to-transparent dark:via-sakiko/20">
          </div>
        </div>

        <NovelCard :novel="novel" />
      </template>
    </div>

    <div v-if="loading" class="flex items-center justify-center gap-3 py-12 text-gray-500 dark:text-gray-400">
      <div class="w-6 h-6 border-3 border-gray-200 border-t-primary rounded-full animate-spin dark:border-gray-700">
      </div>
      <span>加载中...</span>
    </div>

    <div v-if="!loading && hasMore" class="flex flex-col items-center gap-3 py-8">
      <span class="text-sm text-gray-500 dark:text-gray-400">已加载 {{ novels.length }} 篇同人文</span>
      <button @click="emit('load-more')" class="btn-primary">
        加载更多
      </button>
    </div>

    <div v-if="!loading && !hasMore && novels.length > 0"
      class="text-center py-8 text-gray-400 text-sm dark:text-gray-500">
      已加载全部 {{ novels.length }} 篇同人文
    </div>
  </div>
</template>

<style scoped>
.border-3 {
  border-width: 3px;
}
</style>
