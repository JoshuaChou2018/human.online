'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Brain, MessageCircle, Sparkles, Target, Heart, BookOpen, 
  Lightbulb, Zap, BarChart3, ChevronRight, Award, User, Lock, Shield
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { API_BASE_URL } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';

// MindWeave 特征类型
interface MindThreads {
  // 系统分身的六维数值格式
  rationality?: number;
  emotionality?: number;
  confidence?: number;
  openness?: number;
  analytical?: number;
  synthesis?: number;
  // 完整分身的复杂格式
  mindCore?: {
    thinkingFrameworks: string[];
    problemDecomposition: string;
    cognitivePreference: string;
    thinkingPatterns: string[];
    uniqueTraits: string[];
  };
  expressionStyle?: {
    tone: {
      formality: number;
      enthusiasm: number;
      directness: number;
    };
    sentenceStyle: {
      avgLength: number;
      complexity: number;
    };
    vocabulary: {
      technicalDensity: number;
      emotionalMarkers: string[];
      catchphrases: string[];
    };
  };
  decisionLogic?: {
    decisionPriorities: string[];
    riskApproach: string;
    timePreference: string;
    opportunityCostAwareness: string;
    decisionSpeed: string;
  };
  knowledgeAreas?: string[];
  valueSystem?: {
    coreValues: string[];
    moralBoundaries: string[];
    priorities: string[];
    antiPatterns: string[];
  };
  emotionalPattern?: {
    emotionalTone: string;
    emotionalIntensity: string;
    emotionalTriggers: string[];
    expressionStyle: string;
  };
}

interface IdentityCardData {
  // 基本信息系统分身可能没有 basicInfo
  basicInfo?: {
    name: string;
    description: string;
    type: string;
    createdAt: string;
  };
  // 系统分身直接有的字段
  archetype?: string;
  thinkingStyle?: string;
  speechPattern?: string;
  decisionTendency?: string;
  cognitiveBiases?: string;
  knowledgeDomains?: string[];
  // 完整分身的字段
  mindSummary?: {
    thinkingStyle: string;
    expressionStyle: string;
    decisionStyle: string;
    emotionalTone: string;
  };
  keyTraits?: string[];
  knowledgeTags?: string[];
  coreValues?: string[];
  stats?: {
    formality: number;
    enthusiasm: number;
    directness: number;
    complexity: number;
  };
}

// 隐私信息类型
interface PrivateInfoItem {
  category?: string;
  content?: string;
  trait?: string;
  evidence?: string;
  confidence?: number;
  sensitivity?: 'low' | 'medium' | 'high';
}

interface PrivateInfo {
  preferences: PrivateInfoItem[];
  background: PrivateInfoItem[];
  personalTraits: PrivateInfoItem[];
  sensitiveInfo: PrivateInfoItem[];
  summary: string;
  extractedAt?: string;
}

interface AvatarIdentity {
  mindThreads: MindThreads;
  identityCard: IdentityCardData;
  analyzedAt: string;
  isOwner: boolean;
  hasPrivateInfo: boolean;
  privateInfo?: PrivateInfo;
}

interface IdentityCardProps {
  avatarId: string;
  isOpen: boolean;
  onClose: () => void;
  color?: string;
}

// 安全访问辅助函数
const safeAccess = (obj: any, path: string, defaultValue: any = '') => {
  const keys = path.split('.');
  let result = obj;
  for (const key of keys) {
    if (result == null) return defaultValue;
    result = result[key];
  }
  return result ?? defaultValue;
};

const safeArray = (obj: any, path: string, defaultValue: any[] = []) => {
  const val = safeAccess(obj, path);
  return Array.isArray(val) ? val : defaultValue;
};

