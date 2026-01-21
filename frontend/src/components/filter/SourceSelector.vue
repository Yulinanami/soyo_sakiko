<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useSourcesStore } from '@stores/sources';
import { credentialsApi } from '@services/api';
import ao3Logo from '@assets/ao3.png';
import pixivLogo from '@assets/pixiv.png';
import lofterLogo from '@assets/lofter.png';
import bilibiliLogo from '@assets/bilibili.png';
import { Lock, RefreshCw } from 'lucide-vue-next';

const sourcesStore = useSourcesStore();
const router = useRouter();
const props = defineProps<{
  loadingSources?: Record<string, boolean>;
}>();

const emit = defineEmits<{
  (e: 'change'): void;
  (e: 'refresh'): void;
}>();

// 弹窗状态
const showCredentialDialog = ref(false);
const pendingSource = ref<string | null>(null);
const pendingSourceName = ref('');

// 来源图标
const sourceLogos: Record<string, string> = {
  ao3: ao3Logo,
  pixiv: pixivLogo,
  lofter: lofterLogo,
  bilibili: bilibiliLogo,
};

// 需要登录的来源
const credentialSources = ['pixiv', 'lofter'];

function toggle(name: string) {
  // 切换来源
  const source = sourcesStore.sources.find(s => s.name === name);

  if (source && !source.enabled && credentialSources.includes(name)) {
    sourcesStore.toggleSource(name);
    emit('change');

    checkCredentialsAsync(name, source.displayName);
    return;
  }

  sourcesStore.toggleSource(name);
  emit('change');
}

async function checkCredentialsAsync(name: string, displayName: string) {
  // 检查登录信息
  try {
    const status = await credentialsApi.status(name) as { configured: boolean };
    if (!status.configured) {
      pendingSource.value = name;
      pendingSourceName.value = displayName;
      showCredentialDialog.value = true;
    }
  } catch {
    console.warn(`Failed to check ${name} credentials`);
  }
}

function goToSettings() {
  // 跳转设置
  showCredentialDialog.value = false;
  router.push('/settings');
}

function continueWithoutCredentials() {
  // 继续启用
  showCredentialDialog.value = false;
  if (pendingSource.value) {
    sourcesStore.toggleSource(pendingSource.value);
    emit('change');
  }
  pendingSource.value = null;
}
</script>

<template>
  <div class="flex items-center gap-3">
    <span class="font-medium text-gray-700 whitespace-nowrap dark:text-gray-300">数据源:</span>
    <div class="flex gap-2 flex-wrap">
      <button v-for="source in sourcesStore.sources" :key="source.name" :class="[
        'flex items-center gap-1.5 px-3 py-2 border-2 rounded-lg cursor-pointer transition-all text-sm',
        source.enabled
          ? 'border-sakiko bg-sakiko text-white'
          : 'border-gray-200 bg-white hover:border-sakiko hover:text-sakiko-dark dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-sakiko dark:hover:text-sakiko-light',
        source.requiresAuth && !source.enabled ? 'opacity-60' : ''
      ]" @click="toggle(source.name)" :title="source.requiresAuth ? '需要配置账号' : ''">
        <span v-if="source.enabled && props.loadingSources?.[source.name]"
          class="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
        <span v-else-if="sourceLogos[source.name]" class="text-base">
          <img :src="sourceLogos[source.name]" :alt="source.displayName" class="w-4 h-4 object-contain" />
        </span>

        <span>{{ source.displayName }}</span>
        <Lock v-if="source.requiresAuth && !source.enabled" class="w-3 h-3" />
      </button>

      <!-- 刷新 -->
      <button @click="emit('refresh')"
        class="flex items-center gap-1.5 px-3 py-2 border-2 border-gray-200 bg-white rounded-lg cursor-pointer transition-all text-sm hover:border-sakiko hover:text-sakiko-dark dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-sakiko dark:hover:text-sakiko-light"
        title="刷新数据">
        <RefreshCw class="w-4 h-4" />
      </button>
    </div>
  </div>

  <!-- 登录提示 -->
  <Teleport to="body">
    <div v-if="showCredentialDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="showCredentialDialog = false">
      <div
        class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 max-w-md mx-4 animate-in fade-in zoom-in-95 duration-200">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-3">
          需要配置登录凭证
        </h3>
        <p class="text-gray-600 dark:text-gray-300 mb-6">
          <span class="font-medium text-sakiko">{{ pendingSourceName }}</span>
          需要登录凭证才能获取内容。请先前往设置页面完成配置。
        </p>
        <div class="flex gap-3 justify-end">
          <button @click="continueWithoutCredentials"
            class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
            仍然启用
          </button>
          <button @click="goToSettings"
            class="px-4 py-2 bg-sakiko text-white rounded-lg hover:bg-sakiko/90 transition-colors">
            去设置
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
