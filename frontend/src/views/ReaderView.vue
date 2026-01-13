<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { novelApi } from '../services/api';
import type { Novel } from '../types/novel';

const route = useRoute();

const novel = ref<Novel | null>(null);
const chapterContent = ref<string>('');
const currentChapter = ref(1);
const loading = ref(true);
const error = ref<string | null>(null);

const source = route.params.source as string;
const id = route.params.id as string;

onMounted(async () => {
  await loadNovel();
  await loadChapter(1);
});

async function loadNovel() {
  try {
    novel.value = await novelApi.getDetail(source, id);
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载小说信息失败';
  }
}

async function loadChapter(chapter: number) {
  loading.value = true;
  try {
    chapterContent.value = await novelApi.getChapterContent(source, id, chapter);
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
  if (novel.value && currentChapter.value < (novel.value.chapterCount || 1)) {
    loadChapter(currentChapter.value + 1);
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header v-if="novel" class="bg-gradient-to-r from-primary to-secondary text-white py-8">
      <div class="max-w-3xl mx-auto px-4">
        <router-link to="/" class="text-white/80 text-sm hover:text-white no-underline">
          ← 返回列表
        </router-link>
        <h1 class="mt-4 mb-2 text-2xl md:text-3xl font-bold">{{ novel.title }}</h1>
        <p class="opacity-90 mb-2">作者: {{ novel.author }}</p>
        <div class="flex gap-4 text-sm opacity-80">
          <span class="bg-white/20 px-2 py-0.5 rounded">{{ source.toUpperCase() }}</span>
          <span v-if="novel.wordCount">{{ novel.wordCount.toLocaleString() }} 字</span>
          <span v-if="novel.chapterCount">{{ novel.chapterCount }} 章</span>
        </div>
      </div>
    </header>

    <!-- Chapter Navigation -->
    <nav v-if="novel" class="bg-white border-b border-gray-200 py-4 sticky top-16 z-40">
      <div class="max-w-3xl mx-auto px-4 flex justify-between items-center">
        <button 
          @click="prevChapter" 
          :disabled="currentChapter <= 1"
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ← 上一章
        </button>
        <span class="text-gray-600">
          第 {{ currentChapter }} / {{ novel.chapterCount || 1 }} 章
        </span>
        <button 
          @click="nextChapter" 
          :disabled="currentChapter >= (novel.chapterCount || 1)"
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          下一章 →
        </button>
      </div>
    </nav>

    <!-- Content -->
    <main class="py-8">
      <div class="max-w-3xl mx-auto px-4">
        <div v-if="loading" class="text-center py-16 text-gray-500">加载中...</div>
        <div v-else-if="error" class="text-center py-16 text-red-500">{{ error }}</div>
        <article 
          v-else 
          class="bg-white p-8 rounded-lg shadow-sm leading-relaxed text-lg"
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
          :href="novel.sourceUrl" 
          target="_blank" 
          class="text-primary hover:underline"
        >
          在 {{ source.toUpperCase() }} 查看原文
        </a>
        <button 
          @click="nextChapter" 
          :disabled="currentChapter >= (novel.chapterCount || 1)"
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          下一章 →
        </button>
      </div>
    </nav>
  </div>
</template>
