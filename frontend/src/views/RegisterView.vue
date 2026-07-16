<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
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
import { Key, Lock, User } from "@element-plus/icons-vue";
import { useUserStore } from "@stores/user";

interface RegisterForm {
  username: string;
  password: string;
  confirmPassword: string;
}

const router = useRouter();
const userStore = useUserStore();
const registerFormRef = ref<FormInstance>();
const registerForm = reactive<RegisterForm>({
  username: "",
  password: "",
  confirmPassword: "",
});
const registerRules: FormRules<RegisterForm> = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
  confirmPassword: [
    { required: true, message: "请再次输入密码", trigger: "blur" },
  ],
};
const localError = ref("");

async function handleRegister() {
  // 提交注册
  localError.value = "";
  const valid = await registerFormRef.value?.validate().catch(() => false);
  if (!valid) return;

  if (registerForm.password !== registerForm.confirmPassword) {
    localError.value = "两次输入的密码不一致";
    return;
  }

  if (registerForm.password.length < 6) {
    localError.value = "密码长度至少为6位";
    return;
  }

  const success = await userStore.register(
    registerForm.username,
    registerForm.password,
  );
  if (success) {
    router.push("/");
  }
}
</script>

<template>
  <div class="auth-page">
    <ElCard class="auth-card" shadow="always">
      <ElSpace class="auth-heading" direction="vertical" alignment="center" :size="8">
        <ElAvatar :size="56" :icon="Key" />
        <ElText tag="h1" size="large"><strong>创建账号</strong></ElText>
        <ElText tag="p" type="info" size="small">保存喜欢的作品与每一次阅读记录</ElText>
      </ElSpace>

      <ElForm
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-position="top"
        size="large"
        @submit.prevent="handleRegister"
      >
        <ElFormItem label="用户名" prop="username">
          <ElInput
            v-model="registerForm.username"
            :prefix-icon="User"
            placeholder="请输入用户名"
            autocomplete="username"
          />
        </ElFormItem>

        <ElFormItem label="密码" prop="password">
          <ElInput
            v-model="registerForm.password"
            :prefix-icon="Lock"
            type="password"
            placeholder="请输入密码（至少6位）"
            autocomplete="new-password"
          />
        </ElFormItem>

        <ElFormItem label="确认密码" prop="confirmPassword">
          <ElInput
            v-model="registerForm.confirmPassword"
            :prefix-icon="Key"
            type="password"
            placeholder="请再次输入密码"
            autocomplete="new-password"
          />
        </ElFormItem>

        <ElAlert
          v-if="localError || userStore.error"
          class="auth-alert"
          :title="localError || userStore.error || ''"
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
          注册
        </ElButton>
      </ElForm>

      <ElRow class="auth-footer" justify="center" align="middle">
        <ElSpace :size="6">
          <ElText type="info" size="small">已有账号？</ElText>
          <RouterLink v-slot="{ href, navigate }" to="/login" custom>
            <ElLink :href="href" type="primary" underline="never" @click="navigate">
              立即登录
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
