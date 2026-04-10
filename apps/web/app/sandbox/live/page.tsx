'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  Pause,
  ArrowLeft,
  Users,
  MessageSquare,
  Brain,
  Network,
  TrendingUp,
  Sparkles,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/lib/auth';

interface Avatar {
  id: string;
  name: string;
  color: string;
}

interface Activity {
  id: string;
  avatar_id: string;
  avatar_name: string;
  action: 'speaking' | 'thinking' | 'reacting';
  content: string;
  emotion: 'positive' | 'neutral' | 'negative' | 'excited';
  topic: string;
  round: number;
}

interface Relation {
  from: string;
  from_name: string;
  to: string;
  to_name: string;
  relation: 'agree' | 'disagree' | 'curious' | 'neutral';
  strength: number;
}

interface StreamEvent {
  type: string;
  simulation_id: string;
  data: any;
  timestamp: string;
}

export default function LiveSandboxPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isRunning, setIsRunning] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [avatars, setAvatars] = useState<Avatar[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [relations, setRelations] = useState<Relation[]>([]);
  const [currentTopic, setCurrentTopic] = useState('日常闲聊');
  const [currentRound, setCurrentRound] = useState(0);
  const [maxRounds, setMaxRounds] = useState(5);
  const [thinkingLogs, setThinkingLogs] = useState<Record<string, string[]>>({});
  const abortControllerRef = useRef<AbortController | null>(null);
  const activityEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    activityEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activities]);

  const startSimulation = useCallback(async () => {
    if (!isAuthenticated) {
      router.push('/auth/login?redirect=/sandbox/live');
      return;
    }

    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // 重置状态
    setActivities([]);
    setRelations([]);
    setAvatars([]);
    setThinkingLogs({});
    setCurrentRound(0);
    setIsRunning(true);
    setIsConnected(false);
    setError(null);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const token = localStorage.getItem('auth-storage');
      let authToken = '';
      if (token) {
        try {
          const { state } = JSON.parse(token);
          authToken = state?.token || '';
        } catch {}
      }

      // 使用 EventSource 进行流式读取
      console.log('Starting EventSource connection...');
      
      const eventSourceUrl = `/api/v1/sandbox/stream?topic=${encodeURIComponent(currentTopic)}&max_rounds=${maxRounds}&token=${encodeURIComponent(authToken)}`;
      
      // 关闭之前的 EventSource
      if ((window as any).sandboxEventSource) {
        (window as any).sandboxEventSource.close();
      }
      
      // 创建新的 EventSource
      const es = new EventSource(eventSourceUrl);
      (window as any).sandboxEventSource = es;
      
      es.onopen = () => {
        console.log('EventSource connected');
        setIsConnected(true);
      };
      
      es.onmessage = (e) => {
        try {
          const event: StreamEvent = JSON.parse(e.data);
          console.log('Received event:', event.type);
          handleEvent(event);
          
          if (event.type === 'complete' || event.type === 'error') {
            es.close();
            setIsRunning(false);
            setIsConnected(false);
          }
        } catch (err) {
          console.error('Failed to parse event:', e.data, err);
        }
      };
      
      es.onerror = (err) => {
        console.error('EventSource error:', err);
        setError('连接出错，请重试');
        setIsRunning(false);
        setIsConnected(false);
        es.close();
      };
      
      // 等待 EventSource 完成
      await new Promise<void>((resolve) => {
        const checkClosed = setInterval(() => {
          if (es.readyState === EventSource.CLOSED) {
            clearInterval(checkClosed);
            resolve();
          }
        }, 100);
        
        // 超时处理
        setTimeout(() => {
          clearInterval(checkClosed);
          es.close();
          resolve();
        }, maxRounds * 30000); // 每轮最多30秒
      });
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error('Connection error:', err);
        setError(err.message || '连接失败');
      }
    } finally {
      setIsRunning(false);
      setIsConnected(false);
    }
  }, [currentTopic, maxRounds, isAuthenticated, router]);

  const handleEvent = (event: StreamEvent) => {
    console.log('Handling event:', event.type, event.data);
    switch (event.type) {
      case 'start':
        console.log('Start event received, avatars:', event.data.avatars);
        setAvatars(event.data.avatars);
        break;
        
      case 'thinking':
        setThinkingLogs(prev => ({
          ...prev,
          [event.data.avatar_id]: [
            ...(prev[event.data.avatar_id] || []),
            event.data.thinking
          ]
        }));
        break;
        
      case 'message':
        const newActivity: Activity = {
          id: `${Date.now()}_${Math.random()}`,
          avatar_id: event.data.avatar_id,
          avatar_name: event.data.avatar_name,
          action: event.data.action,
          content: event.data.content,
          emotion: event.data.emotion,
          topic: event.data.topic,
          round: event.data.round
        };
        setActivities(prev => [...prev, newActivity]);
        break;
        
      case 'relation_update':
        const newRelation: Relation = {
          from: event.data.from,
          from_name: event.data.from_name,
          to: event.data.to,
          to_name: event.data.to_name,
          relation: event.data.relation,
          strength: event.data.strength
        };
        setRelations(prev => [...prev, newRelation]);
        break;
        
      case 'topic_change':
        setCurrentTopic(event.data.to);
        break;
        
      case 'round_end':
        setCurrentRound(event.data.round);
        break;
        
      case 'complete':
        setIsRunning(false);
        setIsConnected(false);
        break;
        
      case 'error':
        console.error('Simulation error:', event.data.error);
        setIsRunning(false);
        setIsConnected(false);
        break;
    }
  };

  const stopSimulation = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsRunning(false);
    setIsConnected(false);
  };

  const getEmotionColor = (emotion: string) => {
    switch (emotion) {
      case 'positive': return 'text-green-400 border-green-500/30 bg-green-500/10';
      case 'negative': return 'text-red-400 border-red-500/30 bg-red-500/10';
      case 'excited': return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
      default: return 'text-slate-400 border-slate-500/30 bg-slate-500/10';
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="bg-slate-900/50 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/observer')}
                className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                返回观察者
              </button>
              <div className="h-6 w-px bg-slate-700" />
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h1 className="font-bold text-lg">实时沙盒模拟</h1>
                  <p className="text-xs text-slate-400">实时观察分身互动与思维</p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {isConnected && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/20 text-green-400 rounded-full text-sm">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  实时连接中
                </div>
              )}
              
              <div className="flex items-center gap-2">
                <label className="text-sm text-slate-400">话题:</label>
                <input
                  type="text"
                  value={currentTopic}
                  onChange={(e) => setCurrentTopic(e.target.value)}
                  disabled={isRunning}
                  className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 disabled:opacity-50"
                  placeholder="输入话题..."
                />
              </div>
              
              <div className="flex items-center gap-2">
                <label className="text-sm text-slate-400">轮数:</label>
                <select
                  value={maxRounds}
                  onChange={(e) => setMaxRounds(Number(e.target.value))}
                  disabled={isRunning}
                  className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500 disabled:opacity-50"
                >
                  <option value={3}>3轮</option>
                  <option value={5}>5轮</option>
                  <option value={10}>10轮</option>
                </select>
              </div>

              {!isRunning ? (
                <button
                  onClick={startSimulation}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
                >
                  <Play className="w-4 h-4" />
                  开始模拟
                </button>
              ) : (
                <button
                  onClick={stopSimulation}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
                >
                  <Pause className="w-4 h-4" />
                  停止
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Progress */}
        {isRunning && (
          <div className="mb-6 p-4 bg-slate-900/50 border border-slate-800 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">模拟进度</span>
              <span className="text-sm font-medium">第 {currentRound} / {maxRounds} 轮</span>
            </div>
            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
                initial={{ width: 0 }}
                animate={{ width: `${(currentRound / maxRounds) * 100}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-400">
            <p className="font-medium">出错了</p>
            <p className="text-sm">{error}</p>
            <button
              onClick={() => setError(null)}
              className="mt-2 text-sm underline hover:no-underline"
            >
              关闭
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left - Activity Stream */}
          <div className="lg:col-span-2 space-y-6">
            {/* Avatars Grid */}
            {avatars.length > 0 && (
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5 text-indigo-400" />
                  参与分身 ({avatars.length})
                </h2>
                <div className="flex flex-wrap gap-3">
                  {avatars.map((avatar) => (
                    <div
                      key={avatar.id}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700"
                    >
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold"
                        style={{ background: avatar.color }}
                      >
                        {avatar.name.charAt(0)}
                      </div>
                      <span className="text-sm font-medium">{avatar.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Activity Timeline */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-indigo-400" />
                实时活动流
                {activities.length > 0 && (
                  <span className="text-sm text-slate-500">({activities.length})</span>
                )}
              </h2>
              
              <div className="space-y-3 max-h-[500px] overflow-y-auto scrollbar-hide">
                <AnimatePresence initial={false}>
                  {activities.length === 0 && !isRunning && (
                    <div className="text-center py-12 text-slate-500">
                      <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>点击"开始模拟"启动实时沙盒</p>
                      <p className="text-sm mt-2">观察分身之间的互动和思维过程</p>
                    </div>
                  )}
                  
                  {activities.length === 0 && isRunning && (
                    <div className="flex flex-col items-center justify-center py-12 text-slate-500">
                      <Loader2 className="w-8 h-8 animate-spin mb-3" />
                      <span>{isConnected ? '分身们正在思考中...' : '正在连接沙盒...'}</span>
                      <span className="text-xs mt-2 text-slate-600">首次响应可能需要 5-10 秒</span>
                    </div>
                  )}
                  
                  {activities.map((activity) => (
                    <motion.div
                      key={activity.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className={cn(
                        'p-4 rounded-lg border transition-all',
                        getEmotionColor(activity.emotion)
                      )}
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0"
                          style={{ background: avatars.find(a => a.id === activity.avatar_id)?.color || '#666' }}
                        >
                          {activity.avatar_name.charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-white">{activity.avatar_name}</span>
                            <span className="text-xs opacity-70">
                              {activity.action === 'speaking' && '💬 发言'}
                              {activity.action === 'thinking' && '🧠 思考'}
                              {activity.action === 'reacting' && '⚡ 反应'}
                            </span>
                            <span className="text-xs opacity-50">第{activity.round}轮</span>
                          </div>
                          <p className="text-white/90 text-sm leading-relaxed">
                            {activity.content}
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <span className="text-xs opacity-60 px-2 py-0.5 bg-white/10 rounded-full">
                              #{activity.topic}
                            </span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                <div ref={activityEndRef} />
              </div>
            </div>
          </div>

          {/* Right - Thinking & Relations */}
          <div className="space-y-6">
            {/* Thinking Panel */}
            {Object.keys(thinkingLogs).length > 0 && (
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-indigo-400" />
                  思维过程
                </h2>
                <div className="space-y-4 max-h-[300px] overflow-y-auto">
                  {Object.entries(thinkingLogs).map(([avatarId, thoughts]) => {
                    const avatar = avatars.find(a => a.id === avatarId);
                    if (!avatar || thoughts.length === 0) return null;
                    
                    return (
                      <div key={avatarId} className="border-b border-slate-800 pb-3 last:border-0">
                        <div className="flex items-center gap-2 mb-2">
                          <div
                            className="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold"
                            style={{ background: avatar.color }}
                          >
                            {avatar.name.charAt(0)}
                          </div>
                          <span className="text-sm font-medium text-slate-300">{avatar.name}</span>
                        </div>
                        <div className="space-y-1">
                          {thoughts.slice(-3).map((thought, idx) => (
                            <motion.div
                              key={idx}
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              className="p-2 bg-slate-800/50 rounded text-xs text-slate-400"
                            >
                              {thought}
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Relations Network */}
            {relations.length > 0 && (
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Network className="w-5 h-5 text-indigo-400" />
                  关系网络
                  <span className="text-sm text-slate-500">({relations.length})</span>
                </h2>
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {relations.map((rel, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                    >
                      <div className="flex items-center gap-2 text-sm">
                        <span className="font-medium text-slate-300">{rel.from_name}</span>
                        <span className={cn(
                          'text-xs px-2 py-0.5 rounded-full',
                          rel.relation === 'agree' && 'bg-green-500/20 text-green-400',
                          rel.relation === 'disagree' && 'bg-red-500/20 text-red-400',
                          rel.relation === 'curious' && 'bg-amber-500/20 text-amber-400',
                          rel.relation === 'neutral' && 'bg-slate-500/20 text-slate-400'
                        )}>
                          {rel.relation === 'agree' && '赞同'}
                          {rel.relation === 'disagree' && '反对'}
                          {rel.relation === 'curious' && '好奇'}
                          {rel.relation === 'neutral' && '中立'}
                        </span>
                        <span className="font-medium text-slate-300">{rel.to_name}</span>
                      </div>
                      <div className="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full',
                            rel.relation === 'agree' && 'bg-green-500',
                            rel.relation === 'disagree' && 'bg-red-500',
                            rel.relation === 'curious' && 'bg-amber-500',
                            rel.relation === 'neutral' && 'bg-slate-500'
                          )}
                          style={{ width: `${rel.strength * 100}%` }}
                        />
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Topic Evolution */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-indigo-400" />
                话题演进
              </h2>
              <div className="p-4 bg-gradient-to-br from-indigo-600/20 to-purple-600/20 border border-indigo-500/30 rounded-lg">
                <p className="text-sm text-slate-400 mb-1">当前话题</p>
                <p className="text-xl font-bold text-white">#{currentTopic}</p>
              </div>
              <p className="text-xs text-slate-500 mt-3">
                分身会根据对话内容自然切换话题
              </p>
            </div>

            {/* Stats */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
              <h3 className="font-semibold mb-4">实时统计</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">活动数量</span>
                  <span className="font-medium">{activities.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">关系变化</span>
                  <span className="font-medium">{relations.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">参与分身</span>
                  <span className="font-medium">{avatars.length}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
