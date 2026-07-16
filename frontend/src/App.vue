<script setup lang="ts">
import { ref, watch } from 'vue';
import { useUserStore } from '@stores/user';
import { useFavoritesStore } from '@stores/favorites';
import { useNovelsStore } from '@stores/novels';
import { useRoute, useRouter } from 'vue-router';
import ao3Logo from '@assets/ao3.png';
import pixivLogo from '@assets/pixiv.png';
import lofterLogo from '@assets/lofter.png';
import bilibiliLogo from '@assets/bilibili.png';
import {
  Expand,
  Fold,
  House,
  Moon,
  Reading,
  Setting,
  Star,
  Sunny,
  SwitchButton,
  User,
} from '@element-plus/icons-vue';

const userStore = useUserStore();
const favoritesStore = useFavoritesStore();
const novelsStore = useNovelsStore();
const router = useRouter();
const route = useRoute();
const sidebarOpen = ref(window.matchMedia('(min-width: 769px)').matches);

function toggleSidebar() {
  // 切换侧边栏
  sidebarOpen.value = !sidebarOpen.value;
}

function handleLogout() {
  // 退出登录
  userStore.logout();
  router.push('/');
}

watch(
  () => userStore.isLoggedIn,
  (loggedIn) => {
    // 根据登录状态加载收藏和标签配置
    if (loggedIn) {
      favoritesStore.fetchFavorites();
      novelsStore.loadTagConfigs();
    } else {
      favoritesStore.reset();
      // 未登录时也尝试从 localStorage 加载
      novelsStore.loadTagConfigs();
    }
  },
  { immediate: true }
);

watch(
  () => route.path,
  () => {
    if (window.matchMedia('(max-width: 768px)').matches) {
      sidebarOpen.value = false;
    }
  }
);
</script>

<template>
  <el-container id="app" class="app-shell">
    <el-aside
      :class="['app-sidebar', { 'is-collapsed': !sidebarOpen }]"
      :width="sidebarOpen ? '224px' : '65px'"
    >
      <div class="sidebar-content">
        <header class="sidebar-header">
          <el-tooltip :content="sidebarOpen ? '收起菜单' : '展开菜单'" placement="bottom">
            <el-button
              class="sidebar-toggle"
              link
              circle
              :aria-label="sidebarOpen ? '收起菜单' : '展开菜单'"
              @click="toggleSidebar"
            >
              <el-icon :size="21">
                <Fold v-if="sidebarOpen" />
                <Expand v-else />
              </el-icon>
            </el-button>
          </el-tooltip>
          <router-link v-if="sidebarOpen" to="/" class="brand-link">SoyoSaki</router-link>
        </header>

        <el-scrollbar class="sidebar-scroll">
          <nav class="sidebar-nav">
            <el-menu
              class="sidebar-menu"
              :default-active="route.path"
              :collapse="!sidebarOpen"
              :collapse-transition="false"
              router
            >
              <el-menu-item index="/">
                <el-icon><House /></el-icon>
                <template #title>首页</template>
              </el-menu-item>

              <el-menu-item index="/favorites">
                <el-icon><Star /></el-icon>
                <template #title>
                  <el-row class="menu-label" justify="space-between" align="middle">
                    <span>收藏</span>
                    <el-tag
                      v-if="!userStore.isLoggedIn"
                      size="small"
                      effect="plain"
                      round
                    >
                      请登录
                    </el-tag>
                  </el-row>
                </template>
              </el-menu-item>

              <el-menu-item index="/history">
                <el-icon><Reading /></el-icon>
                <template #title>
                  <el-row class="menu-label" justify="space-between" align="middle">
                    <span>阅读记录</span>
                    <el-tag
                      v-if="!userStore.isLoggedIn"
                      size="small"
                      effect="plain"
                      round
                    >
                      请登录
                    </el-tag>
                  </el-row>
                </template>
              </el-menu-item>

              <el-menu-item index="/settings">
                <el-icon><Setting /></el-icon>
                <template #title>设置</template>
              </el-menu-item>
            </el-menu>

            <el-row class="theme-setting" justify="space-between" align="middle">
              <el-space v-if="sidebarOpen" :size="10">
                <el-icon :size="18"><Moon /></el-icon>
                <span>深色模式</span>
              </el-space>
              <el-tooltip
                :disabled="sidebarOpen"
                :content="userStore.darkMode ? '切换浅色模式' : '切换深色模式'"
                placement="right"
              >
                <el-switch
                  v-model="userStore.darkMode"
                  :active-action-icon="Moon"
                  :inactive-action-icon="Sunny"
                  :aria-label="userStore.darkMode ? '切换浅色模式' : '切换深色模式'"
                />
              </el-tooltip>
            </el-row>

            <el-divider />

            <div v-if="sidebarOpen" class="source-title">数据源</div>
            <el-space class="w-full" direction="vertical" fill :size="3">
              <el-link
                class="source-link"
                href="https://archiveofourown.org/"
                target="_blank"
                rel="noopener noreferrer"
                underline="never"
              >
                <el-space :size="12">
                  <img :src="ao3Logo" alt="AO3" class="source-logo" />
                  <span v-if="sidebarOpen">AO3</span>
                </el-space>
              </el-link>
              <el-link
                class="source-link"
                href="https://www.pixiv.net/"
                target="_blank"
                rel="noopener noreferrer"
                underline="never"
              >
                <el-space :size="12">
                  <img :src="pixivLogo" alt="Pixiv" class="source-logo" />
                  <span v-if="sidebarOpen">Pixiv</span>
                </el-space>
              </el-link>
              <el-link
                class="source-link"
                href="https://www.lofter.com/"
                target="_blank"
                rel="noopener noreferrer"
                underline="never"
              >
                <el-space :size="12">
                  <img :src="lofterLogo" alt="Lofter" class="source-logo" />
                  <span v-if="sidebarOpen">Lofter</span>
                </el-space>
              </el-link>
              <el-link
                class="source-link"
                href="https://www.bilibili.com/read/home/"
                target="_blank"
                rel="noopener noreferrer"
                underline="never"
              >
                <el-space :size="12">
                  <img :src="bilibiliLogo" alt="Bilibili" class="source-logo" />
                  <span v-if="sidebarOpen">Bilibili</span>
                </el-space>
              </el-link>
            </el-space>
          </nav>
        </el-scrollbar>

        <footer v-if="sidebarOpen || userStore.isLoggedIn" class="user-panel">
          <template v-if="userStore.isLoggedIn">
            <div v-if="sidebarOpen" class="user-session">
              <el-avatar class="user-avatar" :size="34">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="user-copy">
                <span class="user-name">{{ userStore.user?.username }}</span>
                <span class="user-status">已登录</span>
              </div>
              <el-tooltip content="登出" placement="top">
                <el-button
                  class="logout-button"
                  text
                  circle
                  type="danger"
                  aria-label="登出"
                  @click="handleLogout"
                >
                  <el-icon><SwitchButton /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
            <el-row v-else justify="center">
              <el-tooltip content="登出" placement="right">
                <el-button
                  class="logout-button"
                  text
                  circle
                  type="danger"
                  aria-label="登出"
                  @click="handleLogout"
                >
                  <el-icon><SwitchButton /></el-icon>
                </el-button>
              </el-tooltip>
            </el-row>
          </template>
          <template v-else>
            <el-button-group class="auth-actions">
              <el-button class="auth-button" plain @click="router.push('/login')">
                登录
              </el-button>
              <el-button class="auth-button" type="primary" @click="router.push('/register')">
                注册
              </el-button>
            </el-button-group>
          </template>
        </footer>
      </div>
    </el-aside>

    <div
      v-if="sidebarOpen"
      class="sidebar-backdrop"
      aria-hidden="true"
      @click="toggleSidebar"
    />

    <el-main :class="['app-main', { 'is-sidebar-open': sidebarOpen }]">
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.app-sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 40;
  height: 100vh;
  overflow: hidden;
  color: var(--el-color-white);
  background: var(--color-sakiko-dark);
  border-right: 1px solid var(--el-border-color);
  transition: width 0.3s ease;
  --el-border-color: var(--color-sakiko);
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 68px;
  padding: 0 14px;
  border-bottom: 1px solid var(--el-border-color);
}

