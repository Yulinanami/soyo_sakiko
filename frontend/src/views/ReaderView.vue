<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { novelApi, historyApi } from '../services/api';
import type { Novel } from '../types/novel';
import { useUserStore } from '../stores/user';
import { useFavoritesStore } from '../stores/favorites';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const favoritesStore = useFavoritesStore();

const novel = ref<Novel | null>(null);
const chapterContent = ref<string>('');
const currentChapter = ref(1);
const loading = ref(true);
const error = ref<string | null>(null);
const contentRef = ref<HTMLElement | null>(null);
const favoriteLoading = ref(false);
const isFavorite = computed(() => (novel.value ? favoritesStore.isFavorite(novel.value) : false));

const source = route.params.source as string;
const id = route.params.id as string;
const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000/api').replace(/\/+$/, '');
const cacheKey = `soyosaki:novel:${source}:${id}`;

onMounted(async () => {
  if (userStore.isLoggedIn) {
    favoritesStore.fetchFavorites();
  }
  await loadNovel();
  // Always try to load chapter content, even if novel detail failed
  await loadChapter(1);
});

async function loadNovel() {
  try {
    novel.value = await novelApi.getDetail(source, id);
    const cached = readCachedNovel();
    if (cached && novel.value) {
      if (!novel.value.title || novel.value.title === 'Lofter 文章' || novel.value.title === '文章') {
        novel.value.title = cached.title || novel.value.title;
      }
      if (!novel.value.author || novel.value.author === 'Unknown') {
        novel.value.author = cached.author || novel.value.author;
      }
      novel.value.cover_image = novel.value.cover_image || cached.cover_image;
      novel.value.source_url = novel.value.source_url || cached.source_url || novel.value.source_url;
    }
  } catch (err) {
    // For Lofter and other sources where detail might not be available,
    // we just log but don't block - we'll still try to load the chapter
    console.warn('Could not load novel detail:', err);
    
    const cached = readCachedNovel();

    // Generate source URL for Lofter
    let sourceUrl = '';
    if (source === 'lofter' && id.includes(':')) {
      const [blogName, postId] = id.split(':', 2);
      sourceUrl = `https://${blogName}.lofter.com/post/${postId}`;
    }

    // Create a minimal novel object for display
    novel.value = {
      id: id,
      source: source as any,
      title: cached?.title || (source === 'lofter' ? 'Lofter 文章' : '文章'),
      author: cached?.author || 'Unknown',
      author_url: '',
      summary: '',
      tags: cached?.tags || [],
      word_count: cached?.word_count,
      chapter_count: cached?.chapter_count || 1,
      kudos: cached?.kudos,
      hits: cached?.hits,
      rating: cached?.rating,
      published_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      source_url: cached?.source_url || sourceUrl,
      cover_image: cached?.cover_image,
      is_complete: cached?.is_complete ?? true,
    };
  }
}

async function loadChapter(chapter: number) {
  loading.value = true;
  error.value = null;
  let shouldApplyLoaders = false;
  try {
    const rawContent = await novelApi.getChapterContent(source, id, chapter);
    chapterContent.value = normalizeContent(rawContent);
    currentChapter.value = chapter;
    shouldApplyLoaders = true;
    await recordHistory(chapter);
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载章节内容失败';
  } finally {
    loading.value = false;
    if (shouldApplyLoaders) {
      await nextTick();
      applyImageLoaders();
    }
  }
}

async function recordHistory(chapter: number) {
  if (!userStore.isLoggedIn || !novel.value) {
    return;
  }
  const totalChapters = novel.value.chapter_count || chapter;
  const progress = totalChapters
    ? Math.min(100, Math.round((chapter / totalChapters) * 100))
    : 0;
  try {
    await historyApi.record({
      novel_id: novel.value.id,
      source: novel.value.source,
      title: novel.value.title,
      author: novel.value.author,
      cover_url: novel.value.cover_image,
      source_url: novel.value.source_url,
      last_chapter: chapter,
      progress,
    });
  } catch {
    // Ignore history errors to avoid blocking reading.
  }
}

function prevChapter() {
  if (currentChapter.value > 1) {
    loadChapter(currentChapter.value - 1);
  }
}

function nextChapter() {
  if (novel.value && currentChapter.value < (novel.value.chapter_count || 1)) {
    loadChapter(currentChapter.value + 1);
  }
}

