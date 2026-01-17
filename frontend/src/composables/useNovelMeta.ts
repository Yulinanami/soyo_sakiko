import { computed, type Ref } from 'vue';
import type { Novel } from '../types/novel';

export function useNovelMeta(novel: Ref<Novel>) {
  const formattedDate = computed(() => {
    const rawDate = novel.value.published_at || novel.value.updated_at || '';
    const date = new Date(rawDate);
    if (Number.isNaN(date.getTime())) {
      return '未知日期';
    }
    return date.toLocaleDateString('zh-CN');
  });

  const truncatedSummary = computed(() => {
    if (!novel.value.summary) return '';
    return novel.value.summary.length > 150
      ? novel.value.summary.slice(0, 150) + '...'
      : novel.value.summary;
  });

  function isHighlightTag(tag: string): boolean {
    return tag.includes('素') || tag.includes('祥') || tag.includes('Soyo') || tag.includes('Sakiko');
  }

  return {
    formattedDate,
    truncatedSummary,
    isHighlightTag,
  };
}
