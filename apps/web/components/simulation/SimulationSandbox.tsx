'use client';

import { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, FastForward, BarChart3, Share2, MessageCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { SimulationResult, VisualizationData, Avatar } from '@/types';
import { cn } from '@/lib/utils';
import { SocialNetworkGraph } from './SocialNetworkGraph';
import { SentimentTimeline } from './SentimentTimeline';
import { ReactionStats } from './ReactionStats';

interface SimulationSandboxProps {
  initialAvatars: Avatar[];
  onRunSimulation: (message: string) => Promise<{
    result: SimulationResult;
    visualization: VisualizationData;
  }>;
}

export function SimulationSandbox({
  initialAvatars,
  onRunSimulation,
}: SimulationSandboxProps) {
  const [message, setMessage] = useState('');
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationStep, setSimulationStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [visualization, setVisualization] = useState<VisualizationData | null>(null);
  const [activeTab, setActiveTab] = useState<'network' | 'timeline' | 'stats'>('network');
  
  const playIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 自动播放模拟
  useEffect(() => {
    if (isPlaying && result) {
      playIntervalRef.current = setInterval(() => {
        setSimulationStep((prev) => {
          if (prev >= (result.propagationSteps || 0)) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 800);
    } else {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current);
      }
    }

    return () => {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current);
      }
    };
  }, [isPlaying, result]);

  const handleRunSimulation = async () => {
    if (!message.trim()) return;
    
    setIsSimulating(true);
    setSimulationStep(0);
    setResult(null);
    setVisualization(null);
    
    try {
      const data = await onRunSimulation(message);
      setResult(data.result);
      setVisualization(data.visualization);
    } catch (error) {
      console.error('Simulation failed:', error);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleReset = () => {
    setSimulationStep(0);
    setIsPlaying(false);
  };

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* 顶部输入区 */}
      <div className="bg-white border-b px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <MessageCircle className="w-5 h-5 text-indigo-500" />
            社会模拟沙盒
          </h2>
          
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <span>参与者:</span>
              <div className="flex gap-1">
                {initialAvatars.slice(0, 5).map((avatar) => (
                  <span
                    key={avatar.id}
                    className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full text-xs"
                  >
                    {avatar.name}
                  </span>
                ))}
                {initialAvatars.length > 5 && (
                  <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full text-xs">
                    +{initialAvatars.length - 5}
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex gap-3">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="输入你想测试的言论，观察在数字社会中的传播效果..."
                className="flex-1 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                rows={2}
              />
              <button
                onClick={handleRunSimulation}
                disabled={!message.trim() || isSimulating}
                className={cn(
                  'px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2',
                  message.trim() && !isSimulating
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-500/25'
                    : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                )}
              >
                {isSimulating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    模拟中...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    运行模拟
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 主要内容区 */}
      {result && visualization ? (
        <div className="flex-1 flex overflow-hidden">
          {/* 左侧可视化 */}
          <div className="flex-1 flex flex-col">
            {/* 标签栏 */}
            <div className="flex items-center justify-between px-6 py-3 bg-white border-b">
              <div className="flex gap-1">
                {[
                  { id: 'network', label: '传播网络', icon: Share2 },
                  { id: 'timeline', label: '情感演化', icon: BarChart3 },
                  { id: 'stats', label: '统计指标', icon: BarChart3 },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={cn(
                      'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                      activeTab === tab.id
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-slate-600 hover:bg-slate-50'
                    )}
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                ))}
              </div>
              
              {/* 播放控制 */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleReset}
                  className="p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
                  title="重置"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className={cn(
                    'p-2 rounded-lg transition-colors',
                    isPlaying
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-indigo-100 text-indigo-700'
                  )}
                  title={isPlaying ? '暂停' : '播放'}
                >
                  {isPlaying ? (
                    <Pause className="w-4 h-4" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                </button>
                <div className="flex items-center gap-2 ml-2 px-3 py-1.5 bg-slate-100 rounded-lg">
                  <FastForward className="w-3 h-3 text-slate-500" />
                  <span className="text-xs font-medium text-slate-600">
                    第 {simulationStep} / {result.propagationSteps} 层
                  </span>
                </div>
              </div>
            </div>

            {/* 可视化内容 */}
            <div className="flex-1 p-6 overflow-hidden">
              <AnimatePresence mode="wait">
                {activeTab === 'network' && (
                  <motion.div
                    key="network"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="h-full"
                  >
                    <SocialNetworkGraph
                      data={visualization}
                      currentStep={simulationStep}
                      isPlaying={isPlaying}
                    />
                  </motion.div>
                )}
                
                {activeTab === 'timeline' && (
                  <motion.div
                    key="timeline"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="h-full"
                  >
                    <SentimentTimeline
                      data={visualization.timeline}
                      currentStep={simulationStep}
                    />
                  </motion.div>
                )}
                
                {activeTab === 'stats' && (
                  <motion.div
                    key="stats"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="h-full"
                  >
                    <ReactionStats
                      result={result}
                      distribution={visualization}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* 右侧信息面板 */}
          <div className="w-80 bg-white border-l overflow-y-auto">
            <div className="p-4 space-y-6">
              {/* 关键指标 */}
              <div>
                <h3 className="text-sm font-semibold text-slate-900 mb-3">传播效果</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-500">触达人数</p>
                    <p className="text-2xl font-bold text-indigo-600">{result.totalReach}</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-500">传播深度</p>
                    <p className="text-2xl font-bold text-indigo-600">{result.propagationSteps}</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-500">社区极化</p>
                    <p className={cn(
                      'text-2xl font-bold',
                      result.polarization > 0.5 ? 'text-red-500' : 'text-green-500'
                    )}>
                      {(result.polarization * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-500">关键影响者</p>
                    <p className="text-lg font-bold text-indigo-600">
                      {result.keyInfluencers.length}
                    </p>
                  </div>
                </div>
              </div>

              {/* 反应分布 */}
              <div>
                <h3 className="text-sm font-semibold text-slate-900 mb-3">反应分布</h3>
                <div className="space-y-2">
                  {Object.entries(result.reactionDistribution).map(([type, count]) => (
                    <div key={type} className="flex items-center gap-2">
                      <div className={cn(
                        'w-2 h-2 rounded-full',
                        type === 'support' && 'bg-green-400',
                        type === 'oppose' && 'bg-red-400',
                        type === 'neutral' && 'bg-slate-300',
                        type === 'amplify' && 'bg-amber-400',
                        type === 'question' && 'bg-blue-400',
                        type === 'ignore' && 'bg-gray-200'
                      )} />
                      <span className="text-sm text-slate-600 flex-1 capitalize">{type}</span>
                      <span className="text-sm font-medium text-slate-900">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 关键影响者 */}
              <div>
                <h3 className="text-sm font-semibold text-slate-900 mb-3">关键影响者</h3>
                <div className="space-y-2">
                  {result.keyInfluencers.slice(0, 5).map((id, index) => {
                    const avatar = initialAvatars.find((a) => a.id === id);
                    return (
                      <div
                        key={id}
                        className="flex items-center gap-3 p-2 bg-slate-50 rounded-lg"
                      >
                        <span className="text-xs font-medium text-slate-400 w-4">
                          {index + 1}
                        </span>
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-xs font-medium">
                          {avatar?.name.charAt(0) || '?'}
                        </div>
                        <span className="text-sm text-slate-700">{avatar?.name || id}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-slate-400">
          <div className="w-24 h-24 rounded-full bg-slate-100 flex items-center justify-center mb-4">
            <Share2 className="w-10 h-10 opacity-50" />
          </div>
          <h3 className="text-lg font-medium text-slate-600 mb-2">准备开始模拟</h3>
          <p className="text-sm text-slate-400 max-w-md text-center">
            输入一条言论，观察它如何在这个由数字分身构成的社会中传播，
            了解不同立场和情绪下的反应模式
          </p>
        </div>
      )}
    </div>
  );
}
