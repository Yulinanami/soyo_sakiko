import { computed, type Ref } from 'vue';
import type { Novel } from '@types/novel';

export function useNovelMeta(novel: Ref<Novel>) {
  // 生成展示用信息
  const formattedDate = computed(() => {
    // 生成日期文本
    const rawDate = novel.value.published_at || novel.value.updated_at || '';
    const date = new Date(rawDate);
    if (Number.isNaN(date.getTime())) {
      return '未知日期';
    }
    return date.toLocaleDateString('zh-CN');
  });

  const truncatedSummary = computed(() => {
    // 生成摘要文本
    if (!novel.value.summary) return '';
    return novel.value.summary.length > 150
      ? novel.value.summary.slice(0, 150) + '...'
      : novel.value.summary;
  });

  function isHighlightTag(tag: string): boolean {
    // 判断标签是否需要强调
    return tag.includes('素') || tag.includes('祥') || tag.includes('Soyo') || tag.includes('Sakiko');
  }

  return {
    formattedDate,
    truncatedSummary,
    isHighlightTag,
  };
}
