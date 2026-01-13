<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { favoritesApi } from '../services/api';
import NovelCard from '../components/novel/NovelCard.vue';
import type { Novel } from '../types/novel';

interface FavoriteItem {
  id: number;
  novelId: string;
  source: string;
  title: string;
  author: string;
  coverUrl?: string;
  createdAt: string;
}

const favorites = ref<FavoriteItem[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    favorites.value = await favoritesApi.getAll();
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载收藏失败';
  } finally {
    loading.value = false;
  }
});

async function removeFavorite(id: number) {
  try {
    await favoritesApi.remove(id);
    favorites.value = favorites.value.filter(f => f.id !== id);
  } catch (err) {
    error.value = err instanceof Error ? err.message : '取消收藏失败';
  }
}

function toNovel(fav: FavoriteItem): Partial<Novel> {
  return {
    id: fav.novelId,
    source: fav.source as Novel['source'],
    title: fav.title,
    author: fav.author,
    coverImage: fav.coverUrl,
  };
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-gradient-to-r from-primary to-secondary text-white py-12 text-center">
      <h1 class="text-3xl font-bold mb-2">❤️ 我的收藏</h1>
      <p>共收藏 {{ favorites.length }} 篇小说</p>
    </header>
    
    <main class="py-8">
      <div class="max-w-7xl mx-auto px-4">
        <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>
        
        <div v-else-if="error" class="text-center text-red-500 p-8 bg-red-50 rounded-lg">
          {{ error }}
        </div>
        
        <div v-else-if="favorites.length === 0" class="text-center py-16">
          <p class="text-gray-500 mb-6">还没有收藏任何小说</p>
          <router-link to="/" class="btn-primary">去发现好文</router-link>
        </div>
        
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div v-for="fav in favorites" :key="fav.id" class="relative group">
            <NovelCard :novel="toNovel(fav) as Novel" />
            <button 
              class="absolute top-2 right-2 px-3 py-1 bg-red-500/90 text-white text-sm rounded
                     opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
              @click="removeFavorite(fav.id)"
            >
              取消收藏
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
