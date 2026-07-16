<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue';
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router';
import { novelApi } from '@services/api';
import type { Novel } from '@app-types/novel';
import { useUserStore } from '@stores/user';
import { useFavoritesStore } from '@stores/favorites';
import { useHistoryStore } from '@stores/history';
import {
  ArrowLeft,
  ArrowRight,
  ArrowUpBold,
  Bottom,
  Download,
  Loading,
  Star,
  StarFilled,
  Top,
} from '@element-plus/icons-vue';

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
      novel.value.published_at = novel.value.published_at || cached.published_at || '';
      novel.value.updated_at = novel.value.updated_at || cached.updated_at;
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
      published_at: cached?.published_at || '',
      updated_at: cached?.updated_at,
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
        published_at: novel.value.published_at || undefined,
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
  <div class="reader-page min-h-screen">
    <header v-if="novel" class="reader-hero">
      <div class="reader-shell">
        <el-button link :icon="ArrowLeft" class="reader-back" @click="goBack">
          返回列表
        </el-button>

        <div class="reader-heading">
          <div>
            <h1>{{ novel.title }}</h1>
            <p>作者：{{ novel.author }}</p>
          </div>
          <el-tag type="info" round>{{ source.toUpperCase() }}</el-tag>
        </div>

        <div class="reader-actions">
          <el-link :href="novel.source_url" target="_blank" underline="never" class="source-link">
            在 {{ source.toUpperCase() }} 查看原文
          </el-link>
          <el-button
            round
            size="small"
            :icon="isFavorite ? StarFilled : Star"
            :loading="favoriteLoading"
            @click="toggleFavorite"
          >
            {{ isFavorite ? '已收藏' : '收藏' }}
          </el-button>
          <el-button
            round
            size="small"
            :icon="Download"
            :loading="downloading"
            title="下载 PDF"
            @click="handleDownload"
          >
            下载
          </el-button>
        </div>

        <div class="reader-meta">
          <span v-if="novel.word_count">{{ novel.word_count.toLocaleString() }} 字</span>
          <span v-if="novel.chapter_count">{{ novel.chapter_count }} 章</span>
        </div>
      </div>
    </header>

    <nav v-if="novel" class="chapter-nav-wrap">
      <div class="reader-shell chapter-nav">
        <el-button
          plain
          type="primary"
          :icon="ArrowLeft"
          :disabled="currentChapter <= 1"
          @click="prevChapter"
        >
          上一章
        </el-button>
        <el-tag round effect="plain" size="large">
          第 {{ currentChapter }} / {{ novel.chapter_count || 1 }} 章
        </el-tag>
        <el-button
          plain
          type="primary"
          :icon="ArrowRight"
          :disabled="currentChapter >= (novel.chapter_count || 1)"
          @click="nextChapter"
        >
          下一章
        </el-button>
      </div>
    </nav>

    <main class="reader-main">
      <div class="reader-content-shell">
        <el-card v-if="loading" shadow="never">
          <div v-if="isRetrying" class="retry-state">
            <el-icon class="is-loading" :size="30"><Loading /></el-icon>
            <strong>正在自动重试（{{ retryCount }}/{{ maxRetries }}）</strong>
            <span>Bilibili 风控触发，请稍候</span>
          </div>
          <el-skeleton v-else :rows="10" animated />
        </el-card>

        <el-result v-else-if="error" icon="error" title="章节加载失败" :sub-title="error" />

        <article v-else ref="contentRef" class="reader-content" v-html="chapterContent"></article>
      </div>
    </main>

    <nav v-if="novel && !loading" class="chapter-nav-wrap chapter-nav-bottom">
      <div class="reader-shell chapter-nav">
        <el-button
          plain
          type="primary"
          :icon="ArrowLeft"
          :disabled="currentChapter <= 1"
          @click="prevChapter"
        >
          上一章
        </el-button>
        <el-tag round type="info">{{ source.toUpperCase() }}</el-tag>
        <el-button
          plain
          type="primary"
          :icon="ArrowRight"
          :disabled="currentChapter >= (novel.chapter_count || 1)"
          @click="nextChapter"
        >
          下一章
        </el-button>
      </div>
    </nav>

    <div class="reader-float">
      <el-popover
        v-model:visible="isScrollNavOpen"
        placement="top-end"
        trigger="click"
        :width="150"
      >
        <template #reference>
          <el-button
            type="primary"
            circle
            size="large"
            :icon="isScrollNavOpen ? Bottom : ArrowUpBold"
            :title="isScrollNavOpen ? '收起' : '快速滚动'"
          />
        </template>
        <el-space direction="vertical" fill :size="4">
          <el-button text :icon="Top" style="width: 100%; justify-content: flex-start" @click="scrollToTop">
            回到顶部
          </el-button>
          <el-button text :icon="Bottom" style="width: 100%; justify-content: flex-start" @click="scrollToBottom">
            直达底部
          </el-button>
        </el-space>
      </el-popover>
    </div>
  </div>
</template>

<style scoped>
.reader-page {
  background: var(--el-bg-color-page);
}

.reader-shell {
  width: min(920px, calc(100% - 32px));
  margin: 0 auto;
}

.reader-hero {
  padding: 28px 0 30px;
  color: var(--el-text-color-primary);
  background: var(--el-color-primary);
}

.reader-back {
  --el-button-text-color: var(--el-text-color-primary);
  --el-button-hover-text-color: var(--el-text-color-primary);
}

.source-link {
  --el-link-text-color: var(--el-text-color-primary);
  --el-link-hover-text-color: var(--el-text-color-primary);
}

.reader-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-top: 18px;
}

.reader-heading > div {
  min-width: 0;
  overflow-wrap: anywhere;
}

.reader-heading h1 {
  font-size: clamp(1.65rem, 4vw, 2.35rem);
  line-height: 1.25;
}

.reader-heading p {
  margin: 10px 0 0;
  color: var(--el-text-color-regular);
}

.reader-actions,
.reader-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 18px;
}

.reader-meta {
  gap: 18px;
  color: var(--el-text-color-regular);
  font-size: 0.875rem;
}

.chapter-nav-wrap {
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
}

.chapter-nav-bottom {
  margin-top: 24px;
  border-top: 1px solid var(--el-border-color-lighter);
  border-bottom: 0;
}

.chapter-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 0;
}

.reader-main {
  padding: 38px 0 18px;
}

.reader-content-shell {
  width: min(780px, calc(100% - 32px));
  margin: 0 auto;
}

.reader-content {
  padding: 40px 32px;
  background: var(--el-bg-color);
}

.retry-state {
  display: flex;
  min-height: 220px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--el-text-color-regular);
}

.reader-float {
  position: fixed;
  z-index: 50;
  right: 24px;
  bottom: 24px;
}

@media (max-width: 640px) {
  .reader-hero {
    padding-top: 20px;
  }

  .reader-heading {
    flex-direction: column;
    gap: 12px;
  }

  .chapter-nav {
    gap: 8px;
  }

  .chapter-nav :deep(.el-button) {
    padding-inline: 10px;
  }

  .chapter-nav :deep(.el-tag) {
    max-width: 42%;
  }

  .reader-main {
    padding-top: 24px;
  }

  .reader-content-shell {
    width: min(100% - 20px, 780px);
  }

  .reader-content {
    padding: 24px 20px;
  }

  .reader-float {
    right: 16px;
    bottom: 16px;
  }
}
</style>
