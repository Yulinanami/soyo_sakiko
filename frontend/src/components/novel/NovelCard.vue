<script setup lang="ts">
import { computed } from 'vue';
import type { Novel } from '../../types/novel';

const props = defineProps<{
  novel: Novel;
}>();

const sourceIcon = computed(() => {
  const icons: Record<string, string> = {
    ao3: '📚',
    pixiv: '🎨',
    lofter: '📝',
  };
  return icons[props.novel.source] || '📄';
});

const sourceClass = computed(() => {
  const classes: Record<string, string> = {
    ao3: 'bg-red-700 text-white',
    pixiv: 'bg-sakiko text-white',
    lofter: 'bg-soyo text-white',
  };
  return classes[props.novel.source] || 'bg-gray-500 text-white';
});

const formattedDate = computed(() => {
  const date = new Date(props.novel.publishedAt);
  return date.toLocaleDateString('zh-CN');
});

const truncatedSummary = computed(() => {
  if (!props.novel.summary) return '';
  return props.novel.summary.length > 150 
    ? props.novel.summary.slice(0, 150) + '...' 
    : props.novel.summary;
});

function isHighlightTag(tag: string): boolean {
  return tag.includes('素') || tag.includes('祥') || tag.includes('Soyo') || tag.includes('Sakiko');
}
</script>

<template>
  <article class="card overflow-hidden hover:-translate-y-1 transition-transform duration-200">
    <router-link :to="`/novel/${novel.source}/${novel.id}`" class="block no-underline text-inherit">
      <!-- Cover Image -->
      <div 
        v-if="novel.coverImage" 
        class="h-40 overflow-hidden bg-sakiko-pale"
      >
        <img :src="novel.coverImage" :alt="novel.title" class="w-full h-full object-cover" />
      </div>
      <div 
        v-else 
        class="h-40 bg-sakiko-light flex items-center justify-center"
      >
        <span class="text-5xl opacity-80">{{ sourceIcon }}</span>
      </div>
      
      <!-- Content -->
      <div class="p-4">
        <div class="flex gap-2 mb-3">
          <span :class="['text-xs px-2 py-0.5 rounded', sourceClass]">
            {{ sourceIcon }} {{ novel.source.toUpperCase() }}
          </span>
          <span v-if="novel.rating" class="text-xs px-2 py-0.5 rounded bg-yellow-400 text-gray-800">
            {{ novel.rating }}
          </span>
        </div>
        
        <h3 class="text-lg font-semibold mb-1 line-clamp-2">{{ novel.title }}</h3>
        <p class="text-sm text-gray-600 mb-3">{{ novel.author }}</p>
        
        <p class="text-sm text-gray-500 leading-relaxed mb-3">{{ truncatedSummary }}</p>
        
        <div class="flex flex-wrap gap-1.5 mb-3">
          <span 
            v-for="tag in novel.tags.slice(0, 5)" 
            :key="tag" 
            :class="[
              'text-xs px-2 py-0.5 rounded-full',
              isHighlightTag(tag) ? 'tag-highlight' : 'tag'
            ]"
          >
            {{ tag }}
          </span>
          <span v-if="novel.tags.length > 5" class="text-xs px-2 py-0.5 rounded-full bg-gray-200">
            +{{ novel.tags.length - 5 }}
          </span>
        </div>
        
        <div class="flex flex-wrap gap-3 text-xs text-gray-500">
          <span v-if="novel.wordCount">📝 {{ novel.wordCount.toLocaleString() }} 字</span>
          <span v-if="novel.chapterCount">📖 {{ novel.chapterCount }} 章</span>
          <span v-if="novel.kudos">❤️ {{ novel.kudos }}</span>
          <span class="ml-auto">{{ formattedDate }}</span>
        </div>
        
        <div 
          v-if="novel.isComplete !== undefined"
          :class="[
            'inline-block mt-3 text-xs px-3 py-1 rounded-full',
            novel.isComplete ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-600'
          ]"
        >
          {{ novel.isComplete ? '已完结' : '连载中' }}
        </div>
      </div>
    </router-link>
  </article>
</template>
