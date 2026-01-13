<script setup lang="ts">
import { onMounted } from 'vue';
import { useNovelsStore } from '../stores/novels';
import { useSourcesStore } from '../stores/sources';
import NovelList from '../components/novel/NovelList.vue';
import SourceSelector from '../components/filter/SourceSelector.vue';
import TagFilter from '../components/filter/TagFilter.vue';

const novelsStore = useNovelsStore();
const sourcesStore = useSourcesStore();

onMounted(() => {
  novelsStore.fetchNovels(true);
});

function handleSourceChange() {
  novelsStore.selectedSources = sourcesStore.getEnabledSourceNames();
  novelsStore.fetchNovels(true);
}

function handleTagChange(tags: string[]) {
  novelsStore.selectedTags = tags;
  novelsStore.fetchNovels(true);
}
</script>

<template>
  <div class="min-h-screen">
    <!-- Hero Banner -->
    <header class="bg-gradient-to-r from-primary to-secondary py-16 px-8 text-center text-white">
      <h1 class="text-4xl md:text-5xl font-bold mb-3">🎸 SoyoSaki 同人文聚合</h1>
      <p class="text-lg opacity-90">
        长崎素世 × 丰川祥子 · 收录来自 AO3 / Pixiv / Lofter 的同人作品
      </p>
    </header>

    <!-- Filter Bar -->
    <section class="bg-gray-100 border-b border-gray-200 py-6">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex flex-wrap gap-4 items-center">
          <SourceSelector @change="handleSourceChange" />
          <TagFilter 
            :selected-tags="novelsStore.selectedTags" 
            @update:selected-tags="handleTagChange" 
          />
          <div class="ml-auto">
            <select 
              v-model="novelsStore.sortBy" 
              @change="novelsStore.fetchNovels(true)"
              class="px-4 py-2 rounded-lg border border-gray-300 bg-white text-sm focus:outline-none focus:border-primary"
            >
              <option value="date">最新更新</option>
              <option value="kudos">最多点赞</option>
              <option value="hits">最多阅读</option>
              <option value="wordCount">字数最多</option>
            </select>
          </div>
        </div>
      </div>
    </section>

    <!-- Novel List -->
    <main class="py-8">
      <div class="max-w-7xl mx-auto px-4">
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
      </div>
    </main>
  </div>
</template>
