<script setup lang="ts">
import { useSourcesStore } from '../../stores/sources';
import ao3Logo from '../../assets/ao3.png';
import pixivLogo from '../../assets/pixiv.png';
import lofterLogo from '../../assets/lofter.png';
import { Lock } from 'lucide-vue-next';

const sourcesStore = useSourcesStore();
const props = defineProps<{
  loadingSources?: Record<string, boolean>;
}>();

const emit = defineEmits<{
  (e: 'change'): void;
}>();

// Source logos
const sourceLogos: Record<string, string> = {
  ao3: ao3Logo,
  pixiv: pixivLogo,
  lofter: lofterLogo,
};

function toggle(name: string) {
  sourcesStore.toggleSource(name);
  emit('change');
}
</script>

<template>
  <div class="flex items-center gap-3">
    <span class="font-medium text-gray-700 whitespace-nowrap">数据源:</span>
    <div class="flex gap-2 flex-wrap">
      <button
        v-for="source in sourcesStore.sources"
        :key="source.name"
        :class="[
          'flex items-center gap-1.5 px-3 py-2 border-2 rounded-lg cursor-pointer transition-all text-sm',
          source.enabled 
            ? 'border-sakiko bg-sakiko text-white' 
            : 'border-gray-200 bg-white hover:border-sakiko hover:text-sakiko-dark',
          source.requiresAuth && !source.enabled ? 'opacity-60' : ''
        ]"
        @click="toggle(source.name)"
        :title="source.requiresAuth ? '需要配置账号' : ''"
      >
        <span
          v-if="source.enabled && props.loadingSources?.[source.name]"
          class="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin"
        ></span>
        <span v-else-if="sourceLogos[source.name]" class="text-base">
          <img 
            :src="sourceLogos[source.name]" 
            :alt="source.displayName"
            class="w-4 h-4 object-contain"
          />
        </span>
        <span v-else class="text-base">{{ source.icon }}</span>
        <span>{{ source.displayName }}</span>
        <Lock v-if="source.requiresAuth && !source.enabled" class="w-3 h-3" />
      </button>
    </div>
  </div>
</template>
