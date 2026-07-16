<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useSourcesStore } from '@stores/sources';
import { credentialsApi } from '@services/api';
import ao3Logo from '@assets/ao3.png';
import pixivLogo from '@assets/pixiv.png';
import lofterLogo from '@assets/lofter.png';
import bilibiliLogo from '@assets/bilibili.png';
import { ElAlert, ElButton, ElDialog, ElIcon, ElSpace, ElText } from 'element-plus';
import { Lock, Refresh } from '@element-plus/icons-vue';

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
  <el-space wrap :size="12" alignment="center">
    <el-text tag="strong">数据源:</el-text>
    <el-space wrap :size="8">
      <el-button v-for="source in sourcesStore.sources" :key="source.name"
        :type="source.enabled ? 'primary' : 'default'" :plain="!source.enabled"
        :loading="source.enabled && props.loadingSources?.[source.name]" @click="toggle(source.name)"
        :title="source.requiresAuth ? '需要配置账号' : ''">
        <img v-if="sourceLogos[source.name]" :src="sourceLogos[source.name]" :alt="source.displayName"
          class="h-4 w-4 object-contain" />

        <span>{{ source.displayName }}</span>
        <el-icon v-if="source.requiresAuth && !source.enabled" :size="12"><Lock /></el-icon>
      </el-button>

      <!-- 刷新 -->
      <el-button circle plain :icon="Refresh" title="刷新数据" @click="emit('refresh')" />
    </el-space>
  </el-space>

  <!-- 登录提示 -->
  <el-dialog v-model="showCredentialDialog" title="需要配置登录凭证" width="min(90vw, 28rem)" align-center>
    <el-alert :title="pendingSourceName" type="warning" :closable="false" show-icon
      description="需要登录凭证才能获取内容。请先前往设置页面完成配置。" />
    <template #footer>
      <el-button @click="continueWithoutCredentials">仍然启用</el-button>
      <el-button type="primary" @click="goToSettings">去设置</el-button>
    </template>
  </el-dialog>
</template>
