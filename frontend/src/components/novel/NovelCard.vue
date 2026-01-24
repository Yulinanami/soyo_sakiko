<script setup lang="ts">
import { computed, onMounted, ref, toRef, watch } from 'vue';
import type { Novel } from '@app-types/novel';
import { useFavoritesStore } from '@stores/favorites';
import { useUserStore } from '@stores/user';
import { useRouter } from 'vue-router';
import ao3Logo from '@assets/ao3.png';
import pixivLogo from '@assets/pixiv.png';
import lofterLogo from '@assets/lofter.png';
import bilibiliLogo from '@assets/bilibili.png';
import { useNovelMeta } from '@composables/useNovelMeta';
import { FileText, BookOpen, Heart, AlignLeft } from 'lucide-vue-next';

const props = withDefaults(defineProps<{
  novel: Novel;
  showFavoriteAction?: boolean;
  footerNote?: string;
}>(), {
  showFavoriteAction: true,
  footerNote: '',
});

const favoritesStore = useFavoritesStore();
const userStore = useUserStore();
const router = useRouter();

const novelRef = toRef(props, 'novel');
const { formattedDate, truncatedSummary, isHighlightTag } = useNovelMeta(novelRef);

// 获取服务地址
const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/+$/, '');

// 设置来源图标
const sourceLogos: Record<string, string> = {
  ao3: ao3Logo,
  pixiv: pixivLogo,
  lofter: lofterLogo,
  bilibili: bilibiliLogo,
};

// 选择来源图标
const sourceLogo = computed(() => sourceLogos[props.novel.source]);

// 生成来源样式
const sourceClass = computed(() => {
  const classes: Record<string, string> = {
    ao3: 'bg-red-700 text-white',
    pixiv: 'bg-sakiko text-white',
    lofter: 'bg-soyo text-white',
    bilibili: 'bg-pink-500 text-white',
  };
  return classes[props.novel.source] || 'bg-gray-500 text-white';
});

// 准备封面地址
const lofterDomains = [
  'lf127.net',
  '126.net',
  'lofter.com',
  'imglf',
  'nos.netease.com',
  'nosdn.127.net',
  'netease.com',
];

const coverLoaded = ref(false);
const favoriteLoading = ref(false);
// 判断是否已收藏
const isFavorite = computed(() => favoritesStore.isFavorite(props.novel));
const isLastRead = ref(false);

onMounted(() => {
  // 读取上次阅读信息
  try {
    const raw = sessionStorage.getItem('soyosaki:lastRead');
    if (raw) {
      const last = JSON.parse(raw);
      if (last.source === props.novel.source && String(last.id) === String(props.novel.id)) {
        isLastRead.value = true;
      }
    }
  } catch { }
});

const coverImageUrl = computed(() => {
  // 处理封面地址
  if (!props.novel.cover_image) return null;
  const imageUrl = props.novel.cover_image;

  if (props.novel.source === 'pixiv' && imageUrl.includes('pximg.net')) {
    return `${API_BASE}/proxy/pixiv?url=${encodeURIComponent(imageUrl)}`;
  }

  if (props.novel.source === 'lofter') {
    if (imageUrl.startsWith(`${API_BASE}/proxy/lofter`)) {
      return imageUrl;
    }
    if (lofterDomains.some(domain => imageUrl.includes(domain))) {
      return `${API_BASE}/proxy/lofter?url=${encodeURIComponent(imageUrl)}`;
    }
  }

  if (props.novel.source === 'bilibili' && (imageUrl.includes('hdslb.com') || imageUrl.includes('bilibili.com'))) {
    return `${API_BASE}/proxy/bilibili?url=${encodeURIComponent(imageUrl)}`;
  }

  return imageUrl;
});

watch(coverImageUrl, () => {
  // 重置封面加载状态
  coverLoaded.value = false;
});

onMounted(() => {
  // 登录后加载收藏
  if (userStore.isLoggedIn && !favoritesStore.loaded) {
    favoritesStore.fetchFavorites();
  }
});

function rememberListScroll() {
  // 记录列表位置
  sessionStorage.setItem('soyosaki:listScrollY', String(window.scrollY));
  sessionStorage.setItem('soyosaki:preserveList', '1');
  try {
    const cacheKey = `soyosaki:novel:${props.novel.source}:${props.novel.id}`;
    const payload = {
      title: props.novel.title,
      author: props.novel.author,
      cover_image: props.novel.cover_image,
      source_url: props.novel.source_url,
      tags: props.novel.tags,
      rating: props.novel.rating,
      word_count: props.novel.word_count,
      chapter_count: props.novel.chapter_count,
      kudos: props.novel.kudos,
      hits: props.novel.hits,
      is_complete: props.novel.is_complete,
    };
    sessionStorage.setItem(cacheKey, JSON.stringify(payload));
  } catch {
  }
}

async function toggleFavorite(event: Event) {
  // 切换收藏
  event.preventDefault();
  event.stopPropagation();
  if (!userStore.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: router.currentRoute.value.fullPath, reason: 'favorites' } });
    return;
  }
  if (favoriteLoading.value) return;
  favoriteLoading.value = true;
  try {
    await favoritesStore.toggleFavorite(props.novel);
  } finally {
    favoriteLoading.value = false;
  }
}
</script>

