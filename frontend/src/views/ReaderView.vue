<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { novelApi } from '../services/api';
import type { Novel } from '../types/novel';

const route = useRoute();
const router = useRouter();

const novel = ref<Novel | null>(null);
const chapterContent = ref<string>('');
const currentChapter = ref(1);
const loading = ref(true);
const error = ref<string | null>(null);

const source = route.params.source as string;
const id = route.params.id as string;
const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000/api').replace(/\/+$/, '');

onMounted(async () => {
  await loadNovel();
  // Always try to load chapter content, even if novel detail failed
  await loadChapter(1);
});

async function loadNovel() {
  try {
    novel.value = await novelApi.getDetail(source, id);
  } catch (err) {
    // For Lofter and other sources where detail might not be available,
    // we just log but don't block - we'll still try to load the chapter
    console.warn('Could not load novel detail:', err);
    
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
      title: source === 'lofter' ? 'Lofter 文章' : '文章',
      author: 'Unknown',
      author_url: '',
      summary: '',
      tags: [],
      word_count: undefined,
      chapter_count: 1,
      kudos: undefined,
      hits: undefined,
      rating: undefined,
      published_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      source_url: sourceUrl,
      cover_image: undefined,
      is_complete: true,
    };
  }
}

async function loadChapter(chapter: number) {
  loading.value = true;
  error.value = null;
  try {
    const rawContent = await novelApi.getChapterContent(source, id, chapter);
    chapterContent.value = normalizeContent(rawContent);
    currentChapter.value = chapter;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载章节内容失败';
  } finally {
    loading.value = false;
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

function goBack() {
  if (window.history.length > 1) {
    router.back();
  } else {
    router.push({ name: 'home' });
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
        <a 
          :href="novel.source_url" 
          target="_blank" 
          class="text-soyo-dark hover:underline"
        >
          在 {{ source.toUpperCase() }} 查看原文
        </a>
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