function normalizeContent(content: string) {
  if (!content) return content;
  return content
    .replace(/src=(['"])\/api\/([^'"]+)/g, `src=$1${API_BASE}/$2`)
    .replace(/href=(['"])\/api\/([^'"]+)/g, `href=$1${API_BASE}/$2`);
}

function applyImageLoaders() {
  if (!contentRef.value) return;
  const images = Array.from(contentRef.value.querySelectorAll('img'));
  images.forEach((img) => {
    let wrapper = img.parentElement;
    if (!wrapper || !wrapper.classList.contains('img-loading-wrapper')) {
      wrapper = document.createElement('span');
      wrapper.className = 'img-loading-wrapper';
      const parent = img.parentElement;
      if (parent) {
        parent.insertBefore(wrapper, img);
      }
      wrapper.appendChild(img);
    }

    const markLoaded = () => wrapper?.classList.add('loaded');
    if (img.complete && img.naturalWidth > 0) {
      markLoaded();
    } else {
      img.addEventListener('load', markLoaded, { once: true });
      img.addEventListener('error', markLoaded, { once: true });
    }
  });
}

function readCachedNovel() {
  try {
    const raw = sessionStorage.getItem(cacheKey);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function goBack() {
  if (window.history.length > 1) {
    router.back();
  } else {
    router.push({ name: 'home' });
  }
}

async function toggleFavorite() {
  if (!userStore.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: route.fullPath, reason: 'favorites' } });
    return;
  }
  if (!novel.value || favoriteLoading.value) return;
  favoriteLoading.value = true;
  try {
    await favoritesStore.toggleFavorite(novel.value);
  } finally {
    favoriteLoading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header v-if="novel" class="bg-soyo text-white py-8">
      <div class="max-w-3xl mx-auto px-4">
        <button
          type="button"
          @click="goBack"
          class="text-white/80 text-sm hover:text-white no-underline"
        >
          ← 返回列表
        </button>
        <h1 class="mt-4 mb-2 text-2xl md:text-3xl font-bold">{{ novel.title }}</h1>
        <p class="opacity-90 mb-2">作者: {{ novel.author }}</p>
        <div class="flex flex-wrap items-center gap-3 mb-2">
          <a
            :href="novel.source_url"
            target="_blank"
            class="inline-block text-sm text-white/90 hover:text-white underline-offset-4 hover:underline"
          >
            在 {{ source.toUpperCase() }} 查看原文
          </a>
          <button
            type="button"
            class="text-xs px-3 py-1 rounded-full bg-white/20 text-white hover:bg-white/30"
            @click="toggleFavorite"
          >
            <span v-if="favoriteLoading" class="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            <span v-else>{{ isFavorite ? '已收藏' : '收藏' }}</span>
          </button>
        </div>
        <div class="flex gap-4 text-sm opacity-80">
          <span class="bg-white/20 px-2 py-0.5 rounded">{{ source.toUpperCase() }}</span>
          <span v-if="novel.word_count">{{ novel.word_count.toLocaleString() }} 字</span>
          <span v-if="novel.chapter_count">{{ novel.chapter_count }} 章</span>
        </div>
      </div>
    </header>

    <!-- Chapter Navigation -->
    <nav v-if="novel" class="bg-white border-b border-gray-200 py-4">
      <div class="max-w-3xl mx-auto px-4 flex justify-between items-center">
        <button 
          @click="prevChapter" 
          :disabled="currentChapter <= 1"
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ← 上一章
        </button>
        <span class="text-gray-600">
          第 {{ currentChapter }} / {{ novel.chapter_count || 1 }} 章
        </span>
        <button 
          @click="nextChapter" 
          :disabled="currentChapter >= (novel.chapter_count || 1)"
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          下一章 →
        </button>
      </div>
    </nav>

    <!-- Content -->
    <main class="py-12 bg-gray-50">
      <div class="max-w-2xl mx-auto px-6">
        <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>
        <div v-else-if="error" class="text-center py-16 text-red-500">{{ error }}</div>
        <article 
          v-else 
          ref="contentRef"
          class="reader-content bg-white px-10 py-12 rounded-xl shadow-sm"
          v-html="chapterContent"
        ></article>
      </div>
    </main>

    <!-- Bottom Navigation -->
    <nav v-if="novel && !loading" class="bg-white border-t border-gray-200 py-4 mt-8">
      <div class="max-w-3xl mx-auto px-4 flex justify-between items-center">
        <button 
          @click="prevChapter" 
          :disabled="currentChapter <= 1"
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ← 上一章
        </button>
        <span class="text-gray-500 text-sm">{{ source.toUpperCase() }}</span>
        <button 
          @click="nextChapter" 
          :disabled="currentChapter >= (novel.chapter_count || 1)"
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          下一章 →
        </button>
      </div>
    </nav>
  </div>
</template>
