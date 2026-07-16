<script setup lang="ts">
import { onMounted } from "vue";
import { storeToRefs } from "pinia";
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
import { Delete, Reading, Search } from "@element-plus/icons-vue";
import NovelCard from "@components/novel/NovelCard.vue";
import type { Novel } from "@app-types/novel";
import type { HistoryItem } from "@app-types/user_data";
import { useHistoryStore } from "@stores/history";

const historyStore = useHistoryStore();
const { items, loading, error } = storeToRefs(historyStore);

onMounted(async () => {
  // 进入页面时获取记录
  await historyStore.fetchHistory();
});

async function removeHistory(id: number) {
  // 删除记录
  await historyStore.removeHistory(id);
}

function toNovel(item: HistoryItem): Novel {
  // 转成小说结构
  return {
    id: item.novel_id,
    source: item.source as Novel["source"],
    title: item.title || "未命名作品",
    author: item.author || "Unknown",
    summary: "",
    tags: [],
    rating: undefined,
    word_count: undefined,
    chapter_count: undefined,
    kudos: undefined,
    hits: undefined,
    published_at: item.published_at || "",
    source_url: item.source_url || "",
    cover_image: item.cover_url,
    is_complete: undefined,
  };
}

function formatLastRead(date: string) {
  // 格式化时间
  if (!date) return "未知";
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return "未知";
  return parsed.toLocaleString("zh-CN");
}
</script>

<template>
  <div class="history-page">
    <header class="page-hero">
      <ElRow class="page-heading" align="middle" justify="space-between">
        <ElSpace :size="16">
          <ElAvatar class="page-avatar" :size="54" :icon="Reading" />
          <ElSpace direction="vertical" alignment="flex-start" :size="4">
            <ElText tag="h1" class="page-title">阅读记录</ElText>
            <ElText tag="p" class="page-subtitle">
              从上次停下的地方继续阅读
            </ElText>
          </ElSpace>
        </ElSpace>
        <ElTag class="count-tag" effect="light" round>
          {{ items.length }} 条
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
        v-else-if="items.length === 0"
        shadow="never"
      >
        <ElEmpty description="还没有阅读记录">
          <RouterLink v-slot="{ navigate }" to="/" custom>
            <ElButton type="primary" :icon="Search" @click="navigate">
              去发现好文
            </ElButton>
          </RouterLink>
        </ElEmpty>
      </ElCard>

      <ElRow v-else class="novel-row" :gutter="22">
        <ElCol
          v-for="item in items"
          :key="item.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
        >
          <NovelCard
            :novel="toNovel(item)"
            :footer-note="'最近阅读: ' + formatLastRead(item.last_read_at)"
            :show-favorite-action="false"
          >
            <template #actions>
              <ElButton
                type="danger"
                text
                size="small"
                :icon="Delete"
                aria-label="移除记录"
                @click="removeHistory(item.id)"
              >
                移除记录
              </ElButton>
            </template>
          </NovelCard>
        </ElCol>
      </ElRow>
    </main>
  </div>
</template>

<style scoped>
.history-page {
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
