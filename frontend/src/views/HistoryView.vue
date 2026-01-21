<script setup lang="ts">
import { onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import NovelCard from '../components/novel/NovelCard.vue';
import type { Novel } from '../types/novel';
import { BookOpen } from 'lucide-vue-next';
import type { HistoryItem } from '../types/user_data';
import { useHistoryStore } from '../stores/history';

const historyStore = useHistoryStore();
const { items, loading, error } = storeToRefs(historyStore);

onMounted(async () => {
  // 进入页面时获取记录
  await historyStore.fetchHistory();
});

async function removeHistory(id: number) {
  // 删除记录
  await historyStore.removeHistory(id);
}

function toNovel(item: HistoryItem): Novel {
  // 转成小说结构
  return {
    id: item.novel_id,
    source: item.source as Novel['source'],
    title: item.title || '未命名作品',
    author: item.author || 'Unknown',
    summary: '',
    tags: [],
    rating: undefined,
    word_count: undefined,
    chapter_count: undefined,
    kudos: undefined,
    hits: undefined,
    published_at: '',
    updated_at: item.last_read_at,
    source_url: item.source_url || '',
    cover_image: item.cover_url,
    is_complete: undefined,
  };
}

function formatLastRead(date: string) {
  // 格式化时间
  if (!date) return '未知';
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return '未知';
  return parsed.toLocaleString('zh-CN');
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
    <header class="bg-linear-to-r from-primary to-secondary text-white py-12 text-center dark:bg-none dark:bg-gray-800 dark:border-gray-700 transition-colors duration-300 shadow-sm border-b border-transparent">
      <h1 class="text-3xl font-bold mb-2 flex items-center justify-center gap-3">
        <BookOpen class="w-8 h-8" /> 阅读记录
      </h1>
      <p>共 {{ items.length }} 条记录</p>
    </header>

    <main class="py-8">
      <div class="max-w-7xl mx-auto px-4">
        <div v-if="loading" class="text-center py-16 text-gray-500 dark:text-gray-400">加载中...</div>

        <div v-else-if="error" class="text-center text-red-500 p-8 bg-red-50 rounded-lg dark:bg-red-900/20 dark:text-red-400">
          {{ error }}
        </div>

        <div v-else-if="items.length === 0" class="text-center py-16">
          <p class="text-gray-500 mb-6 dark:text-gray-400">还没有阅读记录</p>
          <router-link to="/" class="btn-primary">去发现好文</router-link>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <div v-for="item in items" :key="item.id" class="relative group">
            <NovelCard
              :novel="toNovel(item)"
              :footer-note="`最近阅读: ${formatLastRead(item.last_read_at)}`"
              :show-favorite-action="false"
            />
            <button
              class="absolute top-2 right-2 px-3 py-1 bg-red-500/90 text-white text-sm rounded
                     opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
              @click="removeHistory(item.id)"
            >
              移除记录
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
