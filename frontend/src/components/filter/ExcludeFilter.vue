<script setup lang="ts">
import { ref, computed } from 'vue';

const props = withDefaults(defineProps<{
  excludeTags: string[];
  open?: boolean;
}>(), {
  open: false,
});

const emit = defineEmits<{
  (e: 'update:exclude-tags', tags: string[]): void;
}>();

const newTag = ref('');

// 默认的排除标签（供用户选择）  
const defaultExcludeTags = [
  'all祥', '祥睦', '睦祥', '祥希', '希祥', '要乐奈', 
  '素爱', '祥爱', '爱祥', '祥初', '祥灯', '高松灯', 
  '千早爱音', '三角初华', '海祥', '灯祥', '初祥', 'ansy', '爱素'
];

const allTags = computed(() => {
  // 合并所有标签
  const set = new Set([...defaultExcludeTags, ...props.excludeTags]);
  return Array.from(set);
});

function toggleTag(tag: string) {
  // 切换排除标签
  const tags = [...props.excludeTags];
  const index = tags.indexOf(tag);
  if (index > -1) {
    tags.splice(index, 1);
  } else {
    tags.push(tag);
  }
  emit('update:exclude-tags', tags);
}

function addCustomTag() {
  // 添加自定义标签
  const tag = newTag.value.trim();
  if (tag && !props.excludeTags.includes(tag)) {
    emit('update:exclude-tags', [...props.excludeTags, tag]);
  }
  newTag.value = '';
}

function isSelected(tag: string) {
  // 判断是否已选择
  return props.excludeTags.includes(tag);
}
</script>

<template>
  <div v-if="props.open" class="flex items-center gap-3 flex-wrap">
    <span class="font-medium text-gray-700 whitespace-nowrap dark:text-gray-300">排除:</span>
    <div class="flex gap-1.5 flex-wrap">
      <button
        v-for="tag in allTags"
        :key="tag"
        :class="[
          'px-3 py-1.5 border rounded-full text-sm cursor-pointer transition-all',
          isSelected(tag) 
            ? 'bg-red-500 text-white border-red-500' 
            : 'border-gray-200 bg-white hover:border-red-400 hover:text-red-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-red-400 dark:hover:text-red-400'
        ]"
        @click="toggleTag(tag)"
        :title="isSelected(tag) ? '点击取消排除' : '点击排除此标签'"
      >
        {{ tag }}
      </button>
    </div>
    <div class="flex gap-1">
      <input 
        v-model="newTag"
        type="text"
        placeholder="添加排除..."
        @keyup.enter="addCustomTag"
        class="px-3 py-1.5 border border-gray-200 rounded-full text-sm w-28 focus:outline-none focus:border-red-400 bg-white text-gray-900 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
      />
      <button 
        @click="addCustomTag" 
        :disabled="!newTag.trim()"
        class="w-8 h-8 border border-gray-200 bg-white rounded-full cursor-pointer text-lg flex items-center justify-center text-gray-500
               hover:bg-red-500 hover:text-white hover:border-red-500 transition-all
               disabled:opacity-50 disabled:cursor-not-allowed
               dark:bg-gray-800 dark:border-gray-600 dark:text-white dark:hover:bg-red-500"
      >
        +
      </button>
    </div>
  </div>
</template>