<template>
  <article
    class="card overflow-hidden hover:-translate-y-1 transition-transform duration-200 dark:bg-gray-800 dark:border dark:border-gray-700 flex flex-col h-full">
    <router-link :to="`/novel/${novel.source}/${novel.id}`" class="no-underline text-inherit flex flex-col h-full"
      @click="rememberListScroll">
      <div class="relative shrink-0">
        <!-- 封面 -->
        <div v-if="coverImageUrl" class="h-40 overflow-hidden bg-sakiko-pale relative">
          <div v-if="!coverLoaded" class="absolute inset-0 flex items-center justify-center bg-sakiko-pale/70">
            <span class="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          </div>
          <img :src="coverImageUrl" :alt="novel.title"
            class="w-full h-full object-cover transition-opacity duration-200"
            :class="coverLoaded ? 'opacity-100' : 'opacity-0'" @load="coverLoaded = true" @error="coverLoaded = true" />
        </div>
        <div v-else class="h-40 bg-sakiko-light flex items-center justify-center">
          <img v-if="sourceLogo" :src="sourceLogo" alt="source" class="w-16 h-16 object-contain opacity-60" />
          <FileText v-else class="w-16 h-16 text-gray-400 opacity-60" />
        </div>

        <!-- 最近阅读 -->
        <div v-if="isLastRead"
          class="absolute top-0 right-0 bg-soyo text-white text-xs px-2 py-1 rounded-bl-lg shadow-sm font-medium z-10">
          刚才看过
        </div>
      </div>

      <!-- 内容 -->
      <div class="p-4 flex flex-col flex-1">
        <div class="flex gap-2 mb-3 shrink-0">
          <span :class="['flex items-center gap-1 text-xs px-2 py-0.5 rounded', sourceClass]">
            <img v-if="sourceLogo" :src="sourceLogo" alt="" class="w-3 h-3 object-contain" />
            {{ novel.source.toUpperCase() }}
          </span>
          <span v-if="novel.rating" class="text-xs px-2 py-0.5 rounded bg-yellow-400 text-gray-800">
            {{ novel.rating }}
          </span>
        </div>

        <h3 class="text-lg font-semibold mb-1 line-clamp-2 dark:text-gray-100 shrink-0">{{ novel.title }}</h3>
        <p class="text-sm text-gray-600 mb-3 dark:text-gray-400 shrink-0">{{ novel.author }}</p>

        <p class="text-sm text-gray-500 leading-relaxed mb-3 dark:text-gray-400 line-clamp-3 flex-1">{{ truncatedSummary
        }}</p>

        <div class="flex flex-wrap gap-1.5 mb-3 shrink-0">
          <span v-for="tag in novel.tags.slice(0, 5)" :key="tag" :class="[
            'text-xs px-2 py-0.5 rounded-full inline-flex items-center justify-center',
            isHighlightTag(tag) ? 'tag-highlight' : 'tag'
          ]">
            {{ tag }}
          </span>
          <span v-if="novel.tags.length > 5"
            class="text-xs px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 dark:text-gray-300 inline-flex items-center justify-center">
            +{{ novel.tags.length - 5 }}
          </span>
        </div>

        <div class="flex flex-wrap gap-3 text-xs text-gray-500 dark:text-gray-400 shrink-0 mt-auto">
          <span v-if="novel.word_count" class="flex items-center gap-1">
            <AlignLeft class="w-3.5 h-3.5" /> {{ novel.word_count.toLocaleString() }} 字
          </span>
          <span v-if="novel.chapter_count" class="flex items-center gap-1">
            <BookOpen class="w-3.5 h-3.5" /> {{ novel.chapter_count }} 章
          </span>
          <span v-if="novel.kudos" class="flex items-center gap-1">
            <Heart class="w-3.5 h-3.5" /> {{ novel.kudos }}
          </span>
          <span class="ml-auto">{{ formattedDate }}</span>
        </div>

        <div class="mt-3 flex items-center gap-2 shrink-0">
          <span v-if="novel.is_complete !== undefined" :class="[
            'text-xs px-3 py-1 rounded-full',
            novel.is_complete ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400'
          ]">
            {{ novel.is_complete ? '已完结' : '连载中' }}
          </span>
          <button v-if="showFavoriteAction" type="button"
            class="text-xs px-3 py-1 rounded-full bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-600"
            :title="userStore.isLoggedIn ? (isFavorite ? '取消收藏' : '收藏') : '登录后可收藏'" @click="toggleFavorite">
            <span v-if="favoriteLoading"
              class="inline-block w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></span>
            <span v-else>{{ isFavorite ? '已收藏' : '收藏' }}</span>
          </button>
        </div>
        <div v-if="footerNote" class="mt-2 text-xs text-gray-500 text-right shrink-0">
          {{ footerNote }}
        </div>
      </div>
    </router-link>
  </article>
</template>
