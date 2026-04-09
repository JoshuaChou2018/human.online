'use client';

import Link from 'next/link';
import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  Users, 
  Share2, 
  MessageSquare, 
  TrendingUp,
  Shield,
  Zap,
  Network,
  Eye,
  User,
  LogOut,
  Database,
  GitBranch,
  ArrowRight
} from 'lucide-react';
import { useAuthStore } from '@/lib/auth';

// 打字机效果 hook
function useTypewriter(text: string, speed: number = 30, startDelay: number = 0) {
  const [displayText, setDisplayText] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    setDisplayText('');
    setIsComplete(false);
    
    const startTimeout = setTimeout(() => {
      let index = 0;
      const timer = setInterval(() => {
        if (index < text.length) {
          setDisplayText(text.slice(0, index + 1));
          index++;
        } else {
          setIsComplete(true);
          clearInterval(timer);
        }
      }, speed);

      return () => clearInterval(timer);
    }, startDelay);

    return () => clearTimeout(startTimeout);
  }, [text, speed, startDelay]);

  return { displayText, isComplete };
}

export default function HomePage() {
  const { user, isAuthenticated, logout, checkAuth } = useAuthStore();
  
  // 对话流程控制
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [showAllMessages, setShowAllMessages] = useState(false);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* 导航栏 */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-xl text-slate-900">Human.online</span>
          </div>
          
          <div className="flex items-center gap-6">
            <a href="#features" className="text-sm text-slate-600 hover:text-slate-900 transition-colors">
              功能
            </a>
            <a href="#how-it-works" className="text-sm text-slate-600 hover:text-slate-900 transition-colors">
              原理
            </a>
            <Link 
              href="/market" 
              className="text-sm text-slate-600 hover:text-slate-900 transition-colors"
            >
              分身市场
            </Link>
            <Link 
              href="/observer" 
              className="text-sm text-slate-600 hover:text-slate-900 transition-colors"
            >
              观察者模式
            </Link>
            
            {isAuthenticated ? (
              <div className="flex items-center gap-4">
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 px-4 py-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  <Database className="w-4 h-4" />
                  数据中心
                </Link>
                <div className="flex items-center gap-3 pl-4 border-l">
                  {user?.avatar_url ? (
                    <img src={user.avatar_url} alt="" className="w-8 h-8 rounded-full" />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                      <User className="w-4 h-4 text-indigo-600" />
                    </div>
                  )}
                  <span className="text-sm font-medium">{user?.display_name || user?.email}</span>
                  <button
                    onClick={logout}
                    className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="退出登录"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <Link
                href="/auth/login"
                className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
              >
                登录 / 注册
              </Link>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-700 rounded-full text-sm font-medium mb-8">
            <Sparkles className="w-4 h-4" />
            基于 MindWeave 思维编织理论
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold text-slate-900 leading-tight mb-6">
            构建你的
            <span className="bg-gradient-to-r from-indigo-500 to-purple-600 bg-clip-text text-transparent">
              数字分身
            </span>
            <br />
            探索数字社会
          </h1>
          
          <p className="text-xl text-slate-600 max-w-2xl mx-auto mb-10 leading-relaxed">
            上传你的聊天记录、书籍文章，AI 将提取你的认知特征，构建一个拥有你思维方式的数字分身。
            在数字社会中与名人分身对话，测试言论的社会影响。
          </p>
          
          <div className="flex items-center justify-center gap-4 flex-wrap">
            {isAuthenticated ? (
              <Link
                href="/avatar/create"
                className="px-8 py-4 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-500/25 flex items-center gap-2"
              >
                <Sparkles className="w-5 h-5" />
                {user?.can_create_free_avatar ? '免费创建分身' : '创建更多分身'}
              </Link>
            ) : (
              <Link
                href="/auth/login"
                className="px-8 py-4 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-500/25 flex items-center gap-2"
              >
                <Sparkles className="w-5 h-5" />
                免费创建我的分身
              </Link>
            )}
            <Link
              href="/market"
              className="px-8 py-4 bg-white text-slate-700 font-semibold rounded-xl border border-slate-200 hover:bg-slate-50 transition-all flex items-center gap-2"
            >
              <Users className="w-5 h-5" />
              浏览名人分身
            </Link>
            <Link
              href="/observer"
              className="px-8 py-4 bg-gradient-to-r from-slate-800 to-slate-900 text-white font-semibold rounded-xl hover:from-slate-900 hover:to-slate-950 transition-all flex items-center gap-2 group"
            >
              <Eye className="w-5 h-5 group-hover:animate-pulse" />
              进入观察模式
            </Link>
          </div>

          {/* 已登录用户的额外信息 */}
          {isAuthenticated && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-8 inline-flex items-center gap-4 px-6 py-3 bg-white rounded-xl border border-slate-200 shadow-sm"
            >
              <div className="text-left">
                <p className="text-sm text-slate-500">免费创建额度</p>
                <p className="font-semibold text-indigo-600">
                  剩余 {user?.remaining_free_quota || 0} 个
                </p>
              </div>
              <div className="h-8 w-px bg-slate-200" />
              <Link
                href="/dashboard"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
              >
                管理我的数据 →
              </Link>
            </motion.div>
          )}
        </div>
      </section>

      {/* 演示对话 - 动态打字效果 */}
      <DemoConversationSection isAuthenticated={isAuthenticated} />

      {/* 反事实模拟可视化展示 */}
      <SimulationShowcaseSection />

      {/* 功能特点 */}
      <section id="features" className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">核心功能</h2>
            <p className="text-slate-600">从认知蒸馏到社会模拟，全方位的数字分身体验</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Network,
                title: '思维编织',
                description: '基于 MindWeave 理论，提取六维思维线索，编织独特的数字分身',
                color: 'from-blue-400 to-indigo-500',
              },
              {
                icon: MessageSquare,
                title: '深度对话',
                description: '与自己和名人分身进行多轮深度对话，体验不同思维方式的碰撞',
                color: 'from-indigo-400 to-purple-500',
              },
              {
                icon: Share2,
                title: '社会模拟',
                description: '在数字社会沙盒中测试言论影响，观察舆论传播和社会反应。点击"进入观察模式"实时观看分身互动',
                color: 'from-purple-400 to-pink-500',
              },
              {
                icon: Users,
                title: '分身市场',
                description: '探索和使用社区创建的名人分身，与乔布斯、马斯克、芒格对话',
                color: 'from-pink-400 to-rose-500',
              },
              {
                icon: TrendingUp,
                title: '影响力分析',
                description: '可视化传播路径，分析关键影响者，理解社会动态',
                color: 'from-amber-400 to-orange-500',
              },
              {
                icon: Shield,
                title: '隐私保护',
                description: '你的数据仅用于构建分身，支持本地处理和端到端加密',
                color: 'from-emerald-400 to-teal-500',
              },
            ].map((feature, index) => (
              <div
                key={index}
                className="group p-6 bg-white rounded-2xl border border-slate-100 hover:border-indigo-200 hover:shadow-xl transition-all"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{feature.title}</h3>
                <p className="text-slate-600 text-sm leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 工作原理 */}
      <section id="how-it-works" className="py-20 px-6 bg-slate-900 text-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">MindWeave 理论</h2>
            <p className="text-slate-400">六维思维线索编织，重构数字分身</p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { num: '01', title: '思维内核', desc: '核心认知模式、思考方式' },
              { num: '02', title: '表达风格', desc: '语言习惯、修辞特点' },
              { num: '03', title: '决策逻辑', desc: '判断模式、选择偏好' },
              { num: '04', title: '知识图谱', desc: '知识体系、认知边界' },
              { num: '05', title: '价值体系', desc: '价值观、原则、底线' },
              { num: '06', title: '情感模式', desc: '情感反应、情绪表达' },
            ].map((item, index) => (
              <div key={index} className="p-6 bg-white/5 backdrop-blur rounded-2xl border border-white/10">
                <span className="text-4xl font-bold text-indigo-400/30">{item.num}</span>
                <h3 className="text-lg font-semibold mt-2 mb-1">{item.title}</h3>
                <p className="text-slate-400 text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-slate-900 mb-4">
            准备好编织你的数字分身了吗？
          </h2>
          <p className="text-slate-600 mb-8">
            登录后上传你的数据，开始 MindWeave 之旅。免费创建一个由你的思维线索编织而成的数字分身。
          </p>
          {isAuthenticated ? (
            <Link
              href="/avatar/create"
              className="inline-flex items-center gap-2 px-8 py-4 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-500/25"
            >
              <Zap className="w-5 h-5" />
              创建我的分身
            </Link>
          ) : (
            <Link
              href="/auth/login"
              className="inline-flex items-center gap-2 px-8 py-4 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-500/25"
            >
              <Zap className="w-5 h-5" />
              免费开始创建
            </Link>
          )}
          <p className="text-xs text-slate-400 mt-4">使用 Google 账号快速登录，无需信用卡</p>
        </div>
      </section>

      {/* 页脚 */}
      <footer className="py-12 px-6 border-t">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
            <span className="font-semibold text-slate-900">Human.online</span>
          </div>
          
          <div className="flex items-center gap-6 text-sm text-slate-500">
            <a href="/privacy" className="hover:text-slate-900 transition-colors">隐私</a>
            <a href="/terms" className="hover:text-slate-900 transition-colors">条款</a>
            <a href="https://github.com/JoshuaChou2018/human.online" target="_blank" rel="noopener noreferrer" className="hover:text-slate-900 transition-colors">GitHub</a>
          </div>
          
          <p className="text-sm text-slate-400">
            © 2024 Human.online. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

// 演示对话组件 - 动态打字效果
function DemoConversationSection({ isAuthenticated }: { isAuthenticated: boolean }) {
  const messages = [
    {
      id: 1,
      role: 'user',
      content: 'OpenAI 和 Anthropic 谁的方向是对的？',
    },
    {
      id: 2,
      role: 'assistant',
      content: '你问错了。这不是一场关于方向的竞赛。这是一场关于品味的竞赛。',
    },
    {
      id: 3,
      role: 'assistant',
      content: 'OpenAI 像 1985 年的微软。什么都做，什么都要赢。这种策略能赢市场份额。问题是——当你什么都做的时候，你不可能每件事都做到 insanely great。',
    },
    {
      id: 4,
      role: 'assistant',
      content: '但两家公司都犯了一个我绝对不会犯的错误——他们不控制硬件。',
    },
  ];

  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAll, setShowAll] = useState(false);
  const [displayedContent, setDisplayedContent] = useState<string[]>(new Array(messages.length).fill(''));

  useEffect(() => {
    if (showAll) {
      // 如果点击了跳过，直接显示所有内容
      setDisplayedContent(messages.map(m => m.content));
      setCurrentIndex(messages.length);
      return;
    }

    if (currentIndex >= messages.length) return;

    const currentMessage = messages[currentIndex];
    let charIndex = 0;
    
    const timer = setInterval(() => {
      if (charIndex < currentMessage.content.length) {
        setDisplayedContent(prev => {
          const newContent = [...prev];
          newContent[currentIndex] = currentMessage.content.slice(0, charIndex + 1);
          return newContent;
        });
        charIndex++;
      } else {
        clearInterval(timer);
        // 等待一下后显示下一条
        setTimeout(() => {
          setCurrentIndex(prev => prev + 1);
        }, currentMessage.role === 'user' ? 500 : 1200);
      }
    }, currentMessage.role === 'user' ? 30 : 25);

    return () => clearInterval(timer);
  }, [currentIndex, showAll]);

  const isTyping = currentIndex < messages.length && !showAll;

  return (
    <section className="py-20 px-6 bg-slate-50">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-900 mb-4">与思维大师对话</h2>
          <p className="text-slate-600">不是角色扮演，而是基于认知框架的真实思维碰撞</p>
        </div>
        
        <div className="bg-white rounded-2xl shadow-xl border overflow-hidden">
          {/* 对话头部 */}
          <div className="px-6 py-4 border-b bg-slate-50/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex -space-x-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center text-white text-xs font-medium border-2 border-white">
                  S
                </div>
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-medium border-2 border-white">
                  N
                </div>
              </div>
              <span className="font-medium text-slate-700">与 Steve Jobs 对话</span>
            </div>
            <div className="flex items-center gap-2">
              {isTyping && (
                <button
                  onClick={() => setShowAll(true)}
                  className="text-xs text-slate-500 hover:text-indigo-600 transition-colors px-2 py-1 rounded hover:bg-slate-100"
                >
                  跳过动画 →
                </button>
              )}
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                AI 驱动
              </div>
            </div>
          </div>
          
          {/* 对话内容 */}
          <div className="p-6 space-y-4 min-h-[300px]">
            {messages.map((message, index) => {
              const isVisible = index <= currentIndex || showAll;
              const isCurrentMessage = index === currentIndex && !showAll;
              
              if (!isVisible) return null;
              
              const isUser = message.role === 'user';
              
              return (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex gap-3 ${isUser ? '' : 'flex-row-reverse'}`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 ${
                    isUser 
                      ? 'bg-gradient-to-br from-slate-100 to-slate-200 text-slate-600' 
                      : 'bg-gradient-to-br from-gray-700 to-gray-900 text-white'
                  }`}>
                    {isUser ? '我' : 'S'}
                  </div>
                  <div className={`flex-1 ${isUser ? '' : 'flex flex-col items-end'}`}>
                    <div className={`relative rounded-2xl px-4 py-2.5 inline-block max-w-lg ${
                      isUser 
                        ? 'bg-slate-100 text-slate-700 rounded-tl-md' 
                        : 'bg-slate-800 text-white rounded-tr-md'
                    }`}>
                      <span>{displayedContent[index]}</span>
                      {isCurrentMessage && (
                        <span className="inline-block w-0.5 h-4 bg-current ml-0.5 animate-pulse" />
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
          
          {/* 输入框 */}
          <div className="px-6 py-4 border-t bg-slate-50">
            <div className="flex gap-3">
              <input
                type="text"
                placeholder={isAuthenticated ? "输入消息..." : "登录后即可开始对话"}
                className="flex-1 px-4 py-2 bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                readOnly
              />
              <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg opacity-50 cursor-not-allowed">
                发送
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}


// ============================================
// 反事实模拟动态可视化展示
// ============================================

function SimulationShowcaseSection() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const [isHovering, setIsHovering] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 设置画布尺寸
    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * 2;
      canvas.height = rect.height * 2;
      ctx.scale(2, 2);
    };
    resize();
    window.addEventListener('resize', resize);

    // 模拟节点数据
    const nodes = [
      { id: 'trump', name: '特朗普', emoji: '👤', x: 0.3, y: 0.4, color: '#ef4444', sentiment: -0.6 },
      { id: 'musk', name: '马斯克', emoji: '👨‍🚀', x: 0.7, y: 0.3, color: '#6366f1', sentiment: 0.2 },
      { id: 'buffett', name: '巴菲特', emoji: '🧓', x: 0.6, y: 0.7, color: '#22c55e', sentiment: -0.2 },
      { id: 'naval', name: 'Naval', emoji: '🧘', x: 0.2, y: 0.6, color: '#8b5cf6', sentiment: 0.1 },
      { id: 'joey', name: 'Joey', emoji: '🎭', x: 0.8, y: 0.6, color: '#f59e0b', sentiment: 0.5 },
      { id: 'jobs', name: '乔布斯', emoji: '🍎', x: 0.4, y: 0.2, color: '#3b82f6', sentiment: 0.3 },
    ];

    // 模拟边（传播路径）
    const edges = [
      { source: 'trump', target: 'musk', step: 1 },
      { source: 'trump', target: 'buffett', step: 2 },
      { source: 'musk', target: 'joey', step: 2 },
      { source: 'buffett', target: 'naval', step: 3 },
      { source: 'jobs', target: 'musk', step: 3 },
      { source: 'naval', target: 'joey', step: 4 },
    ];

    let time = 0;
    let currentStep = 0;
    const stepDuration = 60; // 每步持续帧数

    const animate = () => {
      const rect = canvas.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;

      // 清空画布
      ctx.clearRect(0, 0, width, height);

      // 计算当前步骤（循环播放）
      currentStep = Math.floor(time / stepDuration) % 5;
      time += isHovering ? 0.5 : 1; // 悬停时减慢动画

      // 绘制连线
      edges.forEach((edge, index) => {
        const sourceNode = nodes.find(n => n.id === edge.source);
        const targetNode = nodes.find(n => n.id === edge.target);
        if (!sourceNode || !targetNode) return;

        const sx = sourceNode.x * width;
        const sy = sourceNode.y * height;
        const tx = targetNode.x * width;
        const ty = targetNode.y * height;

        // 边动画效果
        const isActive = edge.step <= currentStep;
        const isNew = edge.step === currentStep;
        const progress = isActive ? 1 : Math.max(0, (time % stepDuration) / stepDuration);

        if (progress > 0) {
          ctx.beginPath();
          ctx.moveTo(sx, sy);
          
          // 绘制带动画的虚线
          const dx = tx - sx;
          const dy = ty - sy;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const currentDist = dist * progress;
          const angle = Math.atan2(dy, dx);
          
          const cx = sx + Math.cos(angle) * currentDist;
          const cy = sy + Math.sin(angle) * currentDist;
          
          ctx.lineTo(cx, cy);
          ctx.strokeStyle = isNew ? '#6366f1' : '#94a3b8';
          ctx.lineWidth = isNew ? 3 : 2;
          ctx.setLineDash(isActive && !isNew ? [5, 5] : []);
          ctx.stroke();
          ctx.setLineDash([]);

          // 绘制流动粒子效果
          if (isActive) {
            const particleOffset = (time * 2) % dist;
            const px = sx + Math.cos(angle) * particleOffset;
            const py = sy + Math.sin(angle) * particleOffset;
            
            ctx.beginPath();
            ctx.arc(px, py, 3, 0, Math.PI * 2);
            ctx.fillStyle = '#6366f1';
            ctx.fill();
          }
        }
      });

      // 绘制节点
      nodes.forEach((node, index) => {
        const x = node.x * width;
        const y = node.y * height;
        const isActivated = edges.some(e => 
          (e.source === node.id || e.target === node.id) && e.step <= currentStep
        ) || node.id === 'trump'; // 发起者默认激活

        // 节点外圈（情绪颜色）
        if (isActivated) {
          ctx.beginPath();
          ctx.arc(x, y, 28, 0, Math.PI * 2);
          ctx.strokeStyle = node.color;
          ctx.lineWidth = 3;
          ctx.stroke();
        }

        // 节点背景
        ctx.beginPath();
        ctx.arc(x, y, 24, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        
        // 节点边框
        ctx.beginPath();
        ctx.arc(x, y, 24, 0, Math.PI * 2);
        ctx.strokeStyle = isActivated ? node.color : '#cbd5e1';
        ctx.lineWidth = isActivated ? 3 : 2;
        ctx.stroke();

        // 绘制emoji
        ctx.font = '20px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(node.emoji, x, y);

        // 绘制名字
        ctx.font = '12px sans-serif';
        ctx.fillStyle = '#475569';
        ctx.fillText(node.name, x, y + 35);

        // 激活步骤标记
        if (isActivated && node.id !== 'trump') {
          const activationStep = edges.find(e => e.target === node.id)?.step || 0;
          ctx.beginPath();
          ctx.arc(x + 18, y - 18, 10, 0, Math.PI * 2);
          ctx.fillStyle = '#6366f1';
          ctx.fill();
          ctx.fillStyle = '#ffffff';
          ctx.font = 'bold 10px sans-serif';
          ctx.fillText(String(activationStep), x + 18, y - 18);
        }
      });

      // 绘制标题和说明
      ctx.font = 'bold 16px sans-serif';
      ctx.fillStyle = '#1e293b';
      ctx.textAlign = 'left';
      ctx.fillText('反事实模拟演示', 20, 30);
      
      ctx.font = '13px sans-serif';
      ctx.fillStyle = '#64748b';
      ctx.fillText('观察舆论在数字社会中的传播路径', 20, 50);

      // 绘制图例
      const legendY = height - 60;
      ctx.font = '11px sans-serif';
      ctx.fillStyle = '#64748b';
      
      // 支持
      ctx.beginPath();
      ctx.arc(20, legendY, 6, 0, Math.PI * 2);
      ctx.fillStyle = '#22c55e';
      ctx.fill();
      ctx.fillStyle = '#64748b';
      ctx.fillText('支持', 32, legendY + 3);
      
      // 反对
      ctx.beginPath();
      ctx.arc(80, legendY, 6, 0, Math.PI * 2);
      ctx.fillStyle = '#ef4444';
      ctx.fill();
      ctx.fillStyle = '#64748b';
      ctx.fillText('反对', 92, legendY + 3);
      
      // 中立
      ctx.beginPath();
      ctx.arc(140, legendY, 6, 0, Math.PI * 2);
      ctx.fillStyle = '#64748b';
      ctx.fill();
      ctx.fillText('中立', 152, legendY + 3);

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resize);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isHovering]);

  return (
    <section className="py-20 px-6 bg-gradient-to-b from-slate-50 to-indigo-50/30">
      <div className="max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* 左侧：文字说明 */}
          <div>
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium mb-4">
                <GitBranch className="w-4 h-4" />
                数字社会模拟器
              </div>
              <h2 className="text-3xl font-bold text-slate-900 mb-4">
                探索"如果...会怎样"
              </h2>
              <p className="text-slate-600 mb-6 leading-relaxed">
                在数字社会沙盒中测试假设性事件的影响。模拟特朗普宣布对伊朗军事行动、
                AI意识觉醒等场景，观察不同数字分身如何反应、传播信息、形成舆论。
              </p>
              
              <div className="space-y-4 mb-8">
                {[
                  { icon: Zap, text: '实时观察舆论传播路径' },
                  { icon: Users, text: '多分身互动对话模拟' },
                  { icon: TrendingUp, text: '情感分析和极化趋势' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center">
                      <item.icon className="w-4 h-4 text-indigo-600" />
                    </div>
                    <span className="text-slate-700">{item.text}</span>
                  </div>
                ))}
              </div>
              
              <Link
                href="/simulate"
                className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors"
              >
                开始模拟
                <ArrowRight className="w-4 h-4" />
              </Link>
            </motion.div>
          </div>

          {/* 右侧：动态可视化 */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="relative"
          >
            <div 
              className="relative rounded-2xl overflow-hidden shadow-2xl border border-slate-200 bg-white"
              onMouseEnter={() => setIsHovering(true)}
              onMouseLeave={() => setIsHovering(false)}
            >
              <canvas
                ref={canvasRef}
                className="w-full h-[400px] block"
                style={{ width: '100%', height: '400px' }}
              />
              
              {/* 悬浮提示 */}
              <div className="absolute bottom-4 left-4 right-4 flex justify-center">
                <div className="px-4 py-2 bg-white/90 backdrop-blur rounded-full text-sm text-slate-600 shadow-lg border">
                  {isHovering ? '悬停查看细节' : '鼠标悬停暂停动画'}
                </div>
              </div>
            </div>

            {/* 装饰元素 */}
            <div className="absolute -top-4 -right-4 w-24 h-24 bg-gradient-to-br from-indigo-400/20 to-purple-400/20 rounded-full blur-2xl" />
            <div className="absolute -bottom-4 -left-4 w-32 h-32 bg-gradient-to-br from-blue-400/20 to-indigo-400/20 rounded-full blur-2xl" />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
