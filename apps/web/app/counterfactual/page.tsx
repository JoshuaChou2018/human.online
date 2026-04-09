'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Play,
  History,
  TrendingUp,
  MessageCircle,
  Users,
  Zap,
  ArrowLeft,
  Loader2,
  AlertTriangle,
  Brain,
  Thermometer,
  Scale,
  Clock,
  ChevronRight,
  Share2,
  Trash2,
  RefreshCw,
  Flame,
  Wind,
  Anchor,
  Radio
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiRequest, useAuthStore } from '@/lib/auth';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

// 预设场景
const PRESETS = [
  {
    key: 'trump_iran',
    title: '特朗普对伊朗军事行动',
    description: '特朗普宣布将对伊朗核设施采取预防性军事打击',
    icon: AlertTriangle,
    color: 'from-red-500 to-orange-500',
    sentiment: -0.6,
    heat: 0.9
  },
  {
    key: 'ai_consciousness',
    title: 'AI意识觉醒',
    description: 'OpenAI宣布其最新模型展现出自主意识和情感反应',
    icon: Brain,
    color: 'from-purple-500 to-pink-500',
    sentiment: 0.2,
    heat: 0.95
  },
  {
    key: 'economic_crisis',
    title: '全球金融危机',
    description: '美股三大指数单日暴跌超过20%，触发全球金融海啸',
    icon: TrendingUp,
    color: 'from-red-600 to-rose-600',
    sentiment: -0.9,
    heat: 0.95
  },
  {
    key: 'alien_contact',
    title: '外星文明接触',
    description: 'NASA宣布收到来自比邻星系的结构化信号',
    icon: Radio,
    color: 'from-blue-500 to-cyan-500',
    sentiment: 0.6,
    heat: 1.0
  }
];

interface SimulationRound {
  round_number: number;
  phase: string;
  topic: string;
  sentiment_score: number;
  heat_score: number;
  polarization_index: number;
  stance_distribution: {
    support: number;
    oppose: number;
    neutral: number;
  };
  messages: Array<{
    id: string;
    avatar_id: string;
    content: string;
    sentiment: number;
    stance: string;
    response_type: string;
    thinking_process?: string;
  }>;
}

interface Scenario {
  id: string;
  title: string;
  description: string;
  scenario_type: string;
  trigger_event: string;
  trigger_source: string;
  status: string;
  max_rounds: number;
  initial_sentiment: number;
  initial_heat: number;
  final_summary?: string;
  key_findings?: string[];
  created_at: string;
  completed_at?: string;
  rounds?: SimulationRound[];
}

