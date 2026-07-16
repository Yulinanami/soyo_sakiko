<script setup lang="ts">
import { computed, onMounted } from "vue";
import {
  ElAlert,
  ElAvatar,
  ElButton,
  ElCard,
  ElCol,
  ElEmpty,
  ElRow,
  ElSkeleton,
  ElSpace,
  ElTag,
  ElText,
} from "element-plus";
import { CollectionTag, Search } from "@element-plus/icons-vue";
import { useFavoritesStore } from "@stores/favorites";
import NovelCard from "@components/novel/NovelCard.vue";
import type { Novel } from "@app-types/novel";
import type { FavoriteItem } from "@app-types/user_data";

const favoritesStore = useFavoritesStore();
const favorites = computed(() => favoritesStore.items);
const loading = computed(() => favoritesStore.loading);
const error = computed(() => favoritesStore.error);

onMounted(async () => {
  // 进入页面时获取收藏
  await favoritesStore.fetchFavorites(true);
});

function toNovel(fav: FavoriteItem): Novel {
  // 转成小说结构
  return {
    id: fav.novel_id,
    source: fav.source as Novel["source"],
    title: fav.title,
    author: fav.author || "Unknown",
    summary: "",
    tags: [],
    published_at: fav.published_at || "",
    source_url: fav.source_url || "",
    cover_image: fav.cover_url,
  };
}
</script>

<template>
  <div class="collection-page">
    <header class="page-hero">
      <ElRow class="page-heading" align="middle" justify="space-between">
        <ElSpace :size="16">
          <ElAvatar class="page-avatar" :size="54" :icon="CollectionTag" />
          <ElSpace direction="vertical" alignment="flex-start" :size="4">
            <ElText tag="h1" class="page-title">我的收藏</ElText>
            <ElText tag="p" class="page-subtitle">
              把喜欢的作品安静地收在这里
            </ElText>
          </ElSpace>
        </ElSpace>
        <ElTag class="count-tag" effect="light" round>
          {{ favorites.length }} 篇
        </ElTag>
      </ElRow>
    </header>

    <main class="page-content">
      <ElCard v-if="loading" shadow="never">
        <ElSkeleton :rows="6" animated />
      </ElCard>

      <ElAlert
        v-else-if="error"
        :title="error || ''"
        type="error"
        show-icon
        :closable="false"
      />

      <ElCard
        v-else-if="favorites.length === 0"
        shadow="never"
      >
        <ElEmpty description="还没有收藏任何小说">
          <RouterLink v-slot="{ navigate }" to="/" custom>
            <ElButton type="primary" :icon="Search" @click="navigate">
              去发现好文
            </ElButton>
          </RouterLink>
        </ElEmpty>
      </ElCard>

      <ElRow v-else class="novel-row" :gutter="22">
        <ElCol
          v-for="fav in favorites"
          :key="fav.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
        >
          <NovelCard :novel="toNovel(fav)" />
        </ElCol>
      </ElRow>
    </main>
  </div>
</template>

<style scoped>
.collection-page {
  min-height: 100vh;
  background: var(--el-fill-color-extra-light);
}

.page-hero {
  padding: 34px 28px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-color-primary);
}

.page-heading {
  max-width: 1280px;
  margin: 0 auto;
  row-gap: 8px;
}

.count-tag {
  margin-left: auto;
}

.page-avatar {
  color: var(--el-color-primary-dark-2);
  background: var(--el-color-primary-light-9);
}

.page-title,
.page-subtitle {
  margin: 0;
  color: var(--el-text-color-primary);
}

.page-title {
  font-size: 28px;
  font-weight: 700;
}

.page-subtitle {
  font-size: 14px;
}

.page-content {
  max-width: 1280px;
  margin: 0 auto;
  padding: 28px;
}

.novel-row {
  row-gap: 22px;
}
</style>
