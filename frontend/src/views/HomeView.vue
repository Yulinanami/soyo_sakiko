<script setup lang="ts">
import { onMounted, onBeforeUnmount, nextTick, ref, computed } from 'vue';
import { useNovelsStore } from '@stores/novels';
import { useSourcesStore } from '@stores/sources';
import NovelList from '@components/novel/NovelList.vue';
import SourceSelector from '@components/filter/SourceSelector.vue';
import TagFilter from '@components/filter/TagFilter.vue';
import ExcludeFilter from '@components/filter/ExcludeFilter.vue';
import {
  ElAlert,
  ElButton,
  ElCard,
  ElCheckTag,
  ElCollapseTransition,
  ElContainer,
  ElDivider,
  ElEmpty,
  ElMain,
  ElOption,
  ElPopover,
  ElRow,
  ElSelect,
  ElSpace,
  ElText,
} from 'element-plus';
import { ArrowUpBold, Bottom, Expand, Fold, Top } from '@element-plus/icons-vue';

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
  <el-container direction="vertical">
    <!-- 顶部标签栏 -->
    <div class="sticky top-0 z-30">
      <el-card shadow="never" :body-style="{ padding: '16px 24px' }">
        <ElCollapseTransition>
          <div v-show="!isConfigCollapsed">
            <el-space direction="vertical" alignment="stretch" fill :size="16">
              <!-- 标签配置源切换 -->
              <el-space wrap :size="8">
                <el-text type="info" size="small">配置源:</el-text>
                <el-check-tag v-for="source in sourcesStore.getEnabledSourceNames()" :key="source" type="primary"
                  :checked="novelsStore.activeConfigSource === source"
                  @change="novelsStore.activeConfigSource = source">
                  {{ sourcesStore.getSourceDisplayName(source) }}
                </el-check-tag>
              </el-space>

              <div>
                <!-- 标签过滤 -->
                <TagFilter :selected-tags="novelsStore.tagsBySource[novelsStore.activeConfigSource]"
                  :exclude-open="isExcludeOpen" @toggle-exclude="toggleExclude" @update:selected-tags="(tags) => {
                    novelsStore.tagsBySource[novelsStore.activeConfigSource] = tags;
                    novelsStore.saveTagConfig(novelsStore.activeConfigSource);
                    novelsStore.fetchNovels(true, [novelsStore.activeConfigSource]);
                  }" />

                <!-- 排除过滤 -->
                <ExcludeFilter :exclude-tags="novelsStore.excludeTagsBySource[novelsStore.activeConfigSource]"
                  :open="isExcludeOpen" @update:exclude-tags="(tags) => {
                    novelsStore.excludeTagsBySource[novelsStore.activeConfigSource] = tags;
                    novelsStore.saveTagConfig(novelsStore.activeConfigSource);
                    novelsStore.fetchNovels(true, [novelsStore.activeConfigSource]);
                  }" />
              </div>

              <el-divider style="margin: 0 0 12px" />
            </el-space>
          </div>
        </ElCollapseTransition>

        <!-- 数据源选择和排序 - 始终显示 -->
        <el-row justify="space-between" align="middle" style="row-gap: 12px">
          <el-space wrap :size="8">
            <el-button text circle :icon="isConfigCollapsed ? Expand : Fold"
              @click="isConfigCollapsed = !isConfigCollapsed"
              :title="isConfigCollapsed ? '展开配置' : '折叠配置'" />
            <SourceSelector :loading-sources="novelsStore.loadingSources" @change="handleSourceChange"
              @refresh="handleRefresh" />
          </el-space>

          <el-select v-model="novelsStore.sortBy" style="width: 8rem" @change="novelsStore.fetchNovels(true)">
            <el-option label="最新更新" value="date" />
            <el-option label="最多点赞" value="kudos" />
            <el-option label="最多阅读" value="hits" />
            <el-option label="字数最多" value="wordCount" />
          </el-select>
        </el-row>
      </el-card>
    </div>

    <el-main>
      <NovelList :novels="novelsStore.novels" :loading="novelsStore.loading" :has-more="novelsStore.hasMore"
        :page-breaks="novelsStore.pageBreaks" @load-more="novelsStore.loadMore" />

      <div v-if="novelsStore.error" style="margin-top: 16px">
        <el-alert :title="novelsStore.error" type="error" show-icon :closable="false">
          <template #default>
            <el-button style="margin-top: 12px" type="danger" plain @click="novelsStore.retry">重试</el-button>
          </template>
        </el-alert>
      </div>

      <el-empty v-if="novelsStore.isEmpty" description="暂无符合条件的小说">
        <el-text type="info" size="small">尝试调整筛选条件或切换数据源</el-text>
      </el-empty>
    </el-main>

    <!-- 浮动页面导航按钮 -->
    <div class="fixed bottom-6 right-6 z-50">
      <el-popover v-model:visible="isPageNavOpen" placement="top-end" trigger="click" :width="150"
        :disabled="loadedPages <= 0">
        <el-space direction="vertical" fill :size="0">
          <el-button text :icon="Top" style="width: 100%; justify-content: flex-start" @click="scrollToPage(1)">
            回到顶部
          </el-button>
          <template v-for="page in loadedPages" :key="page">
            <el-button v-if="page > 1" text style="width: 100%; justify-content: flex-start"
              @click="scrollToPage(page)">
              第 {{ page }} 页
            </el-button>
          </template>
          <el-button text :icon="Bottom" style="width: 100%; justify-content: flex-start" @click="scrollToPage(-1)">
            直达底部
          </el-button>
        </el-space>
        <template #reference>
          <el-button type="primary" circle size="large" :icon="isPageNavOpen ? Bottom : ArrowUpBold"
            :title="isPageNavOpen ? '收起导航' : '页面导航'" />
        </template>
      </el-popover>
    </div>
  </el-container>
</template>
