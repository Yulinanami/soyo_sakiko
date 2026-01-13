<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{
  selectedTags: string[];
}>();

const emit = defineEmits<{
  (e: 'update:selected-tags', tags: string[]): void;
}>();

const customTag = ref('');

const defaultTags = ['素祥', '祥素', 'Nagasaki Soyo/Toyokawa Sakiko', 'MyGO!!!!!'];

const allTags = computed(() => {
  const set = new Set([...defaultTags, ...props.selectedTags]);
  return Array.from(set);
});

function toggleTag(tag: string) {
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
  const tag = customTag.value.trim();
  if (tag && !props.selectedTags.includes(tag)) {
    emit('update:selected-tags', [...props.selectedTags, tag]);
  }
  customTag.value = '';
}

function isSelected(tag: string) {
  return props.selectedTags.includes(tag);
}
</script>

<template>
  <div class="flex items-center gap-3 flex-wrap">
    <span class="font-medium text-gray-700 whitespace-nowrap">标签:</span>
    <div class="flex gap-1.5 flex-wrap">
      <button
        v-for="tag in allTags"
        :key="tag"
        :class="[
          'px-3 py-1.5 border rounded-full text-sm cursor-pointer transition-all',
          isSelected(tag) 
            ? 'bg-soyo text-white border-soyo' 
            : 'border-gray-200 bg-white hover:border-soyo hover:text-soyo-dark'
        ]"
        @click="toggleTag(tag)"
      >
        {{ tag }}
      </button>
    </div>
    <div class="flex gap-1">
      <input 
        v-model="customTag"
        type="text"
        placeholder="添加标签..."
        @keyup.enter="addCustomTag"
        class="px-3 py-1.5 border border-gray-200 rounded-full text-sm w-28 focus:outline-none focus:border-primary"
      />
      <button 
        @click="addCustomTag" 
        :disabled="!customTag.trim()"
        class="w-8 h-8 border border-gray-200 bg-white rounded-full cursor-pointer text-lg flex items-center justify-center
               hover:bg-primary hover:text-white hover:border-primary transition-all
               disabled:opacity-50 disabled:cursor-not-allowed"
      >
        +
      </button>
    </div>
  </div>
</template>
