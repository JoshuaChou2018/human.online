"use client";

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface User {
  id: string;
  email: string;
  display_name?: string;
  avatar_url?: string;
  can_create_free_avatar: boolean;
  remaining_free_quota: number;
  avatars_created: number;
  free_avatar_quota: number;
  is_new_user?: boolean;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  setToken: (token: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,

      setToken: (token: string) => {
        set({ token, isAuthenticated: true });
      },

      setUser: (user: User) => {
        set({ user, isAuthenticated: true });
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false });
        localStorage.removeItem('auth-storage');
      },

      checkAuth: async () => {
        const { token } = get();
        if (!token) return false;

        try {
          const response = await fetch(`${API_URL}/api/v1/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (response.ok) {
            const user = await response.json();
            set({ user, isAuthenticated: true });
            return true;
          } else {
            set({ token: null, user: null, isAuthenticated: false });
            return false;
          }
        } catch (error) {
          console.error('Auth check failed:', error);
          return false;
        }
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);

// API 请求封装
export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
) {
  const { token } = useAuthStore.getState();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    useAuthStore.getState().logout();
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  // 处理 204 NO_CONTENT 响应
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

// 邮箱注册
export async function register(email: string, password: string, displayName?: string): Promise<{ token: string; user: User }> {
  const response = await fetch(`${API_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password, display_name: displayName }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
    throw new Error(error.detail);
  }

  const data = await response.json();
  return {
    token: data.access_token,
    user: data.user,
  };
}

// 邮箱登录
export async function login(email: string, password: string): Promise<{ token: string; user: User }> {
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail);
  }

  const data = await response.json();
  return {
    token: data.access_token,
    user: data.user,
  };
}

// Demo 登录
export async function demoLogin(): Promise<{ token: string; user: User }> {
  try {
    const response = await fetch(`${API_URL}/api/v1/auth/demo`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: `请求失败: ${response.status}` }));
      throw new Error(error.detail || 'Demo 登录失败');
    }

    const data = await response.json();
    return {
      token: data.access_token,
      user: data.user,
    };
  } catch (err) {
    if (err instanceof TypeError && err.message.includes('fetch')) {
      throw new Error('无法连接到服务器，请确认后端服务已启动 (http://localhost:8000)');
    }
    throw err;
  }
}
