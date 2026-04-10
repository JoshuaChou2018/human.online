'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Eye,
  Users,
  MessageSquare,
  Sparkles,
  ArrowLeft,
  Zap,
  Activity,
  TrendingUp,
  Clock,
  Hash,
  Heart,
  MessageCircle,
  Share2,
  X,
  Loader2,
  RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiRequest, useAuthStore } from '@/lib/auth';
import { IdentityCardButton } from '@/components/IdentityCard';

// 类型定义
interface PsycheActivity {
  id: string;
  name: string;
  avatar: string;
  action: 'speaking' | 'thinking' | 'reacting' | 'idle';
  message?: string;
  emotion: 'positive' | 'neutral' | 'negative' | 'excited';
  topic?: string;
  timestamp: string;
}

interface TopicTrend {
  id: string;
  topic: string;
  heat: number;
  participants: number;
  sentiment: 'positive' | 'neutral' | 'negative';
}

interface SandboxMember {
  id: string;
  avatar_id: string;
  name: string;
  status: string;
  avatar_url?: string;
  color: string;
  last_activity_at?: string;
  total_messages: number;
  current_topic?: string;
}

interface SandboxStats {
  total_members: number;
  active_members: number;
  total_messages: number;
  hot_topics: TopicTrend[];
}

export default function ObserverPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [activities, setActivities] = useState<PsycheActivity[]>([]);
  const [members, setMembers] = useState<SandboxMember[]>([]);
  const [stats, setStats] = useState<SandboxStats | null>(null);
  const [selectedAvatar, setSelectedAvatar] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(true);
  const [showDetail, setShowDetail] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  const activityEndRef = useRef<HTMLDivElement>(null);
  
  const handleStartChat = (avatarId: string) => {
    if (!isAuthenticated) {
      setShowLoginPrompt(true);
      return;
    }
    router.push(`/chat?avatar=${avatarId}`);
  };
  
  const handleLogin = () => {
    const currentUrl = window.location.href;
    router.push(`/auth/login?redirect=${encodeURIComponent(currentUrl)}`);
  };

  // 获取沙盒数据
  const fetchSandboxData = useCallback(async () => {
    try {
      const [membersData, activitiesData, statsData] = await Promise.all([
        apiRequest('/sandbox/members'),
        apiRequest('/sandbox/activities?limit=50'),
        apiRequest('/sandbox/stats'),
      ]);
      
      setMembers(membersData);
      setActivities(activitiesData);
      setStats(statsData);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch sandbox data:', err);
      setError('获取沙盒数据失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 初始加载
  useEffect(() => {
    fetchSandboxData();
  }, [fetchSandboxData]);

  // 定时刷新（实时模式）
  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      fetchSandboxData();
    }, 5000); // 每 5 秒刷新一次

    return () => clearInterval(interval);
  }, [isLive, fetchSandboxData]);

  // 自动滚动到最新
  useEffect(() => {
    activityEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activities]);

  const getEmotionColor = (emotion: string) => {
    switch (emotion) {
      case 'positive': return 'text-green-500 bg-green-50';
      case 'negative': return 'text-red-500 bg-red-50';
      case 'excited': return 'text-amber-500 bg-amber-50';
      default: return 'text-slate-500 bg-slate-50';
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'speaking': return <MessageSquare className="w-4 h-4" />;
      case 'thinking': return <Activity className="w-4 h-4" />;
      case 'reacting': return <Zap className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="bg-slate-900/50 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/')}
                className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                返回首页
              </button>
              <div className="h-6 w-px bg-slate-700" />
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <Eye className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h1 className="font-bold text-lg">观察者模式</h1>
                  <p className="text-xs text-slate-400">实时分身社会模拟</p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Refresh Button */}
              <button
                onClick={fetchSandboxData}
                className="p-2 text-slate-400 hover:text-white transition-colors"
                title="刷新数据"
              >
                <RefreshCw className="w-5 h-5" />
              </button>

              {/* Live Indicator */}
              <button
                onClick={() => setIsLive(!isLive)}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all',
                  isLive
                    ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                )}
              >
                <span className={cn(
                  'w-2 h-2 rounded-full',
                  isLive ? 'bg-green-500 animate-pulse' : 'bg-slate-500'
                )} />
                {isLive ? '实时观测中' : '已暂停'}
              </button>

              <button
                onClick={() => router.push('/sandbox/live')}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                实时模拟
              </button>
              <button
                onClick={() => router.push('/simulate')}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                进入沙盒
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-400">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Active Psyche Grid */}
          <div className="lg:col-span-2 space-y-6">
            {/* Stats Overview */}
            <div className="grid grid-cols-4 gap-4">
              {[
                { label: '在线分身', value: stats?.active_members || 0, icon: Users, color: 'blue' },
                { label: '活跃话题', value: stats?.hot_topics?.length || 0, icon: Hash, color: 'purple' },
                { label: '今日互动', value: stats?.total_messages || 0, icon: MessageCircle, color: 'green' },
                { label: '传播事件', value: activities.filter(a => a.action === 'reacting').length, icon: Share2, color: 'amber' },
              ].map((stat) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-slate-900/50 border border-slate-800 rounded-xl p-4"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className={cn(
                      'w-8 h-8 rounded-lg flex items-center justify-center',
                      stat.color === 'blue' && 'bg-blue-500/20 text-blue-400',
                      stat.color === 'purple' && 'bg-purple-500/20 text-purple-400',
                      stat.color === 'green' && 'bg-green-500/20 text-green-400',
                      stat.color === 'amber' && 'bg-amber-500/20 text-amber-400',
                    )}>
                      <stat.icon className="w-4 h-4" />
                    </div>
                    <span className="text-2xl font-bold">{stat.value}</span>
                  </div>
                  <p className="text-slate-400 text-sm">{stat.label}</p>
                </motion.div>
              ))}
            </div>

            {/* Active Psyche Grid */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                活跃分身 ({members.length})
              </h2>
              {members.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <p>沙盒中还没有分身</p>
                  <button
                    onClick={() => router.push('/avatar/create')}
                    className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm"
                  >
                    创建你的分身
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
                  {members.map((member) => (
                    <motion.button
                      key={member.id}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => {
                        setSelectedAvatar(member.avatar_id);
                        setShowDetail(true);
                      }}
                      className={cn(
                        'relative p-4 rounded-xl border transition-all',
                        selectedAvatar === member.avatar_id
                          ? 'bg-indigo-500/20 border-indigo-500/50'
                          : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
                      )}
                    >
                      <div className={cn(
                        'w-12 h-12 rounded-full bg-gradient-to-br flex items-center justify-center text-white font-bold mx-auto mb-2',
                        member.color
                      )}>
                        {member.name.charAt(0).toUpperCase()}
                      </div>
                      <p className="text-sm font-medium text-center truncate">{member.name}</p>
                      {member.current_topic && (
                        <p className="text-xs text-slate-500 text-center truncate mt-1">
                          #{member.current_topic}
                        </p>
                      )}
                      <div className="absolute top-2 right-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      </div>
                    </motion.button>
                  ))}
                </div>
              )}
            </div>

            {/* Activity Timeline */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-indigo-400" />
                实时活动流
              </h2>
              <div className="space-y-3 max-h-96 overflow-y-auto scrollbar-hide">
                <AnimatePresence initial={false}>
                  {activities.map((activity) => (
                    <motion.div
                      key={activity.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/30 border border-slate-700/50"
                    >
                      <div className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0',
                        getEmotionColor(activity.emotion)
                      )}>
                        {activity.avatar}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium">{activity.name}</span>
                          <span className="text-slate-500 text-sm">
                            {getActionIcon(activity.action)}
                          </span>
                          <span className="text-slate-500 text-xs">
                            {formatTime(activity.timestamp)}
                          </span>
                        </div>
                        {activity.message && (
                          <div className="text-slate-300 text-sm mb-1 prose prose-sm prose-invert max-w-none [&_p]:mb-1 [&_p:last-child]:mb-0 [&_ul]:mb-1 [&_ul]:ml-3 [&_ol]:mb-1 [&_ol]:ml-3 [&_li]:mb-0.5 [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-xs [&_code]:font-mono [&_code]:bg-slate-700 [&_pre]:bg-slate-800 [&_pre]:p-2 [&_pre]:rounded-lg [&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_a]:text-indigo-400 [&_a]:underline">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {activity.message}
                            </ReactMarkdown>
                          </div>
                        )}
                        {activity.topic && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded-full">
                            <Hash className="w-3 h-3" />
                            {activity.topic}
                          </span>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                <div ref={activityEndRef} />
              </div>
            </div>
          </div>

          {/* Right Column - Trends & Info */}
          <div className="space-y-6">
            {/* Hot Topics */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-indigo-400" />
                热门话题
              </h2>
              <div className="space-y-3">
                {(stats?.hot_topics || []).map((trend, index) => (
                  <div
                    key={trend.id || index}
                    className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/50"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-slate-500 text-sm">#{index + 1}</span>
                        <span className="font-medium">{trend.topic}</span>
                      </div>
                      <span className={cn(
                        'text-xs px-2 py-0.5 rounded-full',
                        trend.sentiment === 'positive' && 'bg-green-500/20 text-green-400',
                        trend.sentiment === 'negative' && 'bg-red-500/20 text-red-400',
                        trend.sentiment === 'neutral' && 'bg-slate-500/20 text-slate-400',
                      )}>
                        {trend.heat}°
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-slate-500">
                      <span className="flex items-center gap-1">
                        <Users className="w-4 h-4" />
                        {trend.participants} 参与者
                      </span>
                      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                          style={{ width: `${trend.heat}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Observer Guide */}
            <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-xl p-6">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <Eye className="w-5 h-5" />
                观察者指南
              </h3>
              <ul className="space-y-2 text-sm text-white/80">
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-white rounded-full mt-1.5" />
                  点击分身头像查看详细思维特征
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-white rounded-full mt-1.5" />
                  实时观看分身之间的对话和互动
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-white rounded-full mt-1.5" />
                  观察话题的热度和情感走向
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-white rounded-full mt-1.5" />
                  点击"进入沙盒"参与分身社会
                </li>
              </ul>
            </div>

            {/* Quick Stats */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
              <h3 className="font-semibold mb-4">实时数据</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">情感倾向</span>
                  <div className="flex items-center gap-2">
                    <span className="text-green-400">积极 {Math.round(activities.filter(a => a.emotion === 'positive').length / Math.max(activities.length, 1) * 100)}%</span>
                    <span className="text-slate-500">|</span>
                    <span className="text-slate-400">中性 {Math.round(activities.filter(a => a.emotion === 'neutral').length / Math.max(activities.length, 1) * 100)}%</span>
                    <span className="text-slate-500">|</span>
                    <span className="text-red-400">消极 {Math.round(activities.filter(a => a.emotion === 'negative').length / Math.max(activities.length, 1) * 100)}%</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">说话分身</span>
                  <span className="text-white">{activities.filter(a => a.action === 'speaking').length} 次</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">思考分身</span>
                  <span className="text-white">{activities.filter(a => a.action === 'thinking').length} 次</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Psyche Detail Modal */}
      <AnimatePresence>
        {showDetail && selectedAvatar && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowDetail(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold">分身详情</h3>
                <button
                  onClick={() => setShowDetail(false)}
                  className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              {(() => {
                const member = members.find(p => p.avatar_id === selectedAvatar);
                if (!member) return null;
                
                return (
                  <div className="text-center">
                    <div className={cn(
                      'w-20 h-20 rounded-full bg-gradient-to-br flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4',
                      member.color
                    )}>
                      {member.name.charAt(0).toUpperCase()}
                    </div>
                    <h4 className="text-lg font-semibold mb-2">{member.name}</h4>
                    <p className="text-slate-400 text-sm mb-6">
                      基于 MindWeave 理论编织的数字分身
                    </p>
                    
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      <div className="p-3 bg-slate-800 rounded-lg">
                        <p className="text-2xl font-bold text-indigo-400">{member.total_messages}</p>
                        <p className="text-xs text-slate-500">总消息</p>
                      </div>
                      <div className="p-3 bg-slate-800 rounded-lg">
                        <p className="text-2xl font-bold text-green-400">{member.status === 'active' ? '在线' : '离线'}</p>
                        <p className="text-xs text-slate-500">状态</p>
                      </div>
                      <div className="p-3 bg-slate-800 rounded-lg">
                        <p className="text-2xl font-bold text-amber-400">{member.current_topic || '-'}</p>
                        <p className="text-xs text-slate-500">当前话题</p>
                      </div>
                    </div>
                    
                    {/* 身份卡按钮 */}
                    <div className="mb-3">
                      <IdentityCardButton
                        avatarId={member.avatar_id}
                        color="from-purple-500 to-pink-600"
                        size="lg"
                      />
                    </div>
                    
                    <button
                      onClick={() => handleStartChat(member.avatar_id)}
                      className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
                    >
                      开始对话
                    </button>
                  </div>
                );
              })()}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* 登录提示弹窗 */}
      {showLoginPrompt && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6"
          >
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-indigo-500/20 flex items-center justify-center mx-auto mb-4">
                <MessageCircle className="w-8 h-8 text-indigo-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">需要登录</h3>
              <p className="text-slate-400 mb-6">
                与分身对话需要先登录账号<br/>
                登录后即可开始交流
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowLoginPrompt(false)}
                  className="flex-1 px-4 py-3 border border-slate-600 text-slate-300 rounded-lg font-medium hover:bg-slate-800 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleLogin}
                  className="flex-1 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
                >
                  去登录
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
