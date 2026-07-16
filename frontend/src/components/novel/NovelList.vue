<script setup lang="ts">
import NovelCard from '@components/novel/NovelCard.vue';
import type { Novel } from '@app-types/novel';
import { ElButton, ElCol, ElDivider, ElIcon, ElRow, ElSpace, ElText } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';

const props = defineProps<{
  novels: Novel[];
  loading: boolean;
  hasMore: boolean;
  pageBreaks: number[];  // 分页位置数组
}>();

const emit = defineEmits<{
  (e: 'load-more'): void;
}>();

// 计算哪个位置是哪一页的起点
function getPageNumber(index: number): number | null {
  const breakIndex = props.pageBreaks.indexOf(index);
  if (breakIndex !== -1) {
    return breakIndex + 2;  // 第一次加载更多是第2页
  }
  return null;
}
</script>

<template>
  <div>
    <el-row :gutter="24" style="row-gap: 24px">
      <template v-for="(novel, index) in novels" :key="`${novel.source}-${novel.id}`">
        <!-- 分页分隔线 -->
        <el-col v-if="getPageNumber(index)" :span="24" :data-page-num="getPageNumber(index)">
          <el-divider content-position="center">
            <el-text type="primary" size="small">第 {{ getPageNumber(index) }} 页</el-text>
          </el-divider>
        </el-col>

        <el-col :xs="24" :sm="12" :md="8" :lg="6" :data-novel-index="index">
          <NovelCard :novel="novel" />
        </el-col>
      </template>
    </el-row>

    <el-row v-if="loading" justify="center" align="middle" style="padding: 48px 0">
      <el-space :size="12">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <el-text type="info">加载中...</el-text>
      </el-space>
    </el-row>

    <el-row v-if="!loading && hasMore" justify="center" style="padding: 32px 0">
      <el-space direction="vertical" alignment="center" :size="12">
        <el-text type="info" size="small">已加载 {{ novels.length }} 篇同人文</el-text>
        <el-button type="primary" size="large" @click="emit('load-more')">加载更多</el-button>
      </el-space>
    </el-row>

    <el-divider v-if="!loading && !hasMore && novels.length > 0" content-position="center">
      <el-text type="info" size="small">已加载全部 {{ novels.length }} 篇同人文</el-text>
    </el-divider>
  </div>
</template>
