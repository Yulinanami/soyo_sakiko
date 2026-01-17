<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useFavoritesStore } from '../stores/favorites';
import NovelCard from '../components/novel/NovelCard.vue';
import { Heart } from 'lucide-vue-next';
import type { Novel } from '../types/novel';

interface FavoriteItem {
  id: number;
  novel_id: string;
  source: string;
  title: string;
  author?: string;
  cover_url?: string;
  source_url?: string;
  created_at: string;
}

const favoritesStore = useFavoritesStore();
const favorites = computed(() => favoritesStore.items);
const loading = computed(() => favoritesStore.loading);
const error = computed(() => favoritesStore.error);

onMounted(async () => {
  await favoritesStore.fetchFavorites(true);
});

async function removeFavorite(id: number) {
  try {
    const target = favoritesStore.items.find((item) => item.id === id);
    if (target) {
      await favoritesStore.removeFavoriteByKey(target.source, target.novel_id);
    }
  } catch (err) {
    console.warn('取消收藏失败', err);
  }
}

function toNovel(fav: FavoriteItem): Novel {
  return {
    id: fav.novel_id,
    source: fav.source as Novel['source'],
    title: fav.title,
    author: fav.author || 'Unknown',
    summary: '',
    tags: [],
    published_at: fav.created_at || '',
    source_url: fav.source_url || '',
    cover_image: fav.cover_url,
  };
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
    <header class="bg-gradient-to-r from-primary to-secondary text-white py-12 text-center dark:from-primary-dark dark:to-secondary-dark transition-colors duration-300">
      <h1 class="text-3xl font-bold mb-2 flex items-center justify-center gap-3">
        <Heart class="w-8 h-8" /> 收藏
      </h1>
      <p>共收藏 {{ favorites.length }} 篇小说</p>
    </header>
    
    <main class="py-8">
      <div class="max-w-7xl mx-auto px-4">
        <div v-if="loading" class="text-center py-16 text-gray-500 dark:text-gray-400">加载中...</div>
        
        <div v-else-if="error" class="text-center text-red-500 p-8 bg-red-50 rounded-lg dark:bg-red-900/20 dark:text-red-400">
          {{ error }}
        </div>
        
        <div v-else-if="favorites.length === 0" class="text-center py-16">
          <p class="text-gray-500 mb-6 dark:text-gray-400">还没有收藏任何小说</p>
          <router-link to="/" class="btn-primary">去发现好文</router-link>
        </div>
        
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <div v-for="fav in favorites" :key="fav.id" class="relative group">
            <NovelCard :novel="toNovel(fav)" :show-favorite-action="false" />
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
