<script setup lang="ts">
import { onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import NovelCard from '../components/novel/NovelCard.vue';
import type { Novel } from '../types/novel';
import type { HistoryItem } from '../types/user_data';
import { useHistoryStore } from '../stores/history';

const historyStore = useHistoryStore();
const { items, loading, error } = storeToRefs(historyStore);

onMounted(async () => {
  await historyStore.fetchHistory();
});

async function removeHistory(id: number) {
  await historyStore.removeHistory(id);
}

function toNovel(item: HistoryItem): Novel {
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
  if (!date) return '未知';
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return '未知';
  return parsed.toLocaleString('zh-CN');
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-gradient-to-r from-primary to-secondary text-white py-12 text-center">
      <h1 class="text-3xl font-bold mb-2">📖 阅读记录</h1>
      <p>共 {{ items.length }} 条记录</p>
    </header>

    <main class="py-8">
      <div class="max-w-7xl mx-auto px-4">
        <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>

        <div v-else-if="error" class="text-center text-red-500 p-8 bg-red-50 rounded-lg">
          {{ error }}
        </div>

        <div v-else-if="items.length === 0" class="text-center py-16">
          <p class="text-gray-500 mb-6">还没有阅读记录</p>
          <router-link to="/" class="btn-primary">去发现好文</router-link>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
