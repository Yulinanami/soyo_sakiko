<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElButton, ElCheckTag, ElInput, ElSpace, ElText } from 'element-plus';
import { ArrowDown, ArrowRight, Plus } from '@element-plus/icons-vue';

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
  <el-space wrap :size="12" alignment="center">
    <el-button circle plain size="small" :icon="props.excludeOpen ? ArrowDown : ArrowRight"
      @click="emit('toggle-exclude')" :title="props.excludeOpen ? '收起排除标签' : '展开排除标签'"
      aria-label="切换排除标签" />
    <el-text tag="strong">标签:</el-text>
    <el-space wrap :size="6">
      <el-check-tag v-for="tag in allTags" :key="tag" type="primary" :checked="isSelected(tag)"
        @change="toggleTag(tag)">
        {{ tag }}
      </el-check-tag>
    </el-space>
    <el-space :size="4">
      <el-input v-model="customTag" placeholder="添加标签..." size="small" class="w-28"
        @keyup.enter="addCustomTag" />
      <el-button circle size="small" :icon="Plus" :disabled="!customTag.trim()" aria-label="添加标签"
        @click="addCustomTag" />
    </el-space>
  </el-space>
</template>
