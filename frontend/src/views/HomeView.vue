<script setup lang="ts">
import { onMounted, onBeforeUnmount, nextTick, ref } from 'vue';
import { useNovelsStore } from '@stores/novels';
import { useSourcesStore } from '@stores/sources';
import NovelList from '@components/novel/NovelList.vue';
import SourceSelector from '@components/filter/SourceSelector.vue';
import TagFilter from '@components/filter/TagFilter.vue';
import ExcludeFilter from '@components/filter/ExcludeFilter.vue';

const novelsStore = useNovelsStore();
const sourcesStore = useSourcesStore();
const isExcludeOpen = ref(false);

function saveScrollPosition() {
  // 保存滚动位置
  sessionStorage.setItem('soyosaki:listScrollY', String(window.scrollY));
}

function restoreListScroll() {
  // 恢复滚动位置
  const raw = sessionStorage.getItem('soyosaki:listScrollY');
  if (!raw) return;
  const y = Number(raw);
  if (Number.isFinite(y) && y > 0) {
    setTimeout(() => {
      window.scrollTo({ top: y, left: 0, behavior: 'auto' });
    }, 50);
  }
}

onBeforeUnmount(() => {
  // 离开页面时保存位置
  saveScrollPosition();
});

onMounted(async () => {
  // 根据返回来源决定是否保留列表
  const preserve = sessionStorage.getItem('soyosaki:preserveList') === '1';

  if (novelsStore.novels.length > 0) {
    if (preserve) {
      sessionStorage.removeItem('soyosaki:preserveList');
    }
    await nextTick();
    restoreListScroll();
    return;
  }

  sessionStorage.removeItem('soyosaki:preserveList');
  await novelsStore.fetchNovels(true);
  await nextTick();
  restoreListScroll();
});

function handleSourceChange() {
  // 切换来源后刷新
  novelsStore.selectedSources = sourcesStore.getEnabledSourceNames();
  novelsStore.fetchSourcesWithCache();
}

function handleTagChange(tags: string[]) {
  // 切换标签后刷新
  novelsStore.selectedTags = tags;
  novelsStore.fetchNovels(true);
}

function handleExcludeChange(tags: string[]) {
  // 切换排除后刷新
  novelsStore.excludeTags = tags;
  novelsStore.fetchNovels(true);
}

function toggleExclude() {
  // 展开或收起排除项
  isExcludeOpen.value = !isExcludeOpen.value;
}

function handleRefresh() {
  // 重新拉取全部数据
  novelsStore.fetchNovels(true);
}
</script>

<template>
  <div class="min-h-screen">
    <!-- 顶部标签栏 -->
    <header
      class="bg-white border-b border-gray-200 dark:bg-gray-800 dark:border-gray-700 sticky top-0 z-30 shadow-sm transition-colors duration-300">
      <div class="px-6 py-4 space-y-4">
        <!-- 标签过滤 -->
        <TagFilter :selected-tags="novelsStore.selectedTags" :exclude-open="isExcludeOpen"
          @toggle-exclude="toggleExclude" @update:selected-tags="handleTagChange" />

        <!-- 排除过滤 -->
        <ExcludeFilter :exclude-tags="novelsStore.excludeTags" :open="isExcludeOpen"
          @update:exclude-tags="handleExcludeChange" />

        <!-- 数据源选择和排序 -->
        <div class="flex flex-wrap items-center justify-between gap-4">
          <SourceSelector :loading-sources="novelsStore.loadingSources" @change="handleSourceChange"
            @refresh="handleRefresh" />

          <select v-model="novelsStore.sortBy" @change="novelsStore.fetchNovels(true)"
            class="px-4 py-2 rounded-lg border border-gray-300 bg-white text-sm focus:outline-none focus:border-sakiko dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200">
            <option value="date">最新更新</option>
            <option value="kudos">最多点赞</option>
            <option value="hits">最多阅读</option>
            <option value="wordCount">字数最多</option>
          </select>
        </div>
      </div>
    </header>

    <!-- 小说列表 -->
    <main class="p-6">
      <NovelList :novels="novelsStore.novels" :loading="novelsStore.loading" :has-more="novelsStore.hasMore"
        @load-more="novelsStore.loadMore" />

      <div v-if="novelsStore.error" class="text-center p-8 bg-red-50 dark:bg-red-900/20 rounded-lg mt-4">
        <p class="text-red-500 dark:text-red-400 mb-4">{{ novelsStore.error }}</p>
        <button @click="novelsStore.retry"
          class="px-6 py-2 bg-sakiko text-white rounded-lg hover:bg-sakiko/90 transition-colors">
          重试
        </button>
      </div>

      <div v-if="novelsStore.isEmpty" class="text-center py-16 text-gray-500 dark:text-gray-400">
        <p class="text-lg">暂无符合条件的小说</p>
        <p class="text-sm opacity-70 mt-2">尝试调整筛选条件或切换数据源</p>
      </div>
    </main>
  </div>
</template>
