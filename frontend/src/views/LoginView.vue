<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ElAlert,
  ElAvatar,
  ElButton,
  ElCard,
  ElForm,
  ElFormItem,
  ElInput,
  ElLink,
  ElRow,
  ElSpace,
  ElText,
} from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import { Lock, User } from "@element-plus/icons-vue";
import { useUserStore } from "@stores/user";

interface LoginForm {
  username: string;
  password: string;
}

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const loginFormRef = ref<FormInstance>();
const loginForm = reactive<LoginForm>({
  username: "",
  password: "",
});
const loginRules: FormRules<LoginForm> = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const loginReason = computed(() => {
  // 生成提示信息
  if (route.query.reason === "favorites") {
    return "请登录以查看收藏";
  }
  if (route.query.reason === "history") {
    return "请登录以查看阅读记录";
  }
  return "";
});

async function handleLogin() {
  // 提交登录
  const valid = await loginFormRef.value?.validate().catch(() => false);
  if (!valid) return;

  const success = await userStore.login(
    loginForm.username,
    loginForm.password,
  );
  if (success) {
    const redirect = (route.query.redirect as string) || "/";
    router.push(redirect);
  }
}
</script>

<template>
  <div class="auth-page">
    <ElCard class="auth-card" shadow="always">
      <ElSpace class="auth-heading" direction="vertical" alignment="center" :size="8">
        <ElAvatar :size="56" :icon="User" />
        <ElText tag="h1" size="large"><strong>欢迎回来</strong></ElText>
        <ElText tag="p" type="info" size="small">登录后继续使用收藏和阅读记录</ElText>
      </ElSpace>

      <ElAlert
        v-if="loginReason"
        class="auth-alert"
        :title="loginReason"
        type="warning"
        show-icon
        :closable="false"
      />

      <ElForm
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-position="top"
        size="large"
        @submit.prevent="handleLogin"
      >
        <ElFormItem label="用户名" prop="username">
          <ElInput
            v-model="loginForm.username"
            :prefix-icon="User"
            placeholder="请输入用户名"
            autocomplete="username"
          />
        </ElFormItem>

        <ElFormItem label="密码" prop="password">
          <ElInput
            v-model="loginForm.password"
            :prefix-icon="Lock"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
          />
        </ElFormItem>

        <ElAlert
          v-if="userStore.error"
          class="auth-alert"
          :title="userStore.error"
          type="error"
          show-icon
          :closable="false"
        />

        <ElButton
          class="auth-submit"
          type="primary"
          size="large"
          native-type="submit"
          :loading="userStore.loading"
        >
          登录
        </ElButton>
      </ElForm>

      <ElRow class="auth-footer" justify="center" align="middle">
        <ElSpace :size="6">
          <ElText type="info" size="small">还没有账号？</ElText>
          <RouterLink v-slot="{ href, navigate }" to="/register" custom>
            <ElLink :href="href" type="primary" underline="never" @click="navigate">
              立即注册
            </ElLink>
          </RouterLink>
        </ElSpace>
      </ElRow>
    </ElCard>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px 20px;
  background: var(--el-color-primary);
}

.auth-card {
  width: min(100%, 440px);
}

.auth-heading {
  width: 100%;
  margin-bottom: 26px;
}

.auth-alert {
  margin-bottom: 20px;
}

.auth-submit {
  width: 100%;
  margin-top: 4px;
}

.auth-footer {
  margin-top: 24px;
}
</style>
