<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import {
  Delete,
  Key,
  RefreshRight,
  Setting,
} from "@element-plus/icons-vue";
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
  } finally {
    resetting.value = false;
  }
}

function handleFetchModeChange(
  value: string | number | boolean | undefined,
) {
  if (value === "quantity" || value === "date") {
    novelsStore.setFetchMode(value);
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
  <div class="settings-page">
    <header class="page-hero">
      <ElRow class="page-heading" align="middle" justify="space-between">
        <ElSpace :size="16">
          <ElAvatar class="page-avatar" :size="54" :icon="Setting" />
          <ElSpace direction="vertical" alignment="flex-start" :size="4">
            <ElText tag="h1" class="page-title">设置</ElText>
            <ElText tag="p" class="page-subtitle">
              管理同人文获取方式、数据源凭证与标签配置
            </ElText>
          </ElSpace>
        </ElSpace>
      </ElRow>
    </header>

    <main class="page-content">
      <ElSpace class="settings-stack" direction="vertical" fill :size="18">
        <ElCard shadow="never">
          <ElRow class="settings-row" :gutter="24" align="middle">
            <ElCol :xs="24" :sm="14">
              <ElSpace direction="vertical" alignment="flex-start" :size="4">
                <ElText tag="strong" size="large">同人文获取方式</ElText>
                <ElText type="info" size="small">
                  按日期会优先显示当天作品；当天没有时自动跳到最近有作品的日期。
                </ElText>
              </ElSpace>
            </ElCol>
            <ElCol :xs="24" :sm="10">
              <ElRow justify="end">
                <ElRadioGroup
                  :model-value="novelsStore.fetchMode"
                  :disabled="novelsStore.loading"
                  @change="handleFetchModeChange"
                >
                  <ElRadioButton value="quantity">按数量</ElRadioButton>
                  <ElRadioButton value="date">按日期</ElRadioButton>
                </ElRadioGroup>
              </ElRow>
            </ElCol>
          </ElRow>
        </ElCard>

        <ElCard shadow="never">
          <ElSpace class="card-content" direction="vertical" fill :size="18">
            <ElRow class="settings-row" :gutter="24" align="middle">
              <ElCol :xs="24" :sm="14">
                <ElSpace direction="vertical" alignment="flex-start" :size="4">
                  <ElSpace wrap :size="10">
                    <ElText tag="strong" size="large">Pixiv 登录</ElText>
                    <ElTag
                      :type="credentialStatus.pixiv.configured ? 'success' : 'info'"
                      effect="light"
                      round
                      size="small"
                    >
                      {{ credentialStatus.pixiv.configured ? "已配置" : "未配置" }}
                    </ElTag>
                  </ElSpace>
                  <ElText type="info" size="small">用于搜索 Pixiv 同人文。</ElText>
                </ElSpace>
              </ElCol>
              <ElCol :xs="24" :sm="10">
                <ElRow justify="end">
                  <ElSpace wrap :size="10">
                    <ElButton
                      :type="credentialStatus.pixiv.configured ? 'success' : 'primary'"
                      :icon="credentialStatus.pixiv.configured ? RefreshRight : Key"
                      :loading="credentialStatus.pixiv.state === 'running'"
                      @click="startCredential('pixiv')"
                    >
                      {{ credentialStatus.pixiv.configured ? "重新登录" : "开始登录" }}
                    </ElButton>
                    <ElButton
                      type="danger"
                      plain
                      :icon="Delete"
                      @click="clearCredential('pixiv')"
                    >
                      清除
                    </ElButton>
                  </ElSpace>
                </ElRow>
              </ElCol>
            </ElRow>
            <ElAlert
              v-if="credentialStatus.pixiv.message"
              :title="credentialStatus.pixiv.message"
              :type="credentialStatus.pixiv.configured ? 'success' : 'info'"
              show-icon
              :closable="false"
            />
          </ElSpace>
        </ElCard>

        <ElCard shadow="never">
          <ElSpace class="card-content" direction="vertical" fill :size="18">
            <ElRow class="settings-row" :gutter="24" align="middle">
              <ElCol :xs="24" :sm="14">
                <ElSpace direction="vertical" alignment="flex-start" :size="4">
                  <ElSpace wrap :size="10">
                    <ElText tag="strong" size="large">Lofter 登录</ElText>
                    <ElTag
                      :type="credentialStatus.lofter.configured ? 'success' : 'info'"
                      effect="light"
                      round
                      size="small"
                    >
                      {{ credentialStatus.lofter.configured ? "已配置" : "未配置" }}
                    </ElTag>
                  </ElSpace>
                  <ElText type="info" size="small">用于搜索 Lofter 同人文。</ElText>
                </ElSpace>
              </ElCol>
              <ElCol :xs="24" :sm="10">
                <ElRow justify="end">
                  <ElSpace wrap :size="10">
                    <ElButton
                      :type="credentialStatus.lofter.configured ? 'success' : 'primary'"
                      :icon="credentialStatus.lofter.configured ? RefreshRight : Key"
                      :loading="credentialStatus.lofter.state === 'running'"
                      @click="startCredential('lofter')"
                    >
                      {{ credentialStatus.lofter.configured ? "重新登录" : "开始登录" }}
                    </ElButton>
                    <ElButton
                      type="danger"
                      plain
                      :icon="Delete"
                      @click="clearCredential('lofter')"
                    >
                      清除
                    </ElButton>
                  </ElSpace>
                </ElRow>
              </ElCol>
            </ElRow>
            <ElAlert
              v-if="credentialStatus.lofter.message"
              :title="credentialStatus.lofter.message"
              :type="credentialStatus.lofter.configured ? 'success' : 'info'"
              show-icon
              :closable="false"
            />
          </ElSpace>
        </ElCard>

        <ElAlert
          v-if="
            credentialStatus.pixiv.state === 'running' ||
            credentialStatus.lofter.state === 'running'
          "
          title="已弹出浏览器窗口，请在窗口内完成登录。"
          type="info"
          show-icon
          :closable="false"
        />

        <ElCard shadow="never">
          <ElRow class="settings-row" :gutter="24" align="middle">
            <ElCol :xs="24" :sm="16">
              <ElSpace direction="vertical" alignment="flex-start" :size="4">
                <ElText tag="strong" size="large">标签配置</ElText>
                <ElText type="info" size="small">重置搜索标签和排除标签为默认值。</ElText>
              </ElSpace>
            </ElCol>
            <ElCol :xs="24" :sm="8">
              <ElRow justify="end">
                <ElSpace wrap>
                  <ElButton
                    type="warning"
                    plain
                    :icon="RefreshRight"
                    :loading="resetting"
                    @click="resetTagConfigs"
                  >
                    重置为默认
                  </ElButton>
                </ElSpace>
              </ElRow>
            </ElCol>
          </ElRow>
        </ElCard>
      </ElSpace>
    </main>
  </div>
</template>

<style scoped>
.settings-stack {
  width: 100%;
}

.settings-row {
  row-gap: 16px;
}

.card-content {
  width: 100%;
}
</style>
