'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  FileText,
  Trash2,
  RefreshCw,
  Plus,
  AlertCircle,
  CheckCircle,
  Clock,
  Database,
  Sparkles,
  LogOut,
  User as UserIcon,
  ChevronRight,
  Loader2,
  X,
  Edit,
  Eye,
  EyeOff,
  MessageSquare
} from 'lucide-react';
import { useAuthStore, apiRequest, User } from '@/lib/auth';
import { cn } from '@/lib/utils';
import { IdentityCardButton } from '@/components/IdentityCard';

interface DataSource {
  id: string;
  name: string;
  description?: string;
  source_type: string;
  file_name: string;
  file_size: number;
  mime_type?: string;
  status: string;
  use_count: number;
  created_at: string;
  updated_at: string;
}

interface Avatar {
  id: string;
  name: string;
  description?: string;
  status: string;
  sandbox_status: string;
  is_public: boolean;
  created_at: string;
  used_data_source_ids?: string[];
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, token, logout, isAuthenticated } = useAuthStore();
  
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [avatars, setAvatars] = useState<Avatar[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'data' | 'avatars'>('data');
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [editingAvatar, setEditingAvatar] = useState<Avatar | null>(null);

  // 检查登录状态
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
    }
  }, [isAuthenticated, router]);

  // 加载数据
  const loadData = useCallback(async () => {
    if (!token) return;
    
    try {
      const [sourcesData, avatarsData] = await Promise.all([
        apiRequest('/api/v1/user/data'),
        apiRequest('/api/v1/avatars/my/avatars'),
      ]);
      
      setDataSources(sourcesData);
      setAvatars(avatarsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleDeleteDataSource = async (id: string) => {
    if (!confirm('确定要删除这个数据源吗？')) return;
    
    try {
      console.log('Deleting data source:', id);
      await apiRequest(`/api/v1/user/data/${id}`, { method: 'DELETE' });
      setDataSources(prev => prev.filter(ds => ds.id !== id));
      console.log('Data source deleted successfully');
    } catch (error) {
      console.error('Delete error:', error);
      alert(error instanceof Error ? error.message : '删除失败');
    }
  };

  const handleDeleteAvatar = async (id: string) => {
    if (!confirm('确定要永久删除这个分身吗？此操作不可恢复！')) return;
    
    try {
      await apiRequest(`/api/v1/avatars/${id}`, { method: 'DELETE' });
      // 从列表中移除
      setAvatars(prev => prev.filter(a => a.id !== id));
      // 刷新数据
      loadData();
    } catch (error) {
      console.error('Delete error:', error);
      alert(error instanceof Error ? error.message : '删除失败');
    }
  };

  const handleStartChat = async (avatarId: string) => {
    try {
      // 直接跳转到聊天页面并传递avatar参数，让聊天页面创建对话并加载
      router.push(`/chat?avatar=${avatarId}`);
    } catch (error) {
      alert(error instanceof Error ? error.message : '创建对话失败');
    }
  };

  const handleRebuildAvatar = async (id: string) => {
    if (!confirm('确定要重建这个分身吗？这将使用当前的数据重新编织。')) return;
    
    try {
      await apiRequest(`/api/v1/avatars/${id}/rebuild`, { method: 'POST' });
      alert('重建已启动，请稍后查看状态');
      loadData();
    } catch (error) {
      alert(error instanceof Error ? error.message : '重建失败');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <a href="/" className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <span className="font-bold text-xl">Human.online</span>
              </a>
              <div className="h-6 w-px bg-slate-200" />
              <span className="text-slate-600">数据管理中心</span>
            </div>

            <div className="flex items-center gap-4">
              {/* 用户配额 -->
              <div className="px-4 py-2 bg-indigo-50 rounded-lg text-sm">
                <span className="text-slate-600">免费额度: </span>
                <span className="font-semibold text-indigo-600">
                  剩余 {user?.remaining_free_quota || 0} 个
                </span>
                <span className="text-slate-400 text-xs ml-1">
                  (共 {user?.free_avatar_quota || 1} 个)
                </span>
              </div>

              {/* 用户信息 */}
              <div className="flex items-center gap-3">
                {user?.avatar_url ? (
                  <img src={user.avatar_url} alt="" className="w-8 h-8 rounded-full" />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center">
                    <UserIcon className="w-4 h-4 text-slate-500" />
                  </div>
                )}
                <span className="text-sm font-medium">{user?.display_name || user?.email}</span>
              </div>

              <button
                onClick={logout}
                className="p-2 text-slate-400 hover:text-red-600 transition-colors"
                title="退出登录"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Tab Navigation */}
        <div className="flex items-center gap-2 mb-8">
          <button
            onClick={() => setActiveTab('data')}
            className={cn(
              'px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2',
              activeTab === 'data'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-100'
            )}
          >
            <Database className="w-4 h-4" />
            我的数据
            <span className="px-2 py-0.5 bg-white/20 rounded-full text-xs">
              {dataSources.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('avatars')}
            className={cn(
              'px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2',
              activeTab === 'avatars'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-100'
            )}
          >
            <Sparkles className="w-4 h-4" />
            我的分身
            <span className="px-2 py-0.5 bg-white/20 rounded-full text-xs">
              {avatars.length}
            </span>
          </button>
        </div>

        {/* Data Sources Tab */}
        {activeTab === 'data' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">数据源管理</h2>
                <p className="text-slate-600 mt-1">上传和管理用于构建分身的数据</p>
              </div>
              <button
                onClick={() => setUploadModalOpen(true)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                上传数据
              </button>
            </div>

            {dataSources.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
                  <Upload className="w-8 h-8 text-slate-400" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">还没有数据</h3>
                <p className="text-slate-600 mb-6">上传聊天记录、文档等数据来构建你的分身</p>
                <button
                  onClick={() => setUploadModalOpen(true)}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
                >
                  开始上传
                </button>
              </div>
            ) : (
              <div className="grid gap-4">
                {dataSources.map((source) => (
                  <motion.div
                    key={source.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center">
                          <FileText className="w-6 h-6 text-indigo-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-900">{source.name}</h3>
                          <p className="text-sm text-slate-500 mt-1">
                            {source.file_name} · {formatFileSize(source.file_size)}
                          </p>
                          <div className="flex items-center gap-3 mt-2">
                            <span className={cn(
                              'text-xs px-2 py-0.5 rounded-full',
                              source.status === 'completed' && 'bg-green-100 text-green-700',
                              source.status === 'processing' && 'bg-amber-100 text-amber-700',
                              source.status === 'failed' && 'bg-red-100 text-red-700',
                              source.status === 'pending' && 'bg-slate-100 text-slate-600',
                            )}>
                              {source.status === 'completed' && '✓ 已处理'}
                              {source.status === 'processing' && '⏳ 处理中'}
                              {source.status === 'failed' && '✗ 失败'}
                              {source.status === 'pending' && '⏸ 待处理'}
                            </span>
                            {source.use_count > 0 && (
                              <span className="text-xs text-slate-500">
                                已用于 {source.use_count} 个分身
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {source.use_count === 0 && (
                          <button
                            onClick={() => handleDeleteDataSource(source.id)}
                            className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="删除"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}

            {/* Create Avatar CTA */}
            {dataSources.length > 0 && user?.can_create_free_avatar && (
              <div className="mt-8 p-6 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-lg">准备好创建你的分身了吗？</h3>
                    <p className="text-white/80 mt-1">使用已上传的数据免费创建一个数字分身</p>
                  </div>
                  <a
                    href="/avatar/create"
                    className="px-6 py-3 bg-white text-indigo-600 rounded-lg font-medium hover:bg-white/90 transition-colors flex items-center gap-2"
                  >
                    <Sparkles className="w-5 h-5" />
                    创建分身
                  </a>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Avatars Tab */}
        {activeTab === 'avatars' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">我的分身</h2>
                <p className="text-slate-600 mt-1">管理你创建的数字分身</p>
              </div>
              {user?.can_create_free_avatar && (
                <a
                  href="/avatar/create"
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  创建新分身
                </a>
              )}
            </div>

            {avatars.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-8 h-8 text-slate-400" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">还没有分身</h3>
                <p className="text-slate-600 mb-6">创建你的第一个数字分身，它将自动进入沙盘</p>
                <a
                  href="/avatar/create"
                  className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
                >
                  创建分身
                </a>
              </div>
            ) : (
              <div className="grid gap-4">
                {avatars.map((avatar) => (
                  <motion.div
                    key={avatar.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold">
                          {avatar.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-900">{avatar.name}</h3>
                          <p className="text-sm text-slate-500 mt-1">
                            {avatar.description || '无描述'}
                          </p>
                          <div className="flex items-center gap-3 mt-2">
                            <span className={cn(
                              'text-xs px-2 py-0.5 rounded-full',
                              avatar.status === 'ready' && 'bg-green-100 text-green-700',
                              avatar.status === 'weaving' && 'bg-amber-100 text-amber-700',
                              avatar.status === 'draft' && 'bg-slate-100 text-slate-600',
                            )}>
                              {avatar.status === 'ready' && '✓ 就绪'}
                              {avatar.status === 'weaving' && '⏳ 编织中'}
                              {avatar.status === 'draft' && '⏸ 草稿'}
                            </span>
                            {avatar.status === 'weaving' && (
                              <a 
                                href={`/weaving/${avatar.id}`}
                                className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 hover:bg-indigo-200 transition-colors"
                              >
                                查看进度 →
                              </a>
                            )}
                            {avatar.sandbox_status === 'active' && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
                                🌐 沙盒中
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {avatar.status === 'ready' && (
                          <button
                            onClick={() => handleStartChat(avatar.id)}
                            className="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                            title="开始对话"
                          >
                            <MessageSquare className="w-5 h-5" />
                          </button>
                        )}
                        
                        {/* 身份卡按钮 */}
                        <div className="p-2">
                          <IdentityCardButton 
                            avatarId={avatar.id}
                            color="from-indigo-500 to-purple-600"
                            size="sm"
                          />
                        </div>
                        
                        <button
                          onClick={() => setEditingAvatar(avatar)}
                          className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="编辑"
                        >
                          <Edit className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleRebuildAvatar(avatar.id)}
                          className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                          title="重建"
                        >
                          <RefreshCw className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleDeleteAvatar(avatar.id)}
                          className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="删除"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Upload Modal */}
      <UploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onSuccess={loadData}
      />

      {/* Edit Avatar Modal */}
      <EditAvatarModal
        avatar={editingAvatar}
        dataSources={dataSources}
        isOpen={!!editingAvatar}
        onClose={() => setEditingAvatar(null)}
        onSuccess={loadData}
      />
    </div>
  );
}

// Upload Modal Component
function UploadModal({
  isOpen,
  onClose,
  onSuccess,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', name || file.name);
      formData.append('description', description);
      formData.append('source_type', 'document');

      const { token } = useAuthStore.getState();
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const response = await fetch(`${API_URL}/api/v1/user/data/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      onSuccess();
      onClose();
      setFile(null);
      setName('');
      setDescription('');
    } catch (error) {
      alert(error instanceof Error ? error.message : '上传失败');
    } finally {
      setIsUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl max-w-md w-full p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold">上传数据源</h3>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              选择文件
            </label>
            <input
              type="file"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) {
                  setFile(f);
                  if (!name) setName(f.name);
                }
              }}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              required
            />
            <p className="text-xs text-slate-500 mt-1">
              支持 PDF、TXT、Markdown、JSON 等格式
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              名称
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              placeholder="给这个数据起个名字"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              描述（可选）
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              rows={3}
              placeholder="描述这个数据源的内容..."
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-slate-200 rounded-lg font-medium hover:bg-slate-50 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={!file || isUploading}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  上传中...
                </>
              ) : (
                '上传'
              )}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

// Edit Avatar Modal Component
function EditAvatarModal({
  avatar,
  dataSources,
  isOpen,
  onClose,
  onSuccess,
}: {
  avatar: Avatar | null;
  dataSources: DataSource[];
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [selectedDataIds, setSelectedDataIds] = useState<string[]>([]);
  const [isPublic, setIsPublic] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'select' | 'upload' | 'visibility'>('select');
  
  // Upload new data state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState('');
  const [uploadDesc, setUploadDesc] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    if (avatar) {
      setSelectedDataIds(avatar.used_data_source_ids || []);
      setIsPublic(avatar.is_public);
    }
  }, [avatar]);

  if (!isOpen || !avatar) return null;

  const handleUpdateDataSources = async () => {
    if (selectedDataIds.length === 0) {
      alert('请至少选择一个数据源');
      return;
    }

    setIsSaving(true);
    try {
      const formData = new FormData();
      formData.append('data_source_ids', selectedDataIds.join(','));

      const { token } = useAuthStore.getState();
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const response = await fetch(`${API_URL}/api/v1/avatars/${avatar.id}/data-sources`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `更新失败: ${response.status}`);
      }
      
      onSuccess();
      alert('数据源已更新，分身将重新编织');
    } catch (error) {
      console.error('Update data sources error:', error);
      alert(error instanceof Error ? error.message : '更新失败');
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdateVisibility = async () => {
    setIsSaving(true);
    try {
      const formData = new FormData();
      formData.append('is_public', isPublic.toString());

      const { token } = useAuthStore.getState();
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const response = await fetch(`${API_URL}/api/v1/avatars/${avatar.id}/visibility`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (!response.ok) throw new Error('更新失败');
      
      onSuccess();
      alert(isPublic ? '已设为公开，分身将出现在沙盒中' : '已设为私有，分身不会出现在公共区域');
      onClose();
    } catch (error) {
      alert(error instanceof Error ? error.message : '更新失败');
    } finally {
      setIsSaving(false);
    }
  };

  const handleUploadNewData = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setIsUploading(true);
    try {
      const { token } = useAuthStore.getState();
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      // 1. Upload the file
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('name', uploadName || uploadFile.name);
      formData.append('description', uploadDesc);
      formData.append('source_type', 'document');

      const uploadRes = await fetch(`${API_URL}/api/v1/user/data/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (!uploadRes.ok) throw new Error('上传失败');
      
      const newData = await uploadRes.json();
      
      // 2. Add to avatar's data sources
      const newDataIds = [...selectedDataIds, newData.id];
      const updateFormData = new FormData();
      updateFormData.append('data_source_ids', newDataIds.join(','));

      const updateRes = await fetch(`${API_URL}/api/v1/avatars/${avatar.id}/data-sources`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: updateFormData,
      });

      if (!updateRes.ok) throw new Error('更新数据源失败');
      
      // Reset and refresh
      setUploadFile(null);
      setUploadName('');
      setUploadDesc('');
      setSelectedDataIds(newDataIds);
      onSuccess();
      alert('数据上传成功并已添加到分身');
      setActiveTab('select');
    } catch (error) {
      console.error('Upload error:', error);
      alert(error instanceof Error ? error.message : '上传失败');
    } finally {
      setIsUploading(false);
    }
  };

  const toggleDataSelection = (id: string) => {
    setSelectedDataIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold">编辑分身: {avatar.name}</h3>
            <p className="text-sm text-slate-500">管理数据源和公开状态</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('select')}
            className={cn(
              'flex-1 px-4 py-3 text-sm font-medium transition-colors',
              activeTab === 'select' 
                ? 'text-indigo-600 border-b-2 border-indigo-600' 
                : 'text-slate-600 hover:text-slate-900'
            )}
          >
            <Database className="w-4 h-4 inline mr-2" />
            选择数据
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={cn(
              'flex-1 px-4 py-3 text-sm font-medium transition-colors',
              activeTab === 'upload' 
                ? 'text-indigo-600 border-b-2 border-indigo-600' 
                : 'text-slate-600 hover:text-slate-900'
            )}
          >
            <Upload className="w-4 h-4 inline mr-2" />
            上传新数据
          </button>
          <button
            onClick={() => setActiveTab('visibility')}
            className={cn(
              'flex-1 px-4 py-3 text-sm font-medium transition-colors',
              activeTab === 'visibility' 
                ? 'text-indigo-600 border-b-2 border-indigo-600' 
                : 'text-slate-600 hover:text-slate-900'
            )}
          >
            <Eye className="w-4 h-4 inline mr-2" />
            公开状态
          </button>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          {activeTab === 'select' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-slate-600 text-sm">
                  选择用于构建分身的数据源（已选 {selectedDataIds.length} 个）
                </p>
              </div>
              <div className="space-y-2">
                {dataSources.map((source) => (
                  <div
                    key={source.id}
                    onClick={() => toggleDataSelection(source.id)}
                    className={cn(
                      'p-3 rounded-lg border-2 cursor-pointer transition-all',
                      selectedDataIds.includes(source.id)
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-slate-200 hover:border-slate-300'
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        'w-5 h-5 rounded border-2 flex items-center justify-center',
                        selectedDataIds.includes(source.id) ? 'border-indigo-500 bg-indigo-500' : 'border-slate-300'
                      )}>
                        {selectedDataIds.includes(source.id) && <CheckCircle className="w-3 h-3 text-white" />}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-sm">{source.name}</p>
                        <p className="text-xs text-slate-500">{source.file_name}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {dataSources.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-slate-500 mb-4">没有可用的数据源</p>
                  <button
                    onClick={() => setActiveTab('upload')}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm"
                  >
                    去上传数据
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'upload' && (
            <form onSubmit={handleUploadNewData} className="space-y-4">
              <p className="text-slate-600 text-sm">
                上传新数据文件并自动添加到当前分身
              </p>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  选择文件 *
                </label>
                <input
                  type="file"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) {
                      setUploadFile(f);
                      if (!uploadName) setUploadName(f.name);
                    }
                  }}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  required
                />
                <p className="text-xs text-slate-500 mt-1">
                  支持 PDF、TXT、Markdown 等格式
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  名称
                </label>
                <input
                  type="text"
                  value={uploadName}
                  onChange={(e) => setUploadName(e.target.value)}
                  placeholder="给这个数据起个名字"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  描述（可选）
                </label>
                <textarea
                  value={uploadDesc}
                  onChange={(e) => setUploadDesc(e.target.value)}
                  placeholder="描述这个数据的内容..."
                  rows={3}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <button
                type="submit"
                disabled={!uploadFile || isUploading}
                className="w-full py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                {isUploading ? '上传中...' : '上传并添加到分身'}
              </button>
            </form>
          )}

          {activeTab === 'visibility' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => setIsPublic(true)}
                  className={cn(
                    'p-4 rounded-xl border-2 text-left transition-all',
                    isPublic ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200'
                  )}
                >
                  <Eye className="w-6 h-6 text-indigo-600 mb-2" />
                  <p className="font-medium">公开</p>
                  <p className="text-sm text-slate-500 mt-1">
                    分身将出现在沙盒、市场和观察者模式中
                  </p>
                </button>
                <button
                  onClick={() => setIsPublic(false)}
                  className={cn(
                    'p-4 rounded-xl border-2 text-left transition-all',
                    !isPublic ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200'
                  )}
                >
                  <EyeOff className="w-6 h-6 text-slate-600 mb-2" />
                  <p className="font-medium">私有</p>
                  <p className="text-sm text-slate-500 mt-1">
                    只有你自己可以使用，不会出现在公共区域
                  </p>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-slate-200 rounded-lg font-medium hover:bg-slate-50"
          >
            关闭
          </button>
          {activeTab === 'select' && (
            <button
              onClick={handleUpdateDataSources}
              disabled={isSaving}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              更新数据源
            </button>
          )}
          {activeTab === 'visibility' && (
            <button
              onClick={handleUpdateVisibility}
              disabled={isSaving}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              保存设置
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}
