<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElButton, ElCheckTag, ElCollapseTransition, ElInput, ElSpace, ElText } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';

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
  <ElCollapseTransition>
    <div v-show="props.open" style="padding-top: 16px">
      <el-space wrap :size="12" alignment="center">
        <el-text tag="strong">排除:</el-text>
        <el-space wrap :size="6">
          <el-check-tag v-for="tag in allTags" :key="tag" type="danger" :checked="isSelected(tag)"
            @change="toggleTag(tag)" :title="isSelected(tag) ? '点击取消排除' : '点击排除此标签'">
            {{ tag }}
          </el-check-tag>
          <el-space :size="4">
            <el-input v-model="newTag" placeholder="添加排除..." size="small" class="w-28"
              @keyup.enter="addCustomTag" />
            <el-button circle size="small" type="danger" plain :icon="Plus" :disabled="!newTag.trim()"
              aria-label="添加排除标签" @click="addCustomTag" />
          </el-space>
        </el-space>
      </el-space>
    </div>
  </ElCollapseTransition>
</template>
