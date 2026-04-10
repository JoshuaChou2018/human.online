'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore, apiRequest } from '@/lib/auth';
import { BackToHome } from '@/components/BackToHome';
import { 
  Loader2, 
  Brain, 
  MessageCircle, 
  GitBranch, 
  BookOpen, 
  Scale, 
  Sparkles,
  FileText,
  Cpu,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  Clock,
  Terminal,
  BarChart3,
  Zap,
  ArrowLeft
} from 'lucide-react';

// 编织阶段定义
const STAGE_CONFIG: Record<string, { title: string; description: string; icon: React.ElementType; color: string }> = {
  preparing: {
    title: '准备阶段',
    description: '读取和准备用户数据源',
    icon: FileText,
    color: 'from-blue-500 to-cyan-500'
  },
  extracting_text: {
    title: '文本提取',
    description: '从上传文件中提取可分析的文本内容',
    icon: FileText,
    color: 'from-blue-500 to-cyan-500'
  },
  analyzing_mind_core: {
    title: '分析思维内核',
    description: '识别核心思维框架和认知偏好',
    icon: Brain,
    color: 'from-purple-500 to-pink-500'
  },
  analyzing_expression: {
    title: '分析表达风格',
    description: '提取语言习惯和表达特征',
    icon: MessageCircle,
    color: 'from-pink-500 to-rose-500'
  },
  analyzing_decision: {
    title: '分析决策逻辑',
    description: '理解决策模式和判断逻辑',
    icon: GitBranch,
    color: 'from-amber-500 to-orange-500'
  },
  analyzing_knowledge: {
    title: '分析知识领域',
    description: '构建个人知识图谱',
    icon: BookOpen,
    color: 'from-emerald-500 to-teal-500'
  },
  analyzing_values: {
    title: '分析价值体系',
    description: '提取核心价值观和原则',
    icon: Scale,
    color: 'from-indigo-500 to-violet-500'
  },
  analyzing_emotion: {
    title: '分析情感模式',
    description: '识别情感表达和响应特征',
    icon: Sparkles,
    color: 'from-rose-500 to-red-500'
  },
  weaving_mind: {
    title: '编织思维内核',
    description: '综合六维线索编织完整思维体',
    icon: Cpu,
    color: 'from-violet-500 to-purple-500'
  },
  generating_identity: {
    title: '生成身份卡',
    description: '创建可视化的身份认证卡',
    icon: CheckCircle2,
    color: 'from-green-500 to-emerald-500'
  },
  completed: {
    title: '编织完成',
    description: '数字分身已准备就绪',
    icon: CheckCircle2,
    color: 'from-green-500 to-emerald-500'
  },
  failed: {
    title: '编织失败',
    description: '过程中发生错误',
    icon: AlertCircle,
    color: 'from-red-500 to-pink-500'
  }
};

// 日志条目类型
interface LogEntry {
  timestamp: string;
  stage: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  metadata?: Record<string, any>;
}

// 进度数据类型
interface WeavingProgress {
  id: string;
  avatar_id: string;
  current_stage: string;
  current_stage_label: string;
  overall_progress: number;
  stage_progress: Record<string, { progress: number; status: string; updated_at: string }>;
  logs: LogEntry[];
  current_text_preview?: string;
  intermediate_results: Record<string, any>;
  llm_stats: {
    calls_count: number;
    tokens_used: number;
    provider: string;
    model: string;
  };
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  is_running: boolean;
  is_completed: boolean;
  is_failed: boolean;
}