.sidebar-toggle {
  flex: 0 0 auto;
  --el-button-text-color: var(--el-color-white);
  --el-button-hover-text-color: var(--el-color-white);
}

.brand-link {
  overflow: hidden;
  color: inherit;
  font-size: 20px;
  font-weight: 700;
  text-decoration: none;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-scroll {
  flex: 1;
  min-height: 0;
}

.sidebar-nav {
  padding: 12px;
}

.app-sidebar.is-collapsed .sidebar-nav {
  padding-inline: 0;
}

.sidebar-menu {
  border-right: 0;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: var(--el-color-white);
  --el-menu-active-color: var(--el-color-white);
  --el-menu-hover-bg-color: var(--color-sakiko);
}

.menu-label {
  width: 100%;
}

.theme-setting {
  padding: 12px 20px 0;
}

.app-sidebar.is-collapsed .theme-setting {
  justify-content: center;
  padding: 12px 0 0;
}

.source-title {
  padding: 0 12px 7px;
  color: var(--color-sakiko-pale);
  font-size: 11px;
  font-weight: 600;
}

.source-link {
  width: 100%;
  min-height: 40px;
  padding: 0 12px;
  justify-content: flex-start;
  --el-link-text-color: var(--el-color-white);
  --el-link-hover-text-color: var(--el-color-white);
}

.app-sidebar.is-collapsed .source-link {
  justify-content: center;
  padding-inline: 0;
}

.source-logo {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.user-panel {
  padding: 14px;
  border-top: 1px solid var(--el-border-color);
}

.user-session {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.user-name {
  overflow: hidden;
  font-size: 13px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-status {
  color: var(--color-sakiko-pale);
  font-size: 11px;
}

.auth-actions {
  width: 100%;
}

.auth-actions :deep(.el-button) {
  flex: 1;
}

.app-main {
  min-width: 0;
  min-height: 100vh;
  margin-left: 65px;
  overflow: visible;
  padding: 0;
  transition: margin-left 0.3s ease;
}

.app-main.is-sidebar-open {
  margin-left: 224px;
}

.sidebar-backdrop {
  display: none;
}

:global(.dark .app-sidebar) {
  background: var(--el-bg-color);
  --el-border-color: var(--el-border-color-darker);
}

:global(.dark .sidebar-menu) {
  --el-menu-hover-bg-color: var(--el-fill-color-light);
}

@media (max-width: 768px) {
  .app-sidebar {
    max-width: calc(100vw - 48px);
  }

  .sidebar-backdrop {
    position: fixed;
    inset: 0;
    z-index: 39;
    display: block;
    background: var(--el-overlay-color-lighter);
  }

  .app-main,
  .app-main.is-sidebar-open {
    margin-left: 65px;
  }
}
</style>