export default function CounterfactualPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [customEvent, setCustomEvent] = useState('');
  const [maxRounds, setMaxRounds] = useState(5);
  const [activeScenario, setActiveScenario] = useState<Scenario | null>(null);
  const [activeTab, setActiveTab] = useState<'setup' | 'results'>('setup');
  const [currentRound, setCurrentRound] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);

  // 加载历史场景
  const loadScenarios = useCallback(async () => {
    try {
      const data = await apiRequest('/api/v1/counterfactual/scenarios');
      setScenarios(data);
    } catch (error) {
      console.error('Failed to load scenarios:', error);
      toast.error('加载历史场景失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadScenarios();
    }
  }, [isAuthenticated, loadScenarios]);

  // 自动播放轮次
  useEffect(() => {
    if (isPlaying && activeScenario?.rounds) {
      const maxRound = activeScenario.rounds.length;
      if (currentRound >= maxRound) {
        setIsPlaying(false);
        return;
      }
      
      const timer = setTimeout(() => {
        setCurrentRound(prev => prev + 1);
      }, 2000);
      
      return () => clearTimeout(timer);
    }
  }, [isPlaying, currentRound, activeScenario]);

  // 创建新场景
  const handleCreateScenario = async () => {
    if (!selectedPreset && !customEvent.trim()) {
      toast.error('请选择预设场景或输入自定义事件');
      return;
    }

    setCreating(true);
    try {
      const result = await apiRequest('/api/v1/counterfactual/scenarios', {
        method: 'POST',
        body: JSON.stringify({
          preset: selectedPreset || undefined,
          custom_event: customEvent.trim() || undefined,
          max_rounds: maxRounds
        })
      });

      toast.success('反事实模拟运行完成！');
      
      // 加载详细结果
      const detail = await apiRequest(`/api/v1/counterfactual/scenarios/${result.scenario_id}`);
      setActiveScenario(detail);
      setActiveTab('results');
      setCurrentRound(1);
      
      // 刷新列表
      loadScenarios();
    } catch (error) {
      console.error('Failed to create scenario:', error);
      toast.error('模拟运行失败');
    } finally {
      setCreating(false);
    }
  };

  // 删除场景
  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('确定要删除这个模拟场景吗？')) return;

    try {
      await apiRequest(`/api/v1/counterfactual/scenarios/${id}`, {
        method: 'DELETE'
      });
      toast.success('已删除');
      loadScenarios();
      if (activeScenario?.id === id) {
        setActiveScenario(null);
        setActiveTab('setup');
      }
    } catch (error) {
      toast.error('删除失败');
    }
  };

  // 渲染情绪仪表盘
  const renderSentimentGauge = (value: number) => {
    const percentage = (value + 1) / 2 * 100;
    const color = value > 0.3 ? 'bg-green-500' : value < -0.3 ? 'bg-red-500' : 'bg-yellow-500';
    const label = value > 0.3 ? '正面' : value < -0.3 ? '负面' : '中性';
    
    return (
      <div className="flex items-center gap-3">
        <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
          <div 
            className={cn("h-full transition-all duration-500", color)}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className={cn("text-sm font-medium", 
          value > 0.3 ? 'text-green-600' : value < -0.3 ? 'text-red-600' : 'text-yellow-600'
        )}>
          {label} ({value.toFixed(2)})
        </span>
      </div>
    );
  };

  // 渲染热度仪表盘
  const renderHeatGauge = (value: number) => {
    return (
      <div className="flex items-center gap-2">
        <Flame className={cn("w-5 h-5", 
          value > 0.7 ? 'text-red-500' : value > 0.4 ? 'text-orange-500' : 'text-slate-400'
        )} />
        <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
          <div 
            className={cn("h-full transition-all duration-500",
              value > 0.7 ? 'bg-red-500' : value > 0.4 ? 'bg-orange-500' : 'bg-slate-400'
            )}
            style={{ width: `${value * 100}%` }}
          />
        </div>
        <span className="text-sm text-slate-600">{(value * 100).toFixed(0)}%</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.push('/')}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-lg">反事实模拟</h1>
                <p className="text-xs text-slate-500">探索假设性事件的蝴蝶效应</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant={activeTab === 'setup' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('setup')}
            >
              <Zap className="w-4 h-4 mr-1" />
              新建模拟
            </Button>
            <Button
              variant={activeTab === 'results' ? 'default' : 'outline'}
              size="sm"
              onClick={() => activeScenario && setActiveTab('results')}
              disabled={!activeScenario}
            >
              <History className="w-4 h-4 mr-1" />
              查看结果
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'setup' ? (
          <div className="grid grid-cols-3 gap-6">
            {/* 左侧：预设场景 */}
            <div className="col-span-2 space-y-6">
              <div>
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Anchor className="w-5 h-5 text-indigo-600" />
                  选择预设场景
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  {PRESETS.map((preset) => (
                    <Card
                      key={preset.key}
                      className={cn(
                        "p-4 cursor-pointer transition-all hover:shadow-lg",
                        selectedPreset === preset.key 
                          ? "ring-2 ring-indigo-500 border-indigo-500" 
                          : "hover:border-indigo-300"
                      )}
                      onClick={() => {
                        setSelectedPreset(preset.key);
                        setCustomEvent('');
                      }}
                    >
                      <div className="flex items-start gap-3">
                        <div className={cn(
                          "w-10 h-10 rounded-lg bg-gradient-to-br flex items-center justify-center shrink-0",
                          preset.color
                        )}>
                          <preset.icon className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-slate-900">{preset.title}</h3>
                          <p className="text-sm text-slate-500 mt-1 line-clamp-2">
                            {preset.description}
                          </p>
                          <div className="flex items-center gap-3 mt-2 text-xs">
                            <span className="text-slate-400">
                              情绪: {preset.sentiment > 0 ? '+' : ''}{preset.sentiment}
                            </span>
                            <span className="text-slate-400">
                              热度: {(preset.heat * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>

              {/* 自定义事件 */}
              <div>
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Wind className="w-5 h-5 text-indigo-600" />
                  或输入自定义事件
                </h2>
                <Card className="p-4">
                  <textarea
                    value={customEvent}
                    onChange={(e) => {
                      setCustomEvent(e.target.value);
                      if (e.target.value) setSelectedPreset(null);
                    }}
                    placeholder="例如：明天太阳突然熄灭，人类还有多长时间？..."
                    className="w-full h-24 p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                </Card>
              </div>

              {/* 模拟参数 */}
              <div>
                <h2 className="text-lg font-semibold mb-4">模拟参数</h2>
                <Card className="p-4">
                  <div className="flex items-center gap-4">
                    <label className="text-sm font-medium">模拟轮数:</label>
                    <input
                      type="range"
                      min={3}
                      max={10}
                      value={maxRounds}
                      onChange={(e) => setMaxRounds(Number(e.target.value))}
                      className="flex-1 max-w-xs"
                    />
                    <span className="text-sm font-bold text-indigo-600 w-8">{maxRounds}</span>
                    <span className="text-xs text-slate-500">轮</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    轮数越多，话题演变越深入，但模拟时间也会相应增加
                  </p>
                </Card>
              </div>
            </div>

            {/* 右侧：历史记录 */}
            <div>
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <History className="w-5 h-5 text-indigo-600" />
                历史模拟
              </h2>
              <div className="space-y-3">
                {scenarios.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <History className="w-12 h-12 mx-auto mb-3 text-slate-200" />
                    <p className="text-sm">暂无历史记录</p>
                  </div>
                ) : (
                  scenarios.map((scenario) => (
                    <Card
                      key={scenario.id}
                      className="p-3 cursor-pointer hover:border-indigo-300 transition-colors"
                      onClick={() => {
                        setActiveScenario(scenario);
                        setActiveTab('results');
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-sm truncate">{scenario.title}</h4>
                          <p className="text-xs text-slate-500 mt-1">
                            {new Date(scenario.created_at).toLocaleDateString('zh-CN')}
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant={scenario.status === 'completed' ? 'default' : 'secondary'} className="text-xs">
                              {scenario.status === 'completed' ? '已完成' : scenario.status}
                            </Badge>
                            <span className="text-xs text-slate-400">
                              {scenario.max_rounds}轮
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={(e) => handleDelete(scenario.id, e)}
                          className="p-1 text-slate-400 hover:text-red-500 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </Card>
                  ))
                )}
              </div>
            </div>

            {/* 开始按钮 */}
            <div className="col-span-3">
              <Button
                size="lg"
                className="w-full"
                onClick={handleCreateScenario}
                disabled={creating || (!selectedPreset && !customEvent.trim())}
              >
                {creating ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    正在运行模拟...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5 mr-2" />
                    开始反事实模拟
                  </>
                )}
              </Button>
            </div>
          </div>
        ) : activeScenario ? (
          <div className="space-y-6">
            {/* 场景标题 */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold">{activeScenario.title}</h2>
                <p className="text-slate-500 mt-1">{activeScenario.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsPlaying(!isPlaying)}
                >
                  {isPlaying ? '暂停' : '播放演变'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveTab('setup')}
                >
                  <RefreshCw className="w-4 h-4 mr-1" />
                  新建
                </Button>
              </div>
            </div>

            {/* 触发事件卡片 */}
            <Card className="p-4 bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-amber-500 flex items-center justify-center shrink-0">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm font-medium text-amber-800">触发事件</p>
                  <p className="text-slate-700 mt-1">{activeScenario.trigger_event}</p>
                  <p className="text-xs text-slate-500 mt-1">来源: {activeScenario.trigger_source}</p>
                </div>
              </div>
            </Card>

            {/* 演变时间线 */}
            {activeScenario.rounds && activeScenario.rounds.length > 0 && (
              <div className="space-y-4">
                {/* 进度控制 */}
                <div className="flex items-center gap-4 bg-white p-4 rounded-lg border">
                  <span className="text-sm font-medium">轮次:</span>
                  <input
                    type="range"
                    min={1}
                    max={activeScenario.rounds.length}
                    value={currentRound}
                    onChange={(e) => {
                      setCurrentRound(Number(e.target.value));
                      setIsPlaying(false);
                    }}
                    className="flex-1"
                  />
                  <span className="text-sm text-slate-600 w-16">
                    {currentRound} / {activeScenario.rounds.length}
                  </span>
                </div>

                {/* 当前轮次详情 */}
                {(() => {
                  const round = activeScenario.rounds![currentRound - 1];
                  return (
                    <div className="grid grid-cols-3 gap-6">
                      {/* 左侧：舆论指标 */}
                      <div className="space-y-4">
                        <Card className="p-4">
                          <h3 className="font-medium mb-4 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-indigo-600" />
                            第 {round.round_number} 轮：{round.phase}
                          </h3>
                          
                          <div className="space-y-4">
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-slate-600 flex items-center gap-1">
                                  <Scale className="w-4 h-4" />
                                  整体情绪
                                </span>
                              </div>
                              {renderSentimentGauge(round.sentiment_score)}
                            </div>

                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-slate-600 flex items-center gap-1">
                                  <Thermometer className="w-4 h-4" />
                                  讨论热度
                                </span>
                              </div>
                              {renderHeatGauge(round.heat_score)}
                            </div>

                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-slate-600">立场分布</span>
                              </div>
                              <div className="flex h-2 rounded-full overflow-hidden">
                                <div 
                                  className="bg-green-500" 
                                  style={{ width: `${(round.stance_distribution?.support || 0) * 100}%` }}
                                />
                                <div 
                                  className="bg-red-500" 
                                  style={{ width: `${(round.stance_distribution?.oppose || 0) * 100}%` }}
                                />
                                <div 
                                  className="bg-slate-300" 
                                  style={{ width: `${(round.stance_distribution?.neutral || 0) * 100}%` }}
                                />
                              </div>
                              <div className="flex justify-between text-xs mt-1">
                                <span className="text-green-600">
                                  支持 {Math.round((round.stance_distribution?.support || 0) * 100)}%
                                </span>
                                <span className="text-red-600">
                                  反对 {Math.round((round.stance_distribution?.oppose || 0) * 100)}%
                                </span>
                                <span className="text-slate-500">
                                  中立 {Math.round((round.stance_distribution?.neutral || 0) * 100)}%
                                </span>
                              </div>
                            </div>
                          </div>
                        </Card>

                        {/* 当前话题 */}
                        <Card className="p-4">
                          <h4 className="text-sm font-medium mb-2">当前讨论话题</h4>
                          <p className="text-slate-700">{round.topic}</p>
                        </Card>
                      </div>

                      {/* 右侧：消息流 */}
                      <div className="col-span-2">
                        <Card className="p-4 h-[600px] overflow-auto">
                          <h3 className="font-medium mb-4 flex items-center gap-2">
                            <MessageCircle className="w-4 h-4 text-indigo-600" />
                            分身讨论 ({round.messages?.length || 0})
                          </h3>
                          
                          <div className="space-y-3">
                            {round.messages?.map((msg, idx) => (
                              <motion.div
                                key={msg.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.1 }}
                                className={cn(
                                  "p-3 rounded-lg border",
                                  msg.stance === 'support' ? 'bg-green-50 border-green-200' :
                                  msg.stance === 'oppose' ? 'bg-red-50 border-red-200' :
                                  'bg-slate-50 border-slate-200'
                                )}
                              >
                                <div className="flex items-start gap-3">
                                  <div className={cn(
                                    "w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0",
                                    msg.stance === 'support' ? 'bg-green-500' :
                                    msg.stance === 'oppose' ? 'bg-red-500' :
                                    'bg-slate-500'
                                  )}>
                                    {msg.content.charAt(0)}
                                  </div>
                                  <div className="flex-1">
                                    <p className="text-slate-800">{msg.content}</p>
                                    <div className="flex items-center gap-3 mt-2">
                                      <Badge variant="outline" className="text-xs">
                                        {msg.response_type}
                                      </Badge>
                                      <span className={cn("text-xs",
                                        msg.sentiment > 0 ? 'text-green-600' :
                                        msg.sentiment < 0 ? 'text-red-600' :
                                        'text-slate-500'
                                      )}>
                                        情绪: {msg.sentiment.toFixed(2)}
                                      </span>
                                      {msg.thinking_process && (
                                        <span className="text-xs text-slate-400 truncate max-w-xs">
                                          💭 {msg.thinking_process}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </motion.div>
                            ))}
                          </div>
                        </Card>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* 最终总结 */}
            {activeScenario.final_summary && (
              <Card className="p-6 bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-indigo-600" />
                  模拟总结
                </h3>
                <p className="text-slate-700 whitespace-pre-line">{activeScenario.final_summary}</p>
                
                {activeScenario.key_findings && (
                  <div className="mt-4 space-y-2">
                    <p className="text-sm font-medium text-slate-600">关键发现:</p>
                    <ul className="list-disc list-inside space-y-1">
                      {activeScenario.key_findings.map((finding, idx) => (
                        <li key={idx} className="text-sm text-slate-600">{finding}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Card>
            )}
          </div>
        ) : null}
      </main>
    </div>
  );
}
