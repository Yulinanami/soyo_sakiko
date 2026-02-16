<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue';
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router';
import { novelApi } from '@services/api';
import type { Novel } from '@app-types/novel';
import { useUserStore } from '@stores/user';
import { useFavoritesStore } from '@stores/favorites';
import { useHistoryStore } from '@stores/history';
import { Download, ChevronUp } from 'lucide-vue-next';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const favoritesStore = useFavoritesStore();
const historyStore = useHistoryStore();

const novel = ref<Novel | null>(null);
const chapterContent = ref<string>('');
const currentChapter = ref(1);
const loading = ref(true);
const error = ref<string | null>(null);
const contentRef = ref<HTMLElement | null>(null);
const favoriteLoading = ref(false);
const downloading = ref(false);
const isFavorite = computed(() => (novel.value ? favoritesStore.isFavorite(novel.value) : false));

// 自动重试相关状态
const retryCount = ref(0);
const maxRetries = 5;
const isRetrying = ref(false);

const source = route.params.source as string;
const id = route.params.id as string;
const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000/api').replace(/\/+$/, '');
const cacheKey = `soyosaki:novel:${source}:${id}`;

onMounted(async () => {
  // 进入页面时加载数据
  if (userStore.isLoggedIn) {
    favoritesStore.fetchFavorites();
  }
  await loadNovel();
  await loadChapter(1);
});

async function loadNovel() {
  // 加载小说信息
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
    console.warn('Could not load novel detail:', err);

    const cached = readCachedNovel();

    let sourceUrl = '';
    if (source === 'lofter' && id.includes(':')) {
      const [blogName, postId] = id.split(':', 2);
      sourceUrl = `https://${blogName}.lofter.com/post/${postId}`;
    }

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
  // 加载章节内容
  loading.value = true;
  error.value = null;
  retryCount.value = 0;
  isRetrying.value = false;
  let shouldApplyLoaders = false;

  async function attemptLoad(): Promise<boolean> {
    try {
      const rawContent = await novelApi.getChapterContent(source, id, chapter);

      // 检查是否为 Bilibili 可重试错误 (-352, -401, -412)
      if (source === 'bilibili' && rawContent && typeof rawContent === 'string') {
        const retryablePattern = /获取失败:\s*(-352|-401|-412)/;
        if (retryablePattern.test(rawContent) && retryCount.value < maxRetries) {
          retryCount.value++;
          isRetrying.value = true;
          console.log(`Bilibili content retry ${retryCount.value}/${maxRetries}...`);
          await new Promise(resolve => setTimeout(resolve, 1500)); // 等待 1.5 秒
          return false; // 需要重试
        }
      }

      const content = source === 'ao3' ? formatAo3Content(rawContent) : rawContent;
      chapterContent.value = normalizeContent(content);
      currentChapter.value = chapter;
      shouldApplyLoaders = true;
      await recordHistory(chapter);
      return true; // 成功
    } catch (err) {
      // 网络错误也尝试重试（仅限 Bilibili）
      if (source === 'bilibili' && retryCount.value < maxRetries) {
        retryCount.value++;
        isRetrying.value = true;
        console.log(`Bilibili network retry ${retryCount.value}/${maxRetries}...`);
        await new Promise(resolve => setTimeout(resolve, 1500));
        return false; // 需要重试
      }
      error.value = err instanceof Error ? err.message : '加载章节内容失败';
      return true; // 不再重试
    }
  }

  // 执行加载（带重试）
  let done = false;
  while (!done) {
    done = await attemptLoad();
  }

  isRetrying.value = false;
  loading.value = false;
  if (shouldApplyLoaders) {
    await nextTick();
    applyImageLoaders();
  }
}

async function recordHistory(chapter: number) {
  // 记录阅读进度
  if (!userStore.isLoggedIn || !novel.value) {
    return;
  }
  const totalChapters = novel.value.chapter_count || chapter;
  const progress = totalChapters
    ? Math.min(100, Math.round((chapter / totalChapters) * 100))
    : 0;
  try {
    await historyStore.recordHistory(
      {
        novel_id: novel.value.id,
        source: novel.value.source,
        title: novel.value.title,
        author: novel.value.author,
        cover_url: novel.value.cover_image,
        source_url: novel.value.source_url,
        last_chapter: chapter,
        progress,
      },
      { silent: true }
    );
  } catch {
  }
}

