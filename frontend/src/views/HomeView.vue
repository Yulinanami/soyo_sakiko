<script setup lang="ts">
import { onMounted, onBeforeUnmount, nextTick, ref, computed } from 'vue';
import { useNovelsStore } from '@stores/novels';
import { useSourcesStore } from '@stores/sources';
import NovelList from '@components/novel/NovelList.vue';
import SourceSelector from '@components/filter/SourceSelector.vue';
import TagFilter from '@components/filter/TagFilter.vue';
import ExcludeFilter from '@components/filter/ExcludeFilter.vue';
import { Menu, ChevronUp } from 'lucide-vue-next';

const novelsStore = useNovelsStore();
const sourcesStore = useSourcesStore();
const isExcludeOpen = ref(false);
const isConfigCollapsed = ref(false);
const isPageNavOpen = ref(false);

// 计算当前加载了多少页
const loadedPages = computed(() => {
  const breaks = novelsStore.pageBreaks;
  // 页数 = 分页断点数 + 1
  return breaks.length + 1;
});

// 滚动到指定页
function scrollToPage(pageNum: number) {
  if (pageNum === 1) {
    // 回到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else if (pageNum === -1) {
    // 直达底部
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
  } else {
    // 优先尝试定位到分页分隔线
    const dividerEl = document.querySelector(`[data-page-num="${pageNum}"]`);
    if (dividerEl) {
      dividerEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
  isPageNavOpen.value = false;
}

function togglePageNav() {
  isPageNavOpen.value = !isPageNavOpen.value;
}

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
  const enabled = sourcesStore.getEnabledSourceNames();
  novelsStore.selectedSources = enabled;

  // 如果当前配置源被关闭了，切换到第一个开启的源
  if (enabled.length > 0 && !enabled.includes(novelsStore.activeConfigSource)) {
    const firstEnabled = enabled[0];
    if (firstEnabled) {
      novelsStore.activeConfigSource = firstEnabled;
    }
  }

  novelsStore.fetchSourcesWithCache();
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
      <div :class="['px-6', isConfigCollapsed ? 'py-[11px]' : 'py-4']">
        <div class="space-y-4">
          <transition-group enter-active-class="transition duration-200 ease-out"
            enter-from-class="transform -translate-y-2 opacity-0" enter-to-class="transform translate-y-0 opacity-100"
            leave-active-class="transition duration-150 ease-in" leave-from-class="transform translate-y-0 opacity-100"
            leave-to-class="transform -translate-y-2 opacity-0">
            <!-- 标签配置源切换 -->
            <div v-if="!isConfigCollapsed" key="source-config"
              class="flex items-center gap-2 overflow-x-auto no-scrollbar py-1">
              <span class="text-xs font-medium text-gray-500 dark:text-gray-400 mr-2 shrink-0">配置源:</span>
              <button v-for="source in sourcesStore.getEnabledSourceNames()" :key="source"
                @click="novelsStore.activeConfigSource = source" :class="[
                  'px-3 py-1 rounded-full text-xs transition-all whitespace-nowrap border',
                  novelsStore.activeConfigSource === source
                    ? 'bg-sakiko/10 border-sakiko text-sakiko font-medium'
                    : 'bg-gray-100 border-transparent text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                ]">
                {{ sourcesStore.getSourceDisplayName(source) }}
              </button>
            </div>

            <!-- 标签过滤 -->
            <TagFilter v-if="!isConfigCollapsed" key="tag-filter"
              :selected-tags="novelsStore.tagsBySource[novelsStore.activeConfigSource]" :exclude-open="isExcludeOpen"
              @toggle-exclude="toggleExclude" @update:selected-tags="(tags) => {
                novelsStore.tagsBySource[novelsStore.activeConfigSource] = tags;
                novelsStore.saveTagConfig(novelsStore.activeConfigSource);
                novelsStore.fetchNovels(true, [novelsStore.activeConfigSource]);
              }" />

            <!-- 排除过滤 -->
            <ExcludeFilter v-if="!isConfigCollapsed" key="exclude-filter"
              :exclude-tags="novelsStore.excludeTagsBySource[novelsStore.activeConfigSource]" :open="isExcludeOpen"
              @update:exclude-tags="(tags) => {
                novelsStore.excludeTagsBySource[novelsStore.activeConfigSource] = tags;
                novelsStore.saveTagConfig(novelsStore.activeConfigSource);
                novelsStore.fetchNovels(true, [novelsStore.activeConfigSource]);
              }" />
          </transition-group>

          <!-- 数据源选择和排序 - 始终显示 -->
          <div
            :class="['flex flex-wrap items-center justify-between gap-4', isConfigCollapsed ? '' : 'pt-2 border-t border-gray-100 dark:border-gray-700']">
            <div class="flex items-center gap-2">
              <button @click="isConfigCollapsed = !isConfigCollapsed"
                class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 transition-colors"
                :title="isConfigCollapsed ? '展开配置' : '折叠配置'">
                <Menu class="w-5 h-5" />
              </button>
              <SourceSelector :loading-sources="novelsStore.loadingSources" @change="handleSourceChange"
                @refresh="handleRefresh" />
            </div>

            <select v-model="novelsStore.sortBy" @change="novelsStore.fetchNovels(true)"
              class="px-4 py-2 rounded-lg border border-gray-300 bg-white text-sm focus:outline-none focus:border-sakiko dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200">
              <option value="date">最新更新</option>
              <option value="kudos">最多点赞</option>
              <option value="hits">最多阅读</option>
              <option value="wordCount">字数最多</option>
            </select>
          </div>
        </div>
      </div>
    </header>

    <main class="p-6">
      <NovelList :novels="novelsStore.novels" :loading="novelsStore.loading" :has-more="novelsStore.hasMore"
        :page-breaks="novelsStore.pageBreaks" @load-more="novelsStore.loadMore" />

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

    <!-- 浮动页面导航按钮 -->
    <div class="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
      <!-- 展开的页面选项 -->
      <transition enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 translate-y-4 scale-95" enter-to-class="opacity-100 translate-y-0 scale-100"
        leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100 translate-y-0 scale-100"
        leave-to-class="opacity-0 translate-y-4 scale-95">
        <div v-if="isPageNavOpen && loadedPages > 0"
          class="bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 py-2 px-3 min-w-[100px]">
          <button @click="scrollToPage(1)"
            class="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-sakiko/10 hover:text-sakiko rounded-lg transition-colors">
            回到顶部
          </button>
          <template v-for="page in loadedPages" :key="page">
            <button v-if="page > 1" @click="scrollToPage(page)"
              class="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-sakiko/10 hover:text-sakiko rounded-lg transition-colors">
              第 {{ page }} 页
            </button>
          </template>
          <button @click="scrollToPage(-1)"
            class="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-sakiko/10 hover:text-sakiko rounded-lg transition-colors border-t border-gray-100 dark:border-gray-700 mt-1 pt-2">
            直达底部
          </button>
        </div>
      </transition>

      <!-- 主按钮 -->
      <button @click="togglePageNav"
        class="w-12 h-12 rounded-full bg-sakiko text-white shadow-lg hover:bg-sakiko/90 hover:shadow-xl transition-all duration-200 flex items-center justify-center"
        :class="{ 'rotate-180': isPageNavOpen }" :title="isPageNavOpen ? '收起导航' : '页面导航'">
        <ChevronUp class="w-6 h-6 transition-transform duration-200" />
      </button>
    </div>
  </div>
</template>
