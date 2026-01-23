import axios from "axios";
import type {
  Novel,
  NovelListResponse,
  NovelSearchParams,
} from "@app-types/novel";
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
} from "@app-types/user";
import type { FavoriteItem, HistoryItem } from "@app-types/user_data";
import type { CredentialState } from "@app-types/source";
import { useUserStore } from "@stores/user";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT_MS) || 120000;

const api = axios.create({
  baseURL: API_BASE,
  timeout: API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
});

// 统一处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const url = String(error.config?.url ?? "");
      if (!url.includes("/auth/login") && !url.includes("/auth/register")) {
        const userStore = useUserStore();
        userStore.logout();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export const novelApi = {
  search: async (params: NovelSearchParams): Promise<NovelListResponse> => {
    // 获取搜索结果
    const searchParams = new URLSearchParams();

    params.sources.forEach((source) => searchParams.append("sources", source));

    params.tags.forEach((tag) => searchParams.append("tags", tag));

    if (params.excludeTags) {
      params.excludeTags.forEach((tag) =>
        searchParams.append("exclude_tags", tag),
      );
    }

    searchParams.append("page", String(params.page ?? 1));
    searchParams.append("page_size", String(params.pageSize ?? 20));
    searchParams.append("sort_by", params.sortBy ?? "date");
    const { data } = await api.get(`/novels?${searchParams.toString()}`);
    return unwrapData<NovelListResponse>(data);
  },

  getDetail: async (source: string, id: string): Promise<Novel> => {
    // 获取小说详情
    const { data } = await api.get(`/novels/${source}/${id}`);
    return unwrapData<Novel>(data);
  },

  getChapterContent: async (
    source: string,
    id: string,
    chapter: number,
  ): Promise<string> => {
    // 获取章节内容
    const { data } = await api.get(
      `/novels/${source}/${id}/chapters/${chapter}`,
    );
    return unwrapData<string>(data);
  },
};

export const authApi = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    // 登录
    const { data } = await api.post("/auth/login", credentials);
    return normalizeAuthResponse(unwrapData(data));
  },

  register: async (info: RegisterRequest): Promise<AuthResponse> => {
    // 注册
    const { data } = await api.post("/auth/register", info);
    return normalizeAuthResponse(unwrapData(data));
  },

  getProfile: async (): Promise<User> => {
    // 获取用户信息
    const { data } = await api.get("/auth/me");
    return normalizeUser(unwrapData(data));
  },
};

export const favoritesApi = {
  getAll: async (): Promise<FavoriteItem[]> => {
    // 获取收藏列表
    const { data } = await api.get("/user/favorites");
    return unwrapData<FavoriteItem[]>(data);
  },

  add: async (payload: Record<string, any>): Promise<FavoriteItem> => {
    // 添加收藏
    const { data } = await api.post("/user/favorites", payload);
    return unwrapData<FavoriteItem>(data);
  },

  remove: async (id: number) => {
    // 删除收藏
    await api.delete(`/user/favorites/${id}`);
  },
};

export const historyApi = {
  getAll: async (): Promise<HistoryItem[]> => {
    // 获取阅读记录
    const { data } = await api.get("/user/history");
    return unwrapData<HistoryItem[]>(data);
  },
  record: async (payload: Record<string, any>): Promise<HistoryItem> => {
    // 记录阅读进度
    const { data } = await api.post("/user/history", payload);
    return unwrapData<HistoryItem>(data);
  },
  remove: async (id: number) => {
    // 删除阅读记录
    await api.delete(`/user/history/${id}`);
  },
};

export const credentialsApi = {
  start: async (source: string) => {
    // 开始登录
    const { data } = await api.post(`/credentials/${source}/start`);
    return unwrapData(data);
  },
  status: async (source: string): Promise<CredentialState> => {
    // 查询登录状态
    const { data } = await api.get(`/credentials/${source}/status`);
    return unwrapData<CredentialState>(data);
  },
  clear: async (source: string) => {
    // 清除登录信息
    const { data } = await api.delete(`/credentials/${source}`);
    return unwrapData(data);
  },
};

export interface TagConfigItem {
  source: string;
  tags: string[];
  exclude_tags: string[];
}

export const tagConfigApi = {
  getAll: async (): Promise<TagConfigItem[]> => {
    // 获取所有标签配置
    const { data } = await api.get("/user/tag-configs");
    return unwrapData<TagConfigItem[]>(data);
  },

  save: async (
    source: string,
    tags: string[],
    excludeTags: string[],
  ): Promise<TagConfigItem> => {
    // 保存某个数据源的标签配置
    const { data } = await api.put(`/user/tag-configs/${source}`, {
      tags,
      exclude_tags: excludeTags,
    });
    return unwrapData<TagConfigItem>(data);
  },

  reset: async () => {
    // 重置所有标签配置
    await api.delete("/user/tag-configs");
  },
};

export function setAuthToken(token: string | null) {
  // 设置默认登录信息
  if (token && token !== "undefined" && token !== "null") {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
}

function normalizeUser(payload: any): User {
  // 整理用户数据
  return {
    id: payload.id,
    username: payload.username,
    createdAt: payload.created_at ?? payload.createdAt ?? "",
  };
}

function normalizeAuthResponse(payload: any): AuthResponse {
  // 整理登录返回
  return {
    accessToken: payload.access_token ?? payload.accessToken,
    tokenType: payload.token_type ?? payload.tokenType ?? "bearer",
    user: normalizeUser(payload.user ?? {}),
  };
}

function unwrapData<T>(payload: any): T {
  // 取出真正的数据
  if (payload && typeof payload === "object" && "data" in payload) {
    return payload.data as T;
  }
  return payload as T;
}
