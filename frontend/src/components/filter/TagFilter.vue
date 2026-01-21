<script setup lang="ts">
import { ref, computed } from 'vue';
import { ChevronRight, ChevronDown } from 'lucide-vue-next';

const props = defineProps<{
  selectedTags: string[];
  excludeOpen?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:selected-tags', tags: string[]): void;
  (e: 'toggle-exclude'): void;
}>();

const customTag = ref('');

const defaultTags = ['素祥', '祥素', 'そよさき', 'Nagasaki Soyo/Togawa Sakiko'];

const allTags = computed(() => {
  // 合并所有标签
  const set = new Set([...defaultTags, ...props.selectedTags]);
  return Array.from(set);
});

function toggleTag(tag: string) {
  // 切换标签
  const tags = [...props.selectedTags];
  const index = tags.indexOf(tag);
  if (index > -1) {
    tags.splice(index, 1);
  } else {
    tags.push(tag);
  }
  emit('update:selected-tags', tags);
}

function addCustomTag() {
  // 添加自定义标签
  const tag = customTag.value.trim();
  if (tag && !props.selectedTags.includes(tag)) {
    emit('update:selected-tags', [...props.selectedTags, tag]);
  }
  customTag.value = '';
}

function isSelected(tag: string) {
  // 判断是否已选择
  return props.selectedTags.includes(tag);
}
</script>

<template>
  <div class="flex items-center gap-3 flex-wrap">
    <button type="button"
      class="w-6 h-6 flex items-center justify-center rounded border border-gray-200 text-gray-600 hover:border-red-400 hover:text-red-500 transition-all dark:border-gray-600 dark:text-gray-400 dark:hover:border-red-400 dark:hover:text-red-400"
      @click="emit('toggle-exclude')" :title="props.excludeOpen ? '收起排除标签' : '展开排除标签'" aria-label="切换排除标签">
      <ChevronDown v-if="props.excludeOpen" class="w-4 h-4" />
      <ChevronRight v-else class="w-4 h-4" />
    </button>
    <span class="font-medium text-gray-700 whitespace-nowrap dark:text-gray-300">标签:</span>
    <div class="flex gap-1.5 flex-wrap">
      <button v-for="tag in allTags" :key="tag" :class="[
        'px-3 py-1.5 border rounded-full text-sm cursor-pointer transition-all',
        isSelected(tag)
          ? 'bg-soyo text-white border-soyo'
          : 'border-gray-200 bg-white hover:border-soyo hover:text-soyo-dark dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-soyo dark:hover:text-soyo-light'
      ]" @click="toggleTag(tag)">
        {{ tag }}
      </button>
    </div>
    <div class="flex gap-1">
      <input v-model="customTag" type="text" placeholder="添加标签..." @keyup.enter="addCustomTag"
        class="px-3 py-1.5 border border-gray-200 rounded-full text-sm w-28 focus:outline-none focus:border-primary bg-white text-gray-900 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      <button @click="addCustomTag" :disabled="!customTag.trim()" class="w-8 h-8 border border-gray-200 bg-white rounded-full cursor-pointer text-lg flex items-center justify-center text-gray-500
               hover:bg-primary hover:text-white hover:border-primary transition-all
               disabled:opacity-50 disabled:cursor-not-allowed
               dark:bg-gray-800 dark:border-gray-600 dark:text-white dark:hover:bg-primary">
        +
      </button>
    </div>
  </div>
</template>