export default function WeavingPage() {
  const params = useParams();
  const avatarId = typeof params.avatarId === 'string' ? params.avatarId : Array.isArray(params.avatarId) ? params.avatarId[0] : '';
  const router = useRouter();
  const { token, user } = useAuthStore();
  
  const [progress, setProgress] = useState<WeavingProgress | null>(null);
  const [avatar, setAvatar] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'logs' | 'analysis'>('overview');
  const [elapsedTime, setElapsedTime] = useState(0);
  
  const wsRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  
  // 获取 API 基础 URL
  const getApiBaseUrl = () => {
    if (typeof window === 'undefined') return 'http://localhost:8000';
    const host = window.location.hostname;
    return host === 'localhost' ? 'http://localhost:8000' : `http://${host}:8000`;
  };
  
  // 获取 WebSocket URL
  const getWsUrl = () => {
    const apiBase = getApiBaseUrl();
    const wsProtocol = apiBase.startsWith('https') ? 'wss' : 'ws';
    return apiBase.replace(/^http/, wsProtocol);
  };
  
  // 获取分身信息和进度
  useEffect(() => {
    const fetchData = async () => {
      try {
        // 获取分身信息
        const avatarRes = await apiRequest(`/avatars/${avatarId}`);
        setAvatar(avatarRes);
        
        // 获取详细进度
        const progressRes = await apiRequest(`/avatars/${avatarId}/status?detailed=true`);
        if (progressRes.detailed_progress) {
          setProgress(progressRes.detailed_progress);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取数据失败');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [avatarId]);
  
  // WebSocket 连接
  useEffect(() => {
    if (!token || !avatarId) return;
    
    const connectWebSocket = () => {
      const wsUrl = `${getWsUrl()}/ws/weaving/${avatarId}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('[WebSocket] Connected to weaving progress');
        // 发送认证
        ws.send(JSON.stringify({ token }));
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'weaving_progress') {
          setProgress(data);
        } else if (data.type === 'error') {
          console.error('[WebSocket] Error:', data.message);
        }
      };
      
      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
      };
      
      ws.onclose = () => {
        console.log('[WebSocket] Disconnected');
        // 如果编织还在进行中，尝试重连
        if (progress?.is_running) {
          setTimeout(connectWebSocket, 3000);
        }
      };
      
      wsRef.current = ws;
    };
    
    connectWebSocket();
    
    return () => {
      wsRef.current?.close();
    };
  }, [token, avatarId, progress?.is_running]);
  
  // 计时器
  useEffect(() => {
    if (!progress?.is_running) return;
    
    const interval = setInterval(() => {
      if (progress?.started_at) {
        const start = new Date(progress.started_at).getTime();
        const now = Date.now();
        setElapsedTime(Math.floor((now - start) / 1000));
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [progress?.is_running, progress?.started_at]);
  
  // 自动滚动到日志底部
  useEffect(() => {
    if (activeTab === 'logs' && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [progress?.logs, activeTab]);
  
  // 格式化时间
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  // 获取当前阶段配置
  const getCurrentStageConfig = () => {
    const stage = progress?.current_stage || 'preparing';
    return STAGE_CONFIG[stage] || STAGE_CONFIG.preparing;
  };
  
  // 获取日志颜色
  const getLogTypeColor = (type: string) => {
    switch (type) {
      case 'success': return 'text-green-400';
      case 'warning': return 'text-amber-400';
      case 'error': return 'text-red-400';
      default: return 'text-slate-400';
    }
  };
  
  // 获取日志图标
  const getLogTypeIcon = (type: string) => {
    switch (type) {
      case 'success': return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'warning': return <AlertCircle className="w-4 h-4 text-amber-400" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-400" />;
      default: return <Terminal className="w-4 h-4 text-slate-400" />;
    }
  };
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-500">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span>加载中...</span>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-800 mb-2">出现问题</h2>
          <p className="text-slate-500 mb-6">{error}</p>
          <button
            onClick={() => router.back()}
            className="px-6 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition-colors"
          >
            返回
          </button>
        </div>
      </div>
    );
  }
  
  const stageConfig = getCurrentStageConfig();
  const StageIcon = stageConfig.icon;
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <BackToHome />
      {/* 头部 */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-slate-600" />
              </button>
              <div>
                <h1 className="text-xl font-semibold text-slate-800">
                  MindWeave 编织工厂
                </h1>
                <p className="text-sm text-slate-500">
                  正在为 <span className="font-medium text-slate-700">{avatar?.name}</span> 编织数字分身
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {/* 计时器 */}
              <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 rounded-lg">
                <Clock className="w-4 h-4 text-slate-400" />
                <span className="text-sm font-medium text-slate-600">
                  {formatDuration(elapsedTime)}
                </span>
              </div>
              
              {/* 状态标识 */}
              {progress?.is_completed ? (
                <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                  完成
                </span>
              ) : progress?.is_failed ? (
                <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
                  失败
                </span>
              ) : (
                <span className="flex items-center gap-2 px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  编织中
                </span>
              )}
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* 总体进度 */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${stageConfig.color} flex items-center justify-center text-white shadow-lg`}>
                <StageIcon className="w-7 h-7" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-800">{stageConfig.title}</h2>
                <p className="text-slate-500">{stageConfig.description}</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-3xl font-bold text-slate-800">{progress?.overall_progress || 0}%</span>
              <p className="text-sm text-slate-400">总体进度</p>
            </div>
          </div>
          
          {/* 进度条 */}
          <div className="relative h-3 bg-slate-100 rounded-full overflow-hidden">
            <motion.div
              className={`absolute inset-y-0 left-0 bg-gradient-to-r ${stageConfig.color} rounded-full`}
              initial={{ width: 0 }}
              animate={{ width: `${progress?.overall_progress || 0}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          </div>
          
          {/* 阶段指示器 */}
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100">
            {Object.entries(STAGE_CONFIG)
              .filter(([key]) => !['completed', 'failed'].includes(key))
              .map(([key, config], index) => {
                const isActive = progress?.current_stage === key;
                const isCompleted = progress?.stage_progress?.[key]?.status === 'completed';
                const stageProgress = progress?.stage_progress?.[key]?.progress || 0;
                
                return (
                  <div key={key} className="flex flex-col items-center gap-2 flex-1">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-all ${
                      isCompleted 
                        ? 'bg-green-500 text-white' 
                        : isActive 
                          ? 'bg-indigo-500 text-white ring-4 ring-indigo-100' 
                          : 'bg-slate-100 text-slate-400'
                    }`}>
                      {isCompleted ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : (
                        index + 1
                      )}
                    </div>
                    {isActive && (
                      <motion.div
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap"
                      >
                        <span className="text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
                          {stageProgress}%
                        </span>
                      </motion.div>
                    )}
                  </div>
                );
              })}
          </div>
        </div>
        
        {/* 主内容区 */}
        <div className="grid grid-cols-3 gap-6">
          {/* 左侧 - 标签页 */}
          <div className="col-span-2 space-y-6">
            {/* 标签选择 */}
            <div className="flex items-center gap-2 bg-white rounded-xl p-1 border border-slate-200">
              {[
                { key: 'overview', label: '概览', icon: BarChart3 },
                { key: 'logs', label: '实时日志', icon: Terminal },
                { key: 'analysis', label: '分析结果', icon: Brain }
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key as any)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all flex-1 justify-center ${
                    activeTab === key
                      ? 'bg-slate-800 text-white'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </button>
              ))}
            </div>
            
            {/* 标签内容 */}
            <AnimatePresence mode="wait">
              {activeTab === 'overview' && (
                <motion.div
                  key="overview"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  {/* 当前分析内容预览 */}
                  {progress?.current_text_preview && (
                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                      <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        当前分析内容预览
                      </h3>
                      <div className="bg-slate-50 rounded-xl p-4 max-h-48 overflow-y-auto">
                        <p className="text-sm text-slate-600 whitespace-pre-wrap font-mono leading-relaxed">
                          {progress.current_text_preview}
                        </p>
                      </div>
                    </div>
                  )}
                  
                  {/* 六维分析状态 */}
                  <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                    <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
                      <Brain className="w-4 h-4" />
                      MindWeave 六维分析进度
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      {[
                        { key: 'analyzing_mind_core', label: '思维内核', icon: Brain },
                        { key: 'analyzing_expression', label: '表达风格', icon: MessageCircle },
                        { key: 'analyzing_decision', label: '决策逻辑', icon: GitBranch },
                        { key: 'analyzing_knowledge', label: '知识领域', icon: BookOpen },
                        { key: 'analyzing_values', label: '价值体系', icon: Scale },
                        { key: 'analyzing_emotion', label: '情感模式', icon: Sparkles }
                      ].map(({ key, label, icon: Icon }) => {
                        const stageData = progress?.stage_progress?.[key];
                        const isCompleted = stageData?.status === 'completed';
                        const stageProgress = stageData?.progress || 0;
                        
                        return (
                          <div key={key} className={`p-4 rounded-xl border transition-all ${
                            isCompleted 
                              ? 'bg-green-50 border-green-200' 
                              : stageProgress > 0 
                                ? 'bg-indigo-50 border-indigo-200' 
                                : 'bg-slate-50 border-slate-200'
                          }`}>
                            <div className="flex items-center gap-3 mb-2">
                              <Icon className={`w-5 h-5 ${
                                isCompleted ? 'text-green-600' : stageProgress > 0 ? 'text-indigo-600' : 'text-slate-400'
                              }`} />
                              <span className={`text-sm font-medium ${
                                isCompleted ? 'text-green-700' : stageProgress > 0 ? 'text-indigo-700' : 'text-slate-600'
                              }`}>
                                {label}
                              </span>
                              {isCompleted && <CheckCircle2 className="w-4 h-4 text-green-500 ml-auto" />}
                            </div>
                            <div className="h-1.5 bg-white rounded-full overflow-hidden">
                              <div 
                                className={`h-full rounded-full transition-all duration-500 ${
                                  isCompleted ? 'bg-green-500' : 'bg-indigo-500'
                                }`}
                                style={{ width: `${isCompleted ? 100 : stageProgress}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </motion.div>
              )}
              
              {activeTab === 'logs' && (
                <motion.div
                  key="logs"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-slate-900 rounded-2xl shadow-sm border border-slate-800 overflow-hidden"
                >
                  <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                      <Terminal className="w-4 h-4" />
                      实时日志
                    </h3>
                    <span className="text-xs text-slate-500">
                      {progress?.logs?.length || 0} 条记录
                    </span>
                  </div>
                  <div className="p-4 h-96 overflow-y-auto font-mono text-sm space-y-2">
                    {progress?.logs?.map((log, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-start gap-3"
                      >
                        <span className="text-slate-600 text-xs whitespace-nowrap">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        {getLogTypeIcon(log.type)}
                        <span className={getLogTypeColor(log.type)}>
                          {log.message}
                        </span>
                      </motion.div>
                    ))}
                    <div ref={logsEndRef} />
                  </div>
                </motion.div>
              )}
              
              {activeTab === 'analysis' && (
                <motion.div
                  key="analysis"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  {Object.entries(progress?.intermediate_results || {}).map(([stage, result]) => (
                    <div key={stage} className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                      <h3 className="text-sm font-semibold text-slate-700 mb-4 capitalize">
                        {STAGE_CONFIG[stage]?.title || stage}
                      </h3>
                      <div className="bg-slate-50 rounded-xl p-4 overflow-x-auto">
                        <pre className="text-xs text-slate-600 font-mono">
                          {JSON.stringify(result, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ))}
                  
                  {Object.keys(progress?.intermediate_results || {}).length === 0 && (
                    <div className="text-center py-12 text-slate-400">
                      <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>暂无分析结果</p>
                      <p className="text-sm">等待 LLM 分析完成后将显示在此</p>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          
          {/* 右侧 - LLM 统计和操作 */}
          <div className="space-y-6">
            {/* LLM 统计 */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                LLM 调用统计
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">提供商</span>
                  <span className="text-sm font-medium text-slate-700">
                    {progress?.llm_stats?.provider || '-'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">模型</span>
                  <span className="text-sm font-medium text-slate-700">
                    {progress?.llm_stats?.model || '-'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">调用次数</span>
                  <span className="text-sm font-medium text-slate-700">
                    {progress?.llm_stats?.calls_count || 0}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">Token 使用量</span>
                  <span className="text-sm font-medium text-slate-700">
                    {(progress?.llm_stats?.tokens_used || 0).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
            
            {/* 操作按钮 */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-4">操作
              </h3>
              <div className="space-y-3">
                {progress?.is_completed ? (
                  <button
                    onClick={() => router.push(`/dashboard`)}
                    className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-medium hover:from-green-600 hover:to-emerald-600 transition-all flex items-center justify-center gap-2"
                  >
                    <CheckCircle2 className="w-5 h-5" />
                    查看分身
                  </button>
                ) : progress?.is_failed ? (
                  <button
                    onClick={() => window.location.reload()}
                    className="w-full py-3 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-xl font-medium hover:from-red-600 hover:to-pink-600 transition-all flex items-center justify-center gap-2"
                  >
                    <AlertCircle className="w-5 h-5" />
                    重试
                  </button>
                ) : (
                  <button
                    onClick={() => router.push('/dashboard')}
                    className="w-full py-3 bg-slate-100 text-slate-600 rounded-xl font-medium hover:bg-slate-200 transition-all"
                  >
                    后台运行
                  </button>
                )}
                
                <button
                  onClick={() => router.push('/dashboard')}
                  className="w-full py-3 border border-slate-200 text-slate-600 rounded-xl font-medium hover:bg-slate-50 transition-all"
                >
                  返回仪表盘
                </button>
              </div>
            </div>
            
            {/* MindWeave 说明 */}
            <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100 p-6">
              <h3 className="text-sm font-semibold text-indigo-900 mb-3">
                关于 MindWeave
              </h3>
              <p className="text-sm text-indigo-700 leading-relaxed mb-4">
                MindWeave 是一种基于认知科学的数字分身编织理论，通过分析六个维度的思维特征来构建真实的数字 psyche。
              </p>
              <div className="space-y-2">
                {[
                  { label: '思维内核', desc: '核心认知模式' },
                  { label: '表达风格', desc: '语言习惯特征' },
                  { label: '决策逻辑', desc: '判断与选择模式' },
                  { label: '知识领域', desc: '专业知识图谱' },
                  { label: '价值体系', desc: '核心价值观' },
                  { label: '情感模式', desc: '情感表达特征' }
                ].map(({ label, desc }) => (
                  <div key={label} className="flex items-center gap-3 text-sm">
                    <ChevronRight className="w-4 h-4 text-indigo-400" />
                    <span className="font-medium text-indigo-800">{label}</span>
                    <span className="text-indigo-600">- {desc}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