function prevChapter() {
  // 切换到上一章
  if (currentChapter.value > 1) {
    loadChapter(currentChapter.value - 1);
  }
}

function nextChapter() {
  // 切换到下一章
  if (novel.value && currentChapter.value < (novel.value.chapter_count || 1)) {
    loadChapter(currentChapter.value + 1);
  }
}

function normalizeContent(content: string) {
  // 处理链接地址
  if (!content) return content;
  return content
    .replace(/src=(['"])\/api\/([^'"]+)/g, `src=$1${API_BASE}/$2`)
    .replace(/href=(['"])\/api\/([^'"]+)/g, `href=$1${API_BASE}/$2`);
}

function formatAo3Content(content: string) {
  // 处理 AO3 段落换行
  if (!content) return content;
  const hasBlocks =
    /<\/?(p|br|div|section|article|h\d|ul|ol|li|blockquote|pre|hr)\b/i.test(content);
  if (hasBlocks) return content;
  const normalized = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  const splitPattern = normalized.includes('\n\n') ? /\n{2,}/ : /\n+/;
  const blocks = normalized
    .split(splitPattern)
    .map((block) => block.trim())
    .filter(Boolean)
    .map((block) => `<p>${block.replace(/\n/g, '<br>')}</p>`);
  if (!blocks.length) {
    return normalized.replace(/\n/g, '<br>');
  }
  return blocks.join('<p class="ao3-gap"></p>');
}

function applyImageLoaders() {
  // 给图片加加载状态
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
  // 读取本地保存内容
  try {
    const raw = sessionStorage.getItem(cacheKey);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function goBack() {
  // 返回上一页
  if (window.history.length > 1) {
    router.back();
  } else {
    router.push({ name: 'home' });
  }
}

async function toggleFavorite() {
  // 切换收藏状态
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

function handleDownload() {
  if (!novel.value || downloading.value) return;
  downloading.value = true;
  const params = new URLSearchParams();
  params.set('title', novel.value.title);
  params.set('author', novel.value.author);
  const url = `${API_BASE}/download/${novel.value.source}/${novel.value.id}?${params.toString()}`;
  const link = document.createElement('a');
  link.href = url;
  link.target = '_blank';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  setTimeout(() => { downloading.value = false; }, 3000);
}

onBeforeRouteLeave(() => {
  // 离开时记录阅读信息
  if (novel.value) {
    sessionStorage.setItem('soyosaki:lastRead', JSON.stringify({
      source: novel.value.source,
      id: novel.value.id
    }));
  }
});

const isScrollNavOpen = ref(false);

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
  isScrollNavOpen.value = false;
}

function scrollToBottom() {
  window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
  isScrollNavOpen.value = false;
}
</script>

<template>
  <div class="min-h-screen bg-soyo-cream dark:bg-gray-900 transition-colors duration-300">
    <!-- 顶部信息 -->
    <header v-if="novel"
      class="relative z-10 bg-soyo text-white py-8 dark:bg-gray-800 transition-colors duration-300 shadow-sm">
      <div class="max-w-3xl mx-auto px-4">
        <button type="button" @click="goBack" class="text-white/80 text-sm hover:text-white no-underline">
          ← 返回列表
        </button>
        <h1 class="mt-4 mb-2 text-2xl md:text-3xl font-bold">{{ novel.title }}</h1>
        <p class="opacity-90 mb-2">作者: {{ novel.author }}</p>
        <div class="flex flex-wrap items-center gap-3 mb-2">
          <a :href="novel.source_url" target="_blank"
            class="inline-block text-sm text-white/90 hover:text-white underline-offset-4 hover:underline">
            在 {{ source.toUpperCase() }} 查看原文
          </a>
          <button type="button" class="text-xs px-3 py-1 rounded-full bg-white/20 text-white hover:bg-white/30"
            @click="toggleFavorite">
            <span v-if="favoriteLoading"
              class="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            <span v-else>{{ isFavorite ? '已收藏' : '收藏' }}</span>
          </button>
          <button type="button"
            class="text-xs px-3 py-1 rounded-full bg-white/20 text-white hover:bg-white/30 inline-flex items-center gap-1"
            @click="handleDownload" title="下载 PDF">
            <span v-if="downloading"
              class="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            <template v-else>
              <Download class="w-3.5 h-3.5" />
              <span>下载</span>
            </template>
          </button>
        </div>
        <div class="flex gap-4 text-sm opacity-80">
          <span class="bg-white/20 px-2 py-0.5 rounded">{{ source.toUpperCase() }}</span>
          <span v-if="novel.word_count">{{ novel.word_count.toLocaleString() }} 字</span>
          <span v-if="novel.chapter_count">{{ novel.chapter_count }} 章</span>
        </div>
      </div>
    </header>

    <!-- 章节导航 -->
    <nav v-if="novel" class="bg-soyo-cream border-b border-soyo-light/30 py-4 dark:bg-gray-800 dark:border-gray-700">
      <div class="max-w-3xl mx-auto px-4 flex justify-between items-center">
        <button @click="prevChapter" :disabled="currentChapter <= 1"
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-600 dark:hover:border-gray-500">
          ← 上一章
        </button>
        <span class="text-gray-600 dark:text-gray-300">
          第 {{ currentChapter }} / {{ novel.chapter_count || 1 }} 章
        </span>
        <button @click="nextChapter" :disabled="currentChapter >= (novel.chapter_count || 1)"
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-600 dark:hover:border-gray-500">
          下一章 →
        </button>
      </div>
    </nav>

    <!-- 正文内容 -->
    <main class="py-12 bg-soyo-cream dark:bg-gray-900 transition-colors duration-300">
      <div class="max-w-2xl mx-auto px-6">
        <div v-if="loading" class="text-center py-16 text-gray-500 dark:text-gray-400">
          <template v-if="isRetrying">
            <div class="flex flex-col items-center gap-2">
              <span
                class="inline-block w-6 h-6 border-2 border-sakiko border-t-transparent rounded-full animate-spin"></span>
              <span>正在自动重试 ({{ retryCount }}/{{ maxRetries }})...</span>
              <span class="text-xs text-gray-400">Bilibili 风控触发，请稍候</span>
            </div>
          </template>
          <template v-else>加载中...</template>
        </div>
        <div v-else-if="error" class="text-center py-16 text-red-500 dark:text-red-400">{{ error }}</div>
        <article v-else ref="contentRef"
          class="reader-content bg-soyo-cream/50 px-10 py-12 rounded-xl shadow-xl dark:bg-gray-800 dark:shadow-none transition-colors duration-300"
          v-html="chapterContent"></article>
      </div>
    </main>

    <!-- 底部导航 -->
    <nav v-if="novel && !loading"
      class="bg-soyo-cream border-t border-soyo-light/30 py-4 mt-8 dark:bg-gray-800 dark:border-gray-700">
      <div class="max-w-3xl mx-auto px-4 flex justify-between items-center">
        <button @click="prevChapter" :disabled="currentChapter <= 1"
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-600 dark:hover:border-gray-500">
          ← 上一章
        </button>
        <span class="text-gray-500 text-sm dark:text-gray-400">{{ source.toUpperCase() }}</span>
        <button @click="nextChapter" :disabled="currentChapter >= (novel.chapter_count || 1)"
          class="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-600 dark:hover:border-gray-500">
          下一章 →
        </button>
      </div>
    </nav>

    <!-- 浮动滚动按钮 -->
    <div class="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
      <transition enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 translate-y-4 scale-95" enter-to-class="opacity-100 translate-y-0 scale-100"
        leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100 translate-y-0 scale-100"
        leave-to-class="opacity-0 translate-y-4 scale-95">
        <div v-if="isScrollNavOpen"
          class="bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 py-2 px-3 min-w-[100px]">
          <button @click="scrollToTop"
            class="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-sakiko/10 hover:text-sakiko rounded-lg transition-colors">
            回到顶部
          </button>
          <button @click="scrollToBottom"
            class="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-sakiko/10 hover:text-sakiko rounded-lg transition-colors border-t border-gray-100 dark:border-gray-700 mt-1 pt-2">
            直达底部
          </button>
        </div>
      </transition>

      <button @click="isScrollNavOpen = !isScrollNavOpen"
        class="w-12 h-12 rounded-full bg-sakiko text-white shadow-lg hover:bg-sakiko/90 hover:shadow-xl transition-all duration-200 flex items-center justify-center"
        :class="{ 'rotate-180': isScrollNavOpen }" :title="isScrollNavOpen ? '收起' : '快速滚动'">
        <ChevronUp class="w-6 h-6 transition-transform duration-200" />
      </button>
    </div>
  </div>
</template>