export function IdentityCard({ avatarId, isOpen, onClose, color = "from-indigo-500 to-purple-600" }: IdentityCardProps) {
  const [identity, setIdentity] = useState<AvatarIdentity | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'mind' | 'values' | 'private'>('overview');
  const { token } = useAuthStore();

  useEffect(() => {
    if (isOpen && avatarId) {
      loadIdentity();
    }
  }, [isOpen, avatarId]);

  const loadIdentity = async () => {
    setLoading(true);
    try {
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${API_BASE_URL}/avatars/${avatarId}/identity`, {
        headers,
      });
      
      if (response.ok) {
        const data = await response.json();
        setIdentity(data);
      }
    } catch (error) {
      console.error('Failed to load identity:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden shadow-2xl"
        >
          {loading ? (
            <div className="p-12 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
            </div>
          ) : identity ? (
            <>
              {/* Header */}
              <div className={cn("bg-gradient-to-br p-6 text-white relative", color)}>
                <button
                  onClick={onClose}
                  className="absolute top-4 right-4 p-2 bg-white/20 hover:bg-white/30 rounded-full transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
                
                <div className="flex items-center gap-4">
                  <div className="w-20 h-20 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-3xl font-bold">
                    {identity.identityCard?.basicInfo?.name?.charAt(0) || 
                     identity.identityCard?.archetype?.charAt(0) || '?'}
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold">
                      {identity.identityCard?.basicInfo?.name || 
                       identity.identityCard?.archetype || '未知分身'}
                    </h2>
                    <p className="text-white/80 text-sm mt-1">
                      {identity.identityCard?.basicInfo?.description || 
                       identity.identityCard?.thinkingStyle || 
                       '暂无描述'}
                    </p>
                    <div className="flex gap-2 mt-2">
                      <span className="px-2 py-0.5 bg-white/20 rounded text-xs">
                        {identity.identityCard?.basicInfo?.type === 'personal' ? '个人分身' : 
                         identity.identityCard?.basicInfo?.type === 'celebrity' ? '名人分身' : 
                         identity.identityCard?.basicInfo?.type === 'system' ? '系统分身' :
                         identity.identityCard?.archetype || '数字分身'}
                      </span>
                      <span className="px-2 py-0.5 bg-white/20 rounded text-xs">
                        MindWeave
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="border-b flex">
                {[
                  { id: 'overview', label: '概览', icon: User },
                  { id: 'mind', label: '思维', icon: Brain },
                  { id: 'values', label: '价值观', icon: Heart },
                  // 仅创建者可见的隐私标签
                  ...(identity.isOwner ? [{ id: 'private', label: '隐私', icon: Lock }] : []),
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={cn(
                      'flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors flex-1',
                      activeTab === tab.id 
                        ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50/50' 
                        : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                    )}
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                    {tab.id === 'private' && (
                      <span className="ml-1 w-2 h-2 bg-amber-500 rounded-full"></span>
                    )}
                  </button>
                ))}
              </div>

              {/* Content */}
              <div className="p-6 overflow-y-auto max-h-[50vh]">
                {activeTab === 'overview' && (
                  <OverviewTab identity={identity} />
                )}
                {activeTab === 'mind' && (
                  <MindTab mindThreads={identity.mindThreads} />
                )}
                {activeTab === 'values' && (
                  <ValuesTab mindThreads={identity.mindThreads} />
                )}
                {activeTab === 'private' && identity.isOwner && (
                  <PrivateTab privateInfo={identity.privateInfo} />
                )}
              </div>

              {/* Footer */}
              <div className="p-4 border-t bg-slate-50 flex justify-between items-center">
                <span className="text-xs text-slate-400">
                  基于 MindWeave 思维编织理论
                </span>
                <Button size="sm" onClick={onClose}>
                  关闭
                </Button>
              </div>
            </>
          ) : (
            <div className="p-12 text-center">
              <p className="text-slate-500">暂无身份卡信息</p>
              <Button onClick={onClose} className="mt-4">关闭</Button>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

function OverviewTab({ identity }: { identity: AvatarIdentity }) {
  const { identityCard } = identity;
  
  // 安全获取数组 - 兼容系统分身和普通分身的数据格式
  const keyTraits = identityCard?.keyTraits || 
                    (identityCard?.archetype ? [identityCard.archetype] : []);
  const knowledgeTags = identityCard?.knowledgeTags || 
                        identityCard?.knowledgeDomains || [];
  const coreValues = identityCard?.coreValues || 
                     (identityCard?.thinkingStyle ? [identityCard.thinkingStyle] : []);
  const stats = identityCard?.stats || { formality: 0.5, enthusiasm: 0.5, directness: 0.5, complexity: 0.5 };
  
  return (
    <div className="space-y-6">
      {/* 关键特质 */}
      <section>
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-500" />
          关键特质
        </h3>
        {keyTraits.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {keyTraits.map((trait, idx) => (
              <span 
                key={idx}
                className="px-3 py-1 bg-amber-50 text-amber-700 rounded-full text-sm border border-amber-200"
              >
                {trait}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-400">暂无特质数据</p>
        )}
      </section>

      {/* 知识领域 */}
      <section>
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-blue-500" />
          知识领域
        </h3>
        {knowledgeTags.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {knowledgeTags.map((tag, idx) => (
              <span 
                key={idx}
                className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm border border-blue-200"
              >
                {tag}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-400">暂无知识领域数据</p>
        )}
      </section>

      {/* 核心价值观 */}
      <section>
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Award className="w-4 h-4 text-purple-500" />
          核心价值观
        </h3>
        {coreValues.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {coreValues.map((value, idx) => (
              <span 
                key={idx}
                className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm border border-purple-200"
              >
                {value}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-400">暂无价值观数据</p>
        )}
      </section>

      {/* 风格雷达图简化版 */}
      <section>
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-green-500" />
          表达风格
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <StatBar label="正式程度" value={stats.formality ?? 0.5} color="bg-blue-500" />
          <StatBar label="热情程度" value={stats.enthusiasm ?? 0.5} color="bg-amber-500" />
          <StatBar label="直接程度" value={stats.directness ?? 0.5} color="bg-red-500" />
          <StatBar label="复杂程度" value={stats.complexity ?? 0.5} color="bg-purple-500" />
        </div>
      </section>
    </div>
  );
}

function MindTab({ mindThreads }: { mindThreads: MindThreads | undefined }) {
  // 检查是否是系统分身的六维数值格式
  const isSimpleFormat = mindThreads && 
    (mindThreads.rationality !== undefined || 
     mindThreads.analytical !== undefined);
  
  if (!mindThreads) {
    return (
      <div className="p-8 text-center text-slate-500">
        <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>暂无思维分析数据</p>
        <p className="text-sm mt-2">编织过程中可能未完成或数据不完整</p>
      </div>
    );
  }
  
  // 如果是系统分身的简单数值格式，显示六维图表
  if (isSimpleFormat) {
    return (
      <div className="space-y-6">
        <section>
          <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <Brain className="w-4 h-4 text-indigo-500" />
            六维思维特征
          </h3>
          <div className="bg-slate-50 rounded-lg p-4 space-y-4">
            <StatBar 
              label="理性程度" 
              value={mindThreads.rationality ?? 0.5} 
              color="bg-blue-500" 
            />
            <StatBar 
              label="情感程度" 
              value={mindThreads.emotionality ?? 0.5} 
              color="bg-pink-500" 
            />
            <StatBar 
              label="自信程度" 
              value={mindThreads.confidence ?? 0.5} 
              color="bg-amber-500" 
            />
            <StatBar 
              label="开放程度" 
              value={mindThreads.openness ?? 0.5} 
              color="bg-green-500" 
            />
            <StatBar 
              label="分析能力" 
              value={mindThreads.analytical ?? 0.5} 
              color="bg-purple-500" 
            />
            <StatBar 
              label="综合能力" 
              value={mindThreads.synthesis ?? 0.5} 
              color="bg-indigo-500" 
            />
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 思维内核 */}
      <section>
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-amber-500" />
          思维内核
        </h3>
        <div className="bg-slate-50 rounded-lg p-4 space-y-3">
          <div>
            <span className="text-xs text-slate-500">认知偏好</span>
            <p className="text-sm text-slate-800">{safeAccess(mindThreads, 'mindCore.cognitivePreference', '平衡型')}</p>
          </div>
          <div>
            <span className="text-xs text-slate-500">问题分解方式</span>
            <p className="text-sm text-slate-800">{safeAccess(mindThreads, 'mindCore.problemDecomposition', '分步骤分析')}</p>
          </div>
          <div>
            <span className="text-xs text-slate-500">思维框架</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {safeArray(mindThreads, 'mindCore.thinkingFrameworks').map((fw, idx) => (
                <span key={idx} className="px-2 py-0.5 bg-white rounded text-xs border">
                  {fw}
                </span>
              ))}
            </div>
          </div>
          <div>
            <span className="text-xs text-slate-500">思维特质</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {safeArray(mindThreads, 'mindCore.uniqueTraits').map((trait, idx) => (
                <span key={idx} className="px-2 py-0.5 bg-amber-50 text-amber-700 rounded text-xs">
                  {trait}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 决策逻辑 */}
      <section>
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Target className="w-4 h-4 text-blue-500" />
          决策逻辑
        </h3>
        <div className="bg-slate-50 rounded-lg p-4 space-y-3">
          <div>
            <span className="text-xs text-slate-500">决策优先级</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {safeArray(mindThreads, 'decisionLogic.decisionPriorities').map((p, idx) => (
                <span key={idx} className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">
                  {p}
                </span>
              ))}
            </div>
          </div>
          <div>
            <span className="text-xs text-slate-500">风险处理方式</span>
            <p className="text-sm text-slate-800">{safeAccess(mindThreads, 'decisionLogic.riskApproach', '谨慎评估')}</p>
          </div>
          <div>
            <span className="text-xs text-slate-500">决策速度</span>
            <p className="text-sm text-slate-800">{safeAccess(mindThreads, 'decisionLogic.decisionSpeed', '深思熟虑')}</p>
          </div>
        </div>
      </section>

      {/* 情感模式 */}
      <section>
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Zap className="w-4 h-4 text-red-500" />
          情感模式
        </h3>
        <div className="bg-slate-50 rounded-lg p-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <span className="text-xs text-slate-500">情感基调</span>
              <p className="text-sm text-slate-800">{safeAccess(mindThreads, 'emotionalPattern.emotionalTone', '平和')}</p>
            </div>
            <div>
              <span className="text-xs text-slate-500">情感强度</span>
              <p className="text-sm text-slate-800">{safeAccess(mindThreads, 'emotionalPattern.emotionalIntensity', '中等')}</p>
            </div>
          </div>
          <div>
            <span className="text-xs text-slate-500">情感触发点</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {safeArray(mindThreads, 'emotionalPattern.emotionalTriggers').map((trigger, idx) => (
                <span key={idx} className="px-2 py-0.5 bg-red-50 text-red-700 rounded text-xs">
                  {trigger}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function ValuesTab({ mindThreads }: { mindThreads: MindThreads | undefined }) {
  // 检查是否是系统分身的六维数值格式
  const isSimpleFormat = mindThreads && 
    (mindThreads.rationality !== undefined || 
     mindThreads.analytical !== undefined);
  
  if (!mindThreads) {
    return (
      <div className="p-8 text-center text-slate-500">
        <Heart className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>暂无价值观数据</p>
        <p className="text-sm mt-2">编织过程中可能未完成或数据不完整</p>
      </div>
    );
  }
  
  // 如果是系统分身的简单数值格式，显示简化信息
  if (isSimpleFormat) {
    return (
      <div className="p-8 text-center text-slate-500">
        <Heart className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>系统内置分身</p>
        <p className="text-sm mt-2">该分身为系统预设，价值观数据已内置于系统提示词中</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 核心价值观 */}
      <section>
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Award className="w-4 h-4 text-purple-500" />
          核心价值观
        </h3>
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex flex-wrap gap-2">
            {safeArray(mindThreads, 'valueSystem.coreValues').map((value, idx) => (
              <span 
                key={idx}
                className="px-3 py-1.5 bg-white text-purple-700 rounded-lg text-sm font-medium shadow-sm"
              >
                {value}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* 优先事项 */}
      <section>
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Target className="w-4 h-4 text-blue-500" />
          人生优先事项
        </h3>
        <div className="space-y-2">
          {safeArray(mindThreads, 'valueSystem.priorities').map((priority, idx) => (
            <div key={idx} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
              <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold">
                {idx + 1}
              </span>
              <span className="text-slate-800">{priority}</span>
            </div>
          ))}
        </div>
      </section>

      {/* 道德底线 */}
      <section>
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Heart className="w-4 h-4 text-red-500" />
          道德底线
        </h3>
        <div className="flex flex-wrap gap-2">
          {safeArray(mindThreads, 'valueSystem.moralBoundaries').map((boundary, idx) => (
            <span 
              key={idx}
              className="px-3 py-1.5 bg-red-50 text-red-700 rounded-lg text-sm border border-red-200"
            >
              {boundary}
            </span>
          ))}
        </div>
      </section>

      {/* 反对的行为 */}
      <section>
        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <X className="w-4 h-4 text-slate-500" />
          明确反对
        </h3>
        <div className="flex flex-wrap gap-2">
          {safeArray(mindThreads, 'valueSystem.antiPatterns').map((pattern, idx) => (
            <span 
              key={idx}
              className="px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg text-sm"
            >
              {pattern}
            </span>
          ))}
        </div>
      </section>
    </div>
  );
}


function PrivateTab({ privateInfo }: { privateInfo: PrivateInfo | undefined }) {
  if (!privateInfo || (!privateInfo.preferences?.length && !privateInfo.background?.length)) {
    return (
      <div className="p-8 text-center">
        <Shield className="w-12 h-12 mx-auto mb-4 text-slate-300" />
        <p className="text-slate-500 mb-2">暂无隐私信息</p>
        <p className="text-sm text-slate-400">
          系统从你上传的数据中提取的个人偏好、背景等信息将显示在此
        </p>
      </div>
    );
  }

  // 敏感度颜色映射
  const sensitivityColors = {
    low: 'bg-green-50 text-green-700 border-green-200',
    medium: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    high: 'bg-red-50 text-red-700 border-red-200',
  };

  return (
    <div className="space-y-6">
      {/* 隐私警示 */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
        <Shield className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
        <div>
          <h4 className="text-sm font-medium text-amber-800">隐私信息保护</h4>
          <p className="text-xs text-amber-700 mt-1">
            以下信息仅你可见，其他用户无法访问。这些内容来自你上传的数据，系统自动提取的个人偏好、背景等。
          </p>
        </div>
      </div>

      {/* 摘要 */}
      {privateInfo.summary && (
        <section>
          <h3 className="text-sm font-semibold text-slate-900 mb-3">摘要</h3>
          <p className="text-sm text-slate-600 bg-slate-50 p-4 rounded-lg">
            {privateInfo.summary}
          </p>
        </section>
      )}

      {/* 个人偏好 */}
      {privateInfo.preferences && privateInfo.preferences.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-pink-500" />
            个人偏好
          </h3>
          <div className="space-y-2">
            {privateInfo.preferences.map((pref, idx) => (
              <div key={idx} className="bg-pink-50 rounded-lg p-3 border border-pink-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-pink-600 uppercase">
                    {pref.category || '偏好'}
                  </span>
                  {pref.confidence !== undefined && (
                    <span className="text-xs text-pink-400">
                      置信度: {Math.round(pref.confidence * 100)}%
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-800 mt-1">{pref.content}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 背景信息 */}
      {privateInfo.background && privateInfo.background.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-blue-500" />
            背景情况
          </h3>
          <div className="space-y-2">
            {privateInfo.background.map((bg, idx) => (
              <div key={idx} className="bg-blue-50 rounded-lg p-3 border border-blue-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-blue-600 uppercase">
                    {bg.category || '背景'}
                  </span>
                  {bg.confidence !== undefined && (
                    <span className="text-xs text-blue-400">
                      置信度: {Math.round(bg.confidence * 100)}%
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-800 mt-1">{bg.content}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 个人特质 */}
      {privateInfo.personalTraits && privateInfo.personalTraits.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <User className="w-4 h-4 text-purple-500" />
            个人特质
          </h3>
          <div className="flex flex-wrap gap-2">
            {privateInfo.personalTraits.map((trait, idx) => (
              <span 
                key={idx}
                className="px-3 py-1.5 bg-purple-50 text-purple-700 rounded-lg text-sm border border-purple-200"
                title={trait.evidence}
              >
                {trait.trait}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* 敏感信息 */}
      {privateInfo.sensitiveInfo && privateInfo.sensitiveInfo.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <Lock className="w-4 h-4 text-red-500" />
            敏感信息
          </h3>
          <div className="space-y-2">
            {privateInfo.sensitiveInfo.map((info, idx) => (
              <div 
                key={idx} 
                className={`rounded-lg p-3 border ${sensitivityColors[info.sensitivity || 'medium']}`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium uppercase">
                    {info.category}
                  </span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    info.sensitivity === 'high' ? 'bg-red-200 text-red-800' : 
                    info.sensitivity === 'low' ? 'bg-green-200 text-green-800' : 
                    'bg-yellow-200 text-yellow-800'
                  }`}>
                    {info.sensitivity === 'high' ? '高敏感' : 
                     info.sensitivity === 'low' ? '低敏感' : '中敏感'}
                  </span>
                </div>
                <p className="text-sm mt-1">{info.content}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function StatBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-slate-600">
        <span>{label}</span>
        <span>{Math.round(value * 100)}%</span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all`}
          style={{ width: `${value * 100}%` }}
        />
      </div>
    </div>
  );
}

// 简化的身份卡按钮组件
export function IdentityCardButton({ 
  avatarId, 
  color = "from-indigo-500 to-purple-600",
  size = "md"
}: { 
  avatarId: string; 
  color?: string;
  size?: "sm" | "md" | "lg";
}) {
  const [isOpen, setIsOpen] = useState(false);

  const sizeClasses = {
    sm: "p-1.5",
    md: "p-2", 
    lg: "p-3"
  };

  const iconSizes = {
    sm: "w-3.5 h-3.5",
    md: "w-4 h-4",
    lg: "w-5 h-5"
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          "rounded-lg bg-gradient-to-br text-white hover:opacity-90 transition-all shadow-sm",
          color,
          sizeClasses[size]
        )}
        title="查看身份卡"
      >
        <Award className={iconSizes[size]} />
      </button>

      <IdentityCard 
        avatarId={avatarId}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        color={color}
      />
    </>
  );
}
