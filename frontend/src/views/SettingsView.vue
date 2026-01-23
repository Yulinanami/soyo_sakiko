<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from "vue";
import { credentialsApi } from "@services/api";
import { useNovelsStore } from "@stores/novels";
import type { CredentialState } from "@app-types/source";

const novelsStore = useNovelsStore();

const credentialStatus = ref<{
  pixiv: CredentialState;
  lofter: CredentialState;
}>({
  pixiv: { state: "idle", message: "", configured: false },
  lofter: { state: "idle", message: "", configured: false },
});
const pollingTimer = ref<number | null>(null);
const resetting = ref(false);

async function refreshCredentialStatus() {
  // 刷新登录状态
  const [pixiv, lofter] = await Promise.all([
    credentialsApi.status("pixiv"),
    credentialsApi.status("lofter"),
  ]);
  credentialStatus.value.pixiv = pixiv;
  credentialStatus.value.lofter = lofter;
}

function startPolling() {
  // 开始定时查看
  if (pollingTimer.value) return;
  pollingTimer.value = window.setInterval(async () => {
    await refreshCredentialStatus();
    const running = (["pixiv", "lofter"] as const).some(
      (key) => credentialStatus.value[key].state === "running",
    );
    if (!running && pollingTimer.value) {
      clearInterval(pollingTimer.value);
      pollingTimer.value = null;
    }
  }, 2000);
}

async function startCredential(source: "pixiv" | "lofter") {
  // 开始登录
  await credentialsApi.start(source);
  await refreshCredentialStatus();
  startPolling();
}

async function clearCredential(source: "pixiv" | "lofter") {
  // 清除登录信息
  await credentialsApi.clear(source);
  await refreshCredentialStatus();
}

async function resetTagConfigs() {
  // 重置所有标签配置
  resetting.value = true;
  try {
    await novelsStore.resetToDefaults();
    await novelsStore.fetchNovels(true);
  } finally {
    resetting.value = false;
  }
}

onMounted(async () => {
  // 进入页面时刷新状态
  await refreshCredentialStatus();
});

onBeforeUnmount(() => {
  // 离开页面时停止定时查看
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value);
    pollingTimer.value = null;
  }
});
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
    <header
      class="bg-white border-b border-gray-200 dark:bg-gray-800 dark:border-gray-700 transition-colors duration-300 shadow-sm">
      <div class="px-6 py-6">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">设置</h1>
        <p class="text-sm text-gray-500 mt-1 dark:text-gray-400">
          登录并配置需要凭证的数据源。
        </p>
      </div>
    </header>

    <main class="p-6">
      <section
        class="bg-white rounded-xl border border-gray-200 p-6 space-y-4 max-w-3xl dark:bg-gray-800 dark:border-gray-700 transition-colors duration-300">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-base font-semibold text-gray-900 dark:text-white">
              Pixiv 登录
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400">
              用于搜索 Pixiv 同人文。
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" class="flex items-center gap-2 px-4 py-2 border-2 rounded-lg text-sm transition-all"
              :class="credentialStatus.pixiv.configured
                ? 'border-green-400 text-green-700 dark:text-green-400 dark:border-green-500/50'
                : 'border-gray-200 hover:border-sakiko hover:text-sakiko-dark dark:border-gray-600 dark:text-gray-300 dark:hover:border-sakiko dark:hover:text-sakiko-light'
                " @click="startCredential('pixiv')">
              <span v-if="credentialStatus.pixiv.state === 'running'"
                class="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span>{{
                credentialStatus.pixiv.configured ? "重新登录" : "开始登录"
                }}</span>
            </button>
            <button type="button"
              class="px-3 py-2 border-2 rounded-lg text-sm border-red-200 text-red-600 hover:border-red-400 hover:text-red-700 transition-all dark:border-red-900/30 dark:text-red-400 dark:hover:border-red-500/50 dark:hover:text-red-300"
              @click="clearCredential('pixiv')">
              清除
            </button>
          </div>
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400" v-if="credentialStatus.pixiv.message">
          {{ credentialStatus.pixiv.message }}
        </div>
      </section>

      <section
        class="bg-white rounded-xl border border-gray-200 p-6 space-y-4 max-w-3xl mt-6 dark:bg-gray-800 dark:border-gray-700 transition-colors duration-300">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-base font-semibold text-gray-900 dark:text-white">
              Lofter 登录
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400">
              用于搜索 Lofter 同人文。
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" class="flex items-center gap-2 px-4 py-2 border-2 rounded-lg text-sm transition-all"
              :class="credentialStatus.lofter.configured
                ? 'border-green-400 text-green-700 dark:text-green-400 dark:border-green-500/50'
                : 'border-gray-200 hover:border-soyo hover:text-soyo-dark dark:border-gray-600 dark:text-gray-300 dark:hover:border-soyo dark:hover:text-soyo-light'
                " @click="startCredential('lofter')">
              <span v-if="credentialStatus.lofter.state === 'running'"
                class="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span>{{
                credentialStatus.lofter.configured ? "重新登录" : "开始登录"
                }}</span>
            </button>
            <button type="button"
              class="px-3 py-2 border-2 rounded-lg text-sm border-red-200 text-red-600 hover:border-red-400 hover:text-red-700 transition-all dark:border-red-900/30 dark:text-red-400 dark:hover:border-red-500/50 dark:hover:text-red-300"
              @click="clearCredential('lofter')">
              清除
            </button>
          </div>
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400" v-if="credentialStatus.lofter.message">
          {{ credentialStatus.lofter.message }}
        </div>
      </section>

      <p v-if="
        credentialStatus.pixiv.state === 'running' ||
        credentialStatus.lofter.state === 'running'
      " class="text-xs text-gray-500 mt-4 dark:text-gray-400">
        已弹出浏览器窗口，请在窗口内完成登录。
      </p>

      <!-- 标签配置重置 -->
      <section
        class="bg-white rounded-xl border border-gray-200 p-6 space-y-4 max-w-3xl mt-6 dark:bg-gray-800 dark:border-gray-700 transition-colors duration-300">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-base font-semibold text-gray-900 dark:text-white">
              标签配置
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400">
              重置搜索标签和排除标签为默认值。
            </div>
          </div>
          <button type="button"
            class="flex items-center gap-2 px-4 py-2 border-2 rounded-lg text-sm transition-all border-orange-200 text-orange-600 hover:border-orange-400 hover:text-orange-700 dark:border-orange-900/30 dark:text-orange-400 dark:hover:border-orange-500/50 dark:hover:text-orange-300"
            :disabled="resetting" @click="resetTagConfigs">
            <span v-if="resetting"
              class="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
            <span>{{ resetting ? '重置中...' : '重置为默认' }}</span>
          </button>
        </div>
      </section>
    </main>
  </div>
</template>
