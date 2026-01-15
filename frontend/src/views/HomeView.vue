<script setup lang="ts">
import { onMounted, nextTick, ref } from 'vue';
import { useNovelsStore } from '../stores/novels';
import { useSourcesStore } from '../stores/sources';
import NovelList from '../components/novel/NovelList.vue';
import SourceSelector from '../components/filter/SourceSelector.vue';
import TagFilter from '../components/filter/TagFilter.vue';
import ExcludeFilter from '../components/filter/ExcludeFilter.vue';

const novelsStore = useNovelsStore();
const sourcesStore = useSourcesStore();
const isExcludeOpen = ref(false);

function restoreListScroll() {
  const raw = sessionStorage.getItem('soyosaki:listScrollY');
  if (!raw) return;
  sessionStorage.removeItem('soyosaki:listScrollY');
  const y = Number(raw);
  if (Number.isFinite(y)) {
    window.scrollTo({ top: y, left: 0, behavior: 'auto' });
  }
}

onMounted(async () => {
  const preserve = sessionStorage.getItem('soyosaki:preserveList') === '1';
  if (preserve && novelsStore.novels.length > 0) {
    sessionStorage.removeItem('soyosaki:preserveList');
    await nextTick();
    restoreListScroll();
    return;
  }
  await novelsStore.fetchNovels(true);
  await nextTick();
  restoreListScroll();
});

function handleSourceChange() {
  novelsStore.selectedSources = sourcesStore.getEnabledSourceNames();
  novelsStore.fetchNovels(true);
}

function handleTagChange(tags: string[]) {
  novelsStore.selectedTags = tags;
  novelsStore.fetchNovels(true);
}

function handleExcludeChange(tags: string[]) {
  novelsStore.excludeTags = tags;
  novelsStore.fetchNovels(true);
}

function toggleExclude() {
  isExcludeOpen.value = !isExcludeOpen.value;
}
</script>

<template>
  <div class="min-h-screen">
    <!-- 顶部标签栏 -->
    <header class="bg-white border-b border-gray-200">
      <div class="px-6 py-4 space-y-4">
        <!-- 标签过滤 -->
        <TagFilter 
          :selected-tags="novelsStore.selectedTags"
          :exclude-open="isExcludeOpen"
          @toggle-exclude="toggleExclude"
          @update:selected-tags="handleTagChange" 
        />
        
        <!-- 排除过滤 -->
        <ExcludeFilter
          :exclude-tags="novelsStore.excludeTags"
          :open="isExcludeOpen"
          @update:exclude-tags="handleExcludeChange"
        />
        
        <!-- 数据源选择和排序 -->
        <div class="flex flex-wrap items-center justify-between gap-4">
          <SourceSelector
            :loading-sources="novelsStore.loadingSources"
            @change="handleSourceChange"
          />
          
          <select 
            v-model="novelsStore.sortBy" 
            @change="novelsStore.fetchNovels(true)"
            class="px-4 py-2 rounded-lg border border-gray-300 bg-white text-sm focus:outline-none focus:border-sakiko"
          >
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
      <NovelList 
        :novels="novelsStore.novels"
        :loading="novelsStore.loading"
        :has-more="novelsStore.hasMore"
        @load-more="novelsStore.loadMore"
      />
      
      <div 
        v-if="novelsStore.error" 
        class="text-center text-red-500 p-8 bg-red-50 rounded-lg mt-4"
      >
        {{ novelsStore.error }}
      </div>
      
      <div v-if="novelsStore.isEmpty" class="text-center py-16 text-gray-500">
        <p class="text-lg">暂无符合条件的小说</p>
        <p class="text-sm opacity-70 mt-2">尝试调整筛选条件或切换数据源</p>
      </div>
    </main>
  </div>
</template>
