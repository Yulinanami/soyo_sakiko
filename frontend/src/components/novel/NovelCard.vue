<script setup lang="ts">
import { computed, onMounted, ref, toRef } from 'vue';
import type { Novel } from '@app-types/novel';
import { useFavoritesStore } from '@stores/favorites';
import { useUserStore } from '@stores/user';
import { useRouter } from 'vue-router';
import ao3Logo from '@assets/ao3.png';
import pixivLogo from '@assets/pixiv.png';
import lofterLogo from '@assets/lofter.png';
import bilibiliLogo from '@assets/bilibili.png';
import { useNovelMeta } from '@composables/useNovelMeta';
import { ElButton, ElCard, ElIcon, ElImage, ElRow, ElSkeletonItem, ElSpace, ElTag, ElText } from 'element-plus';
import { Calendar, Document, Download, Reading, Star, StarFilled } from '@element-plus/icons-vue';

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
const { formattedPublishedDate, truncatedSummary, isHighlightTag } = useNovelMeta(novelRef);

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

const favoriteLoading = ref(false);
const downloading = ref(false);
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
      published_at: props.novel.published_at,
      updated_at: props.novel.updated_at,
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

async function handleDownload(event: Event) {
  // 下载 PDF
  event.preventDefault();
  event.stopPropagation();
  if (downloading.value) return;
  downloading.value = true;
  try {
    const params = new URLSearchParams();
    params.set('title', props.novel.title);
    params.set('author', props.novel.author);
    const url = `${API_BASE}/download/${props.novel.source}/${props.novel.id}?${params.toString()}`;
    const link = document.createElement('a');
    link.href = url;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } finally {
    // 延迟重置，给浏览器时间发起请求
    setTimeout(() => { downloading.value = false; }, 3000);
  }
}
</script>

<template>
  <article class="h-full">
    <el-card shadow="hover" class="h-full"
      :body-style="{ padding: '0', height: '100%' }">
      <div class="flex h-full flex-col">
        <router-link :to="`/novel/${novel.source}/${novel.id}`"
          class="no-underline text-inherit flex flex-1 flex-col" @click="rememberListScroll">
          <div class="relative shrink-0">
            <!-- 封面 -->
            <el-image v-if="coverImageUrl" :src="coverImageUrl" :alt="novel.title" fit="cover"
              class="h-40 w-full bg-sakiko-pale">
              <template #placeholder>
                <el-skeleton-item variant="image" class="h-full w-full" />
              </template>
              <template #error>
                <el-row class="h-full w-full bg-sakiko-light" justify="center" align="middle">
                  <img v-if="sourceLogo" :src="sourceLogo" alt="source"
                    class="h-16 w-16 object-contain opacity-60" />
                  <el-icon v-else :size="64"><Document /></el-icon>
                </el-row>
              </template>
            </el-image>
            <el-row v-else class="h-40 bg-sakiko-light" justify="center" align="middle">
              <img v-if="sourceLogo" :src="sourceLogo" alt="source"
                class="w-16 h-16 object-contain opacity-60" />
              <el-icon v-else :size="64" color="var(--el-text-color-placeholder)"><Document /></el-icon>
            </el-row>

            <!-- 最近阅读 -->
            <el-tag v-if="isLastRead" type="success" effect="dark" size="small"
              class="absolute top-2 right-2 z-10">
              刚才看过
            </el-tag>
          </div>

          <!-- 内容 -->
          <div class="p-4 pb-2 flex flex-col flex-1">
            <el-space class="w-full flex-1" direction="vertical" alignment="flex-start" fill :size="8">
              <el-space wrap :size="8">
                <el-tag size="small" type="primary" effect="dark">
                  <el-space :size="4">
                  <img v-if="sourceLogo" :src="sourceLogo" alt="" class="w-3 h-3 object-contain" />
                  {{ novel.source.toUpperCase() }}
                  </el-space>
                </el-tag>
                <el-tag v-if="novel.rating" size="small" type="warning" effect="dark">
                  {{ novel.rating }}
                </el-tag>
              </el-space>

              <el-text tag="h3" size="large" :line-clamp="2"><strong>{{ novel.title }}</strong></el-text>
              <el-text type="info" size="small">{{ novel.author }}</el-text>

              <el-text class="flex-1" tag="div" type="info" size="small" :line-clamp="3">
                {{ truncatedSummary }}
              </el-text>

              <el-space wrap :size="6">
                <el-tag v-for="tag in novel.tags.slice(0, 5)" :key="tag" size="small" round
                  :type="isHighlightTag(tag) ? 'primary' : 'info'"
                  :effect="isHighlightTag(tag) ? 'dark' : 'plain'">
                  {{ tag }}
                </el-tag>
                <el-tag v-if="novel.tags.length > 5" size="small" type="info" round>
                  +{{ novel.tags.length - 5 }}
                </el-tag>
              </el-space>

              <el-row class="w-full mt-auto" justify="space-between" align="middle">
                <el-space wrap :size="12">
                  <el-space v-if="novel.word_count" :size="4">
                    <el-icon><Document /></el-icon>
                    <el-text type="info" size="small">{{ novel.word_count.toLocaleString() }} 字</el-text>
                  </el-space>
                  <el-space v-if="novel.chapter_count" :size="4">
                    <el-icon><Reading /></el-icon>
                    <el-text type="info" size="small">{{ novel.chapter_count }} 章</el-text>
                  </el-space>
                  <el-space v-if="novel.kudos" :size="4">
                    <el-icon><Star /></el-icon>
                    <el-text type="info" size="small">{{ novel.kudos }}</el-text>
                  </el-space>
                </el-space>
                <el-space :size="4">
                  <el-icon><Calendar /></el-icon>
                  <el-text type="info" size="small">{{ formattedPublishedDate }}</el-text>
                </el-space>
              </el-row>
            </el-space>
          </div>
        </router-link>

        <div class="px-4 pb-4 shrink-0">
          <el-row class="mt-2" justify="space-between" align="middle">
            <el-space :size="8">
              <el-tag v-if="novel.is_complete !== undefined" size="small" round
                :type="novel.is_complete ? 'success' : 'warning'">
                {{ novel.is_complete ? '已完结' : '连载中' }}
              </el-tag>
              <el-button v-if="showFavoriteAction" size="small" round :loading="favoriteLoading"
                :icon="isFavorite ? StarFilled : Star"
                :title="userStore.isLoggedIn ? (isFavorite ? '取消收藏' : '收藏') : '登录后可收藏'"
                @click="toggleFavorite">
                {{ isFavorite ? '已收藏' : '收藏' }}
              </el-button>
              <slot name="actions" />
            </el-space>
            <el-button text circle :icon="Download" :loading="downloading" title="下载 PDF"
              aria-label="下载 PDF" @click="handleDownload" />
          </el-row>
          <el-row v-if="footerNote" class="mt-2" justify="end">
            <el-text type="info" size="small">{{ footerNote }}</el-text>
          </el-row>
        </div>
      </div>
    </el-card>
  </article>
</template>
