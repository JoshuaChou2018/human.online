'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { BackToHome } from '@/components/BackToHome';
import { 
  Upload, 
  FileText, 
  Sparkles,
  ArrowRight,
  Check,
  Loader2,
  Database,
  Plus,
  X,
  AlertCircle,
  ChevronRight,
  User,
  Eye,
  Lock,
  FileEdit,
  MessageSquare,
  Lightbulb
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore, apiRequest } from '@/lib/auth';

type Step = 'select-data' | 'processing' | 'complete';
type CreationMethod = 'data' | 'text';

interface DataSource {
  id: string;
  name: string;
  source_type: string;
  file_name: string;
  file_size: number;
  status: string;
}

export default function CreateAvatarPage() {
  const router = useRouter();
  const { user, isAuthenticated, checkAuth } = useAuthStore();
  
  const [currentStep, setCurrentStep] = useState<Step>('select-data');
  const [creationMethod, setCreationMethod] = useState<CreationMethod>('data');
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [selectedDataIds, setSelectedDataIds] = useState<string[]>([]);
  const [avatarName, setAvatarName] = useState('');
  const [avatarDescription, setAvatarDescription] = useState('');
  const [textPrompt, setTextPrompt] = useState('');
  const [isPublic, setIsPublic] = useState(true); // 默认公开
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [createdAvatarId, setCreatedAvatarId] = useState<string | null>(null);

  // 检查登录状态
  useEffect(() => {
    const init = async () => {
      const isAuth = await checkAuth();
      if (!isAuth) {
        router.push('/auth/login?redirect=/avatar/create');
        return;
      }
      loadDataSources();
    };
    init();
  }, [checkAuth, router]);

  const loadDataSources = useCallback(async () => {
    try {
      const data = await apiRequest('/user/data');
      // 只显示已处理完成的数据
      const completed = data.filter((ds: DataSource) => ds.status === 'completed');
      setDataSources(completed);
    } catch (err) {
      setError('加载数据源失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleCreateAvatar = async () => {
    if (!avatarName.trim()) {
      setError('请输入分身名称');
      return;
    }

    // 根据创建方式验证
    if (creationMethod === 'data') {
      if (selectedDataIds.length === 0) {
        setError('请至少选择一个数据源');
        return;
      }
    } else {
      if (!textPrompt.trim() || textPrompt.length < 10) {
        setError('请输入至少10个字符的描述');
        return;
      }
    }

    setIsCreating(true);
    setError(null);

    try {
      const { token } = useAuthStore.getState();

      let response;
      
      if (creationMethod === 'data') {
        // 从数据源创建
        const formData = new FormData();
        formData.append('name', avatarName);
        formData.append('description', avatarDescription);
        formData.append('data_source_ids', selectedDataIds.join(','));
        formData.append('is_public', isPublic.toString());

        response = await fetch('/api/v1/avatars/from-data', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        });
      } else {
        // 从文本描述创建
        const formData = new FormData();
        formData.append('name', avatarName);
        formData.append('description', textPrompt);
        formData.append('is_public', isPublic.toString());

        response = await fetch('/api/v1/avatars/from-description', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        });
      }

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '创建失败');
      }

      const avatar = await response.json();
      setCreatedAvatarId(avatar.id);
      
      // 跳转到编织进度详情页面
      router.push(`/weaving/${avatar.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败');
    } finally {
      setIsCreating(false);
    }
  };

  const toggleDataSelection = (id: string) => {
    setSelectedDataIds(prev => 
      prev.includes(id) 
        ? prev.filter(i => i !== id)
        : [...prev, id]
    );
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
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

  // 如果没有可用的数据源且选择了数据创建方式，显示提示引导用户使用文本方式
  if (dataSources.length === 0 && !isLoading && creationMethod === 'data') {
    return (
      <div className="min-h-screen bg-slate-50">
        <header className="bg-white border-b sticky top-0 z-10">
          <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-lg">编织数字分身</span>
            </div>
            <a href="/" className="text-slate-500 hover:text-slate-900">返回首页</a>
          </div>
        </header>

        <main className="max-w-2xl mx-auto px-6 py-20 text-center">
          <div className="w-20 h-20 rounded-full bg-amber-50 flex items-center justify-center mx-auto mb-6">
            <Database className="w-10 h-10 text-amber-500" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-4">先上传一些数据</h2>
          <p className="text-slate-600 mb-8">
            创建分身需要使用你的数据来编织思维特征。<br/>
            请先上传聊天记录、文档等数据，或者使用"一句话创建"方式。
          </p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => setCreationMethod('text')}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors flex items-center gap-2"
            >
              <FileEdit className="w-5 h-5" />
              一句话创建
            </button>
            <a
              href="/dashboard"
              className="px-6 py-3 border border-slate-200 rounded-lg font-medium hover:bg-slate-50 transition-colors"
            >
              去上传数据
            </a>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <BackToHome />
      {/* 头部 */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg">编织数字分身</span>
          </div>
          
          {/* 步骤指示器 */}
          <div className="flex items-center gap-2">
            {[
              { id: 'select-data', label: '选择数据' },
              { id: 'processing', label: '思维编织' },
              { id: 'complete', label: '完成' },
            ].map((step, index) => {
              const stepIndex = ['select-data', 'processing', 'complete'].indexOf(currentStep);
              const isActive = index <= stepIndex;
              const isCurrent = index === stepIndex;
              
              return (
                <div key={step.id} className="flex items-center">
                  <div className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-colors',
                    isCurrent ? 'bg-indigo-600 text-white' : 
                    isActive ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-200 text-slate-500'
                  )}>
                    {isActive ? <Check className="w-4 h-4" /> : index + 1}
                  </div>
                  {index < 2 && (
                    <div className={cn(
                      'w-8 h-0.5 mx-1',
                      isActive ? 'bg-indigo-600' : 'bg-slate-200'
                    )} />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {currentStep === 'select-data' && (
            <motion.div
              key="select-data"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* 用户配额信息 */}
              <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                    <User className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">免费创建额度</p>
                    <p className="text-sm text-slate-600">
                      剩余 {user?.remaining_free_quota || 0} 个免费分身额度
                    </p>
                  </div>
                </div>
                {user && !user.can_create_free_avatar && (
                  <span className="text-amber-600 text-sm font-medium">
                    额度已用完
                  </span>
                )}
              </div>

              {/* 错误提示 */}
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  {error}
                </div>
              )}

              {/* 分身信息 */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6">
                <h2 className="text-lg font-semibold mb-4">分身信息</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      名称 *
                    </label>
                    <input
                      type="text"
                      value={avatarName}
                      onChange={(e) => setAvatarName(e.target.value)}
                      placeholder="给你的分身起个名字"
                      className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      描述（可选）
                    </label>
                    <textarea
                      value={avatarDescription}
                      onChange={(e) => setAvatarDescription(e.target.value)}
                      placeholder="描述这个分身的特点..."
                      rows={3}
                      className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                    />
                  </div>
                  
                  {/* 公开/私有选择 */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-3">
                      可见性设置
                    </label>
                    <div className="grid grid-cols-2 gap-4">
                      <button
                        type="button"
                        onClick={() => setIsPublic(true)}
                        className={cn(
                          'p-4 rounded-xl border-2 text-left transition-all',
                          isPublic
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-slate-200 hover:border-slate-300'
                        )}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <div className={cn(
                            'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                            isPublic ? 'border-indigo-500' : 'border-slate-300'
                          )}>
                            {isPublic && <div className="w-2.5 h-2.5 rounded-full bg-indigo-500" />}
                          </div>
                          <span className="font-medium">公开</span>
                        </div>
                        <p className="text-sm text-slate-500">
                          分身将出现在沙盒、市场和观察者模式中，其他用户可以与你互动
                        </p>
                      </button>
                      
                      <button
                        type="button"
                        onClick={() => setIsPublic(false)}
                        className={cn(
                          'p-4 rounded-xl border-2 text-left transition-all',
                          !isPublic
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-slate-200 hover:border-slate-300'
                        )}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <div className={cn(
                            'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                            !isPublic ? 'border-indigo-500' : 'border-slate-300'
                          )}>
                            {!isPublic && <div className="w-2.5 h-2.5 rounded-full bg-indigo-500" />}
                          </div>
                          <span className="font-medium">私有</span>
                        </div>
                        <p className="text-sm text-slate-500">
                          只有你自己可以使用这个分身，不会出现在公共区域
                        </p>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* 创建方式选择 */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6">
                <h2 className="text-lg font-semibold mb-4">选择创建方式</h2>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    type="button"
                    onClick={() => setCreationMethod('data')}
                    className={cn(
                      'p-5 rounded-xl border-2 text-left transition-all',
                      creationMethod === 'data'
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-slate-200 hover:border-slate-300'
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <div className={cn(
                        'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
                        creationMethod === 'data' ? 'bg-indigo-500 text-white' : 'bg-slate-100 text-slate-500'
                      )}>
                        <Database className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-medium text-slate-900 mb-1">从数据创建</h3>
                        <p className="text-sm text-slate-500">
                          上传聊天记录、文档等数据，AI 分析后编织成你的分身
                        </p>
                      </div>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => setCreationMethod('text')}
                    className={cn(
                      'p-5 rounded-xl border-2 text-left transition-all',
                      creationMethod === 'text'
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-slate-200 hover:border-slate-300'
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <div className={cn(
                        'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
                        creationMethod === 'text' ? 'bg-indigo-500 text-white' : 'bg-slate-100 text-slate-500'
                      )}>
                        <FileEdit className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-medium text-slate-900 mb-1">一句话创建</h3>
                        <p className="text-sm text-slate-500">
                          不想上传数据？用文字描述你想创建什么样的分身
                        </p>
                      </div>
                    </div>
                  </button>
                </div>
              </div>

              {/* 根据创建方式显示不同内容 */}
              {creationMethod === 'data' ? (
                /* 数据源选择 */
                <div className="bg-white rounded-2xl border border-slate-200 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold">选择数据源</h2>
                    <button
                      onClick={() => setUploadModalOpen(true)}
                      className="text-sm text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
                    >
                      <Plus className="w-4 h-4" />
                      上传新数据
                    </button>
                  </div>
                  <p className="text-slate-600 text-sm mb-4">
                    选择用于编织分身的数据源（至少选择一个）
                  </p>

                  {dataSources.length === 0 ? (
                    <div className="text-center py-8 bg-slate-50 rounded-xl">
                      <Database className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                      <p className="text-slate-500 text-sm mb-3">还没有可用的数据源</p>
                      <button
                        onClick={() => setUploadModalOpen(true)}
                        className="text-indigo-600 text-sm font-medium hover:text-indigo-700"
                      >
                        立即上传
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="space-y-3">
                        {dataSources.map((source) => (
                          <div
                            key={source.id}
                            onClick={() => toggleDataSelection(source.id)}
                            className={cn(
                              'p-4 rounded-xl border-2 cursor-pointer transition-all',
                              selectedDataIds.includes(source.id)
                                ? 'border-indigo-500 bg-indigo-50'
                                : 'border-slate-200 hover:border-slate-300'
                            )}
                          >
                            <div className="flex items-center gap-4">
                              <div className={cn(
                                'w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors',
                                selectedDataIds.includes(source.id)
                                  ? 'border-indigo-500 bg-indigo-500'
                                  : 'border-slate-300'
                              )}>
                                {selectedDataIds.includes(source.id) && (
                                  <Check className="w-4 h-4 text-white" />
                                )}
                              </div>
                              <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                                <FileText className="w-5 h-5 text-indigo-600" />
                              </div>
                              <div className="flex-1">
                                <h3 className="font-medium text-slate-900">{source.name}</h3>
                                <p className="text-sm text-slate-500">
                                  {source.file_name} · {formatFileSize(source.file_size)}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {selectedDataIds.length > 0 && (
                        <div className="mt-4 p-3 bg-indigo-50 rounded-lg text-sm text-indigo-700">
                          已选择 {selectedDataIds.length} 个数据源
                        </div>
                      )}
                    </>
                  )}
                </div>
              ) : (
                /* 文本描述创建 */
                <div className="bg-white rounded-2xl border border-slate-200 p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Lightbulb className="w-5 h-5 text-amber-500" />
                    <h2 className="text-lg font-semibold">描述你的分身</h2>
                  </div>
                  <p className="text-slate-600 text-sm mb-4">
                    用文字详细描述你想创建的分身，AI 会据此生成完整的分身配置
                  </p>

                  <div className="space-y-4">
                    <textarea
                      value={textPrompt}
                      onChange={(e) => setTextPrompt(e.target.value)}
                      placeholder={"例如：\n" +
                        "• 创建一个像乔布斯一样追求完美、有现实扭曲力场的科技领袖\n" +
                        "• 我想创建一个温柔、善解人意的心理咨询师分身\n" +
                        "• 创建一个精通中国历史、说话文绉绉的学者，喜欢引用古诗词\n" +
                        "• 创建一个幽默风趣、喜欢讲段子的喜剧演员分身"}
                      rows={6}
                      className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all resize-none"
                    />
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500">
                        建议至少 50 字，描述越详细，分身越真实
                      </span>
                      <span className={cn(
                        'font-medium',
                        textPrompt.length < 10 ? 'text-red-500' : 'text-slate-400'
                      )}>
                        {textPrompt.length} / 2000
                      </span>
                    </div>
                  </div>

                  {/* 示例提示 */}
                  <div className="mt-4 p-4 bg-slate-50 rounded-xl">
                    <p className="text-xs text-slate-500 font-medium mb-2">💡 提示技巧</p>
                    <ul className="text-xs text-slate-500 space-y-1">
                      <li>• 描述性格特点（如：幽默、严肃、温和等）</li>
                      <li>• 说明说话风格（如：喜欢引用名言、善用比喻等）</li>
                      <li>• 提及专业领域或知识背景</li>
                      <li>• 描述价值观或处事原则</li>
                    </ul>
                  </div>
                </div>
              )}

              {/* 创建按钮 */}
              <button
                onClick={handleCreateAvatar}
                disabled={isCreating || !user?.can_create_free_avatar}
                className="w-full py-4 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isCreating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    创建中...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    开始思维编织
                  </>
                )}
              </button>
            </motion.div>
          )}

          {currentStep === 'processing' && (
            <motion.div
              key="processing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-20"
            >
              <div className="w-24 h-24 rounded-full bg-indigo-50 flex items-center justify-center mx-auto mb-8">
                <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-4">正在编织你的分身</h2>
              <p className="text-slate-600 max-w-md mx-auto">
                AI 正在分析你提供的数据，提取六维思维线索，编织成独特的数字分身...
              </p>
              <div className="mt-8 max-w-md mx-auto">
                <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-600 rounded-full animate-pulse w-3/4" />
                </div>
                <p className="text-sm text-slate-500 mt-2">这可能需要几分钟时间</p>
              </div>
            </motion.div>
          )}

          {currentStep === 'complete' && (
            <motion.div
              key="complete"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center py-20"
            >
              <div className="w-24 h-24 rounded-full bg-green-50 flex items-center justify-center mx-auto mb-8">
                <Check className="w-12 h-12 text-green-500" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-4">分身创建成功！</h2>
              <p className="text-slate-600 max-w-md mx-auto mb-4">
                你的数字分身 <strong>{avatarName}</strong> 已经编织完成
                {isPublic ? '，并已自动加入沙盒开始与其他分身互动。' : '。'}
              </p>
              {isPublic && (
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-700 rounded-lg text-sm mb-8">
                  <Eye className="w-4 h-4" />
                  公开分身 - 可在沙盒、市场和观察者模式中看到
                </div>
              )}
              {!isPublic && (
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-600 rounded-lg text-sm mb-8">
                  <Lock className="w-4 h-4" />
                  私有分身 - 仅你自己可以使用
                </div>
              )}
              <div className="flex gap-4 justify-center">
                <button
                  onClick={() => router.push(`/chat?avatar=${createdAvatarId}`)}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors flex items-center gap-2"
                >
                  <User className="w-5 h-5" />
                  开始对话
                </button>
                {isPublic && (
                  <button
                    onClick={() => router.push('/observer')}
                    className="px-6 py-3 border border-slate-200 rounded-lg font-medium hover:bg-slate-50 transition-colors flex items-center gap-2"
                  >
                    <Eye className="w-5 h-5" />
                    观察沙盒
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <UploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onSuccess={() => {
          loadDataSources();
          setUploadModalOpen(false);
        }}
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

      const response = await fetch('/api/v1/user/data/upload', {
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
