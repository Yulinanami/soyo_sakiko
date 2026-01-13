import axios from 'axios';
import type { Novel, NovelListResponse, NovelSearchParams } from '../types/novel';
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '../types/user';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Novel API
export const novelApi = {
  search: async (params: NovelSearchParams): Promise<NovelListResponse> => {
    const { data } = await api.get('/novels', { params });
    return data;
  },

  getDetail: async (source: string, id: string): Promise<Novel> => {
    const { data } = await api.get(`/novels/${source}/${id}`);
    return data;
  },

  getChapters: async (source: string, id: string) => {
    const { data } = await api.get(`/novels/${source}/${id}/chapters`);
    return data;
  },

  getChapterContent: async (source: string, id: string, chapter: number): Promise<string> => {
    const { data } = await api.get(`/novels/${source}/${id}/chapters/${chapter}`);
    return data;
  },
};

// Auth API
export const authApi = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const { data } = await api.post('/auth/login', credentials);
    return data;
  },

  register: async (info: RegisterRequest): Promise<AuthResponse> => {
    const { data } = await api.post('/auth/register', info);
    return data;
  },

  getProfile: async (): Promise<User> => {
    const { data } = await api.get('/auth/me');
    return data;
  },
};

// Favorites API
export const favoritesApi = {
  getAll: async () => {
    const { data } = await api.get('/user/favorites');
    return data;
  },

  add: async (novel: Partial<Novel>) => {
    const { data } = await api.post('/user/favorites', novel);
    return data;
  },

  remove: async (id: number) => {
    await api.delete(`/user/favorites/${id}`);
  },
};

// Sources API
export const sourcesApi = {
  getStatus: async () => {
    const { data } = await api.get('/sources/status');
    return data;
  },
};

export default api;
