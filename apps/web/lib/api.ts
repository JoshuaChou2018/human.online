/**
 * API 客户端
 */
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';

// API 基础配置
// API 基础配置（使用相对路径，通过 Next.js rewrite 转发到后端）
// 本地开发如需直接访问后端，可设为: http://localhost:8000/api/v1
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

// 请求拦截器 - 添加认证 token
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      // 从 zustand persist 存储中获取 token
      const authStorage = localStorage.getItem('auth-storage');
      if (authStorage) {
        try {
          const { state } = JSON.parse(authStorage);
          if (state?.token) {
            config.headers.Authorization = `Bearer ${state.token}`;
          }
        } catch (e) {
          console.error('Failed to parse auth storage:', e);
        }
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token 过期，清除本地存储
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// API 方法封装
export const api = {
  // GET 请求
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.get<T>(url, config).then((res) => res.data),

  // POST 请求
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.post<T>(url, data, config).then((res) => res.data),

  // PUT 请求
  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.put<T>(url, data, config).then((res) => res.data),

  // DELETE 请求
  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.delete<T>(url, config).then((res) => res.data),

  // 文件上传
  upload: <T>(url: string, formData: FormData, onProgress?: (progress: number) => void) =>
    apiClient.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    }).then((res) => res.data),
};

// 认证相关 API
export const authApi = {
  register: (data: { email: string; username: string; password: string }) =>
    api.post('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),

  logout: () => api.post('/auth/logout'),

  getMe: () => api.get('/auth/me'),
};

// 数字分身相关 API
export const avatarApi = {
  list: (params?: { type?: string; status?: string; search?: string; page?: number; page_size?: number }) =>
    api.get('/avatars', { params }),

  getFeatured: () => api.get('/avatars/featured'),

  getById: (id: string) => api.get(`/avatars/${id}`),

  create: (data: { name: string; description?: string; avatar_type?: string }) =>
    api.post('/avatars', data),

  update: (id: string, data: Partial<{ name: string; description: string; is_public: boolean }>) =>
    api.put(`/avatars/${id}`, data),

  delete: (id: string) => api.delete(`/avatars/${id}`),

  startWeaving: (id: string) =>
    api.post(`/avatars/${id}/weave`),

  getStatus: (id: string) =>
    api.get(`/avatars/${id}/status`),
};

// 数据源相关 API
export const dataSourceApi = {
  list: (avatarId: string) =>
    api.get(`/avatars/${avatarId}/data-sources`),

  upload: (avatarId: string, file: File, sourceType: string, onProgress?: (progress: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_type', sourceType);
    return api.upload(`/avatars/${avatarId}/data-sources`, formData, onProgress);
  },

  delete: (avatarId: string, sourceId: string) =>
    api.delete(`/avatars/${avatarId}/data-sources/${sourceId}`),
};

// 对话相关 API
export const conversationApi = {
  list: () => api.get('/conversations'),

  create: (data: { participant_ids: string[]; title?: string }) =>
    api.post('/conversations', data),

  getById: (id: string) => api.get(`/conversations/${id}`),

  getMessages: (id: string, params?: { limit?: number; before_id?: string }) =>
    api.get(`/conversations/${id}/messages`, { params }),

  sendMessage: (id: string, content: string) =>
    api.post(`/conversations/${id}/messages`, { content }),
};

// 模拟相关 API
export const simulationApi = {
  list: (params?: { page?: number; page_size?: number }) =>
    api.get('/simulations', { params }),

  create: (data: {
    name: string;
    description?: string;
    initial_message: string;
    initiator_avatar_id: string;
    avatar_ids: string[];
  }) => api.post('/simulations', data),

  getById: (id: string) => api.get(`/simulations/${id}`),

  start: (id: string) => api.post(`/simulations/${id}/start`),

  getResults: (id: string) => api.get(`/simulations/${id}/results`),

  delete: (id: string) => api.delete(`/simulations/${id}`),
};

// 市场相关 API
export const marketApi = {
  // 获取分类
  getCategories: () => api.get('/market/categories'),

  // 获取市场分身列表
  getAvatars: (params?: {
    category?: string;
    search?: string;
    sort_by?: string;
    avatar_type?: string;
    page?: number;
    page_size?: number;
  }) => api.get('/market/avatars', { params }),

  // 获取精选分身
  getFeatured: (limit?: number) =>
    api.get('/market/avatars/featured', { params: { limit } }),

  // 获取分身详情
  getAvatarDetail: (id: string) => api.get(`/market/avatars/${id}`),

  // 克隆分身
  cloneAvatar: (id: string, data: {
    new_name?: string;
    new_description?: string;
    custom_notes?: string;
    force?: boolean;
  }) => api.post(`/market/avatars/${id}/clone`, data),

  // 获取分身统计
  getAvatarStats: (id: string) => api.get(`/market/avatars/${id}/stats`),

  // 获取评价列表
  getReviews: (id: string, params?: { page?: number; page_size?: number }) =>
    api.get(`/market/avatars/${id}/reviews`, { params }),

  // 创建评价
  createReview: (id: string, data: { rating: number; comment?: string }) =>
    api.post(`/market/avatars/${id}/reviews`, data),
  
  // 获取当前用户的评价
  getMyReview: (id: string) => 
    api.get(`/market/avatars/${id}/my-review`),
  
  // 更新评价
  updateReview: (id: string, data: { rating: number; comment?: string }) =>
    api.put(`/market/avatars/${id}/reviews`, data),
  
  // 删除评价
  deleteReview: (id: string) =>
    api.delete(`/market/avatars/${id}/reviews`),
};

// 沙盒 API
export const sandboxApi = {
  // 获取分身池
  getPool: () => api.get('/sandbox/pool'),
  
  // 获取沙盒成员
  getMembers: (onlyActive?: boolean) => 
    api.get('/sandbox/members', { params: { only_active: onlyActive } }),
  
  // 获取沙盒活动
  getActivities: (limit?: number) => 
    api.get('/sandbox/activities', { params: { limit } }),
  
  // 获取沙盒统计
  getStats: () => api.get('/sandbox/stats'),
  
  // 加入/离开沙盒
  toggleMember: (avatarId: string, join: boolean) => 
    api.post('/sandbox/toggle', { avatar_id: avatarId, join }),
};

export default apiClient;
