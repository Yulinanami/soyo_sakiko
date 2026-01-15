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
const defaultExcludeTags = ['爱素', '愛素', '素爱', '素愛', '燈素', '灯素', '素燈', '素灯', '希素', '素希'];

const allTags = computed(() => {
  const set = new Set([...defaultExcludeTags, ...props.excludeTags]);
  return Array.from(set);
});

function toggleTag(tag: string) {
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
  const tag = newTag.value.trim();
  if (tag && !props.excludeTags.includes(tag)) {
    emit('update:exclude-tags', [...props.excludeTags, tag]);
  }
  newTag.value = '';
}

function isSelected(tag: string) {
  return props.excludeTags.includes(tag);
}
</script>

<template>
  <div v-if="props.open" class="flex items-center gap-3 flex-wrap">
    <span class="font-medium text-gray-700 whitespace-nowrap">排除:</span>
    <div class="flex gap-1.5 flex-wrap">
      <button
        v-for="tag in allTags"
        :key="tag"
        :class="[
          'px-3 py-1.5 border rounded-full text-sm cursor-pointer transition-all',
          isSelected(tag) 
            ? 'bg-red-500 text-white border-red-500' 
            : 'border-gray-200 bg-white hover:border-red-400 hover:text-red-500'
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
        class="px-3 py-1.5 border border-gray-200 rounded-full text-sm w-28 focus:outline-none focus:border-red-400"
      />
      <button 
        @click="addCustomTag" 
        :disabled="!newTag.trim()"
        class="w-8 h-8 border border-gray-200 bg-white rounded-full cursor-pointer text-lg flex items-center justify-center
               hover:bg-red-500 hover:text-white hover:border-red-500 transition-all
               disabled:opacity-50 disabled:cursor-not-allowed"
      >
        +
      </button>
    </div>
  </div>
</template>
