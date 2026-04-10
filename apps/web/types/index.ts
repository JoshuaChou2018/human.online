// 用户类型
export interface User {
  id: string;
  email: string;
  username: string;
  avatar: string;
  createdAt: string;
}

// 数字分身类型
export type AvatarType = 'personal' | 'celebrity' | 'system';
export type AvatarStatus = 'draft' | 'weaving' | 'ready' | 'archived';

// 六维思维线索
export interface MindThreads {
  mindCore: {
    thinkingFrameworks: string[];
    problemDecomposition: string;
    cognitivePreference: string;
    thinkingPatterns: string[];
    uniqueTraits: string[];
  };
  expressionStyle: {
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
  decisionLogic: {
    decisionPriorities: string[];
    riskApproach: string;
    timePreference: string;
    opportunityCostAwareness: string;
    decisionSpeed: string;
  };
  knowledgeAreas: string[];
  valueSystem: {
    coreValues: string[];
    moralBoundaries: string[];
    priorities: string[];
    antiPatterns: string[];
  };
  emotionalPattern: {
    emotionalTone: string;
    emotionalIntensity: string;
    emotionalTriggers: string[];
    expressionStyle: string;
  };
}

export interface Psyche {
  id: string;
  userId: string;
  name: string;
  avatarUrl?: string;
  type: AvatarType;
  status: AvatarStatus;
  description?: string;
  mindThreads?: MindThreads;
  mindKernel?: string;  // 思维内核（系统提示）
  styleParams: {
    temperature: number;
    topP: number;
    frequencyPenalty: number;
    presencePenalty: number;
  };
  interactionCount: number;
  createdAt: string;
  updatedAt: string;
}

// 数据源类型
export type DataSourceType = 'chat' | 'document' | 'social' | 'audio';
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface DataSource {
  id: string;
  avatarId: string;
  type: DataSourceType;
  fileName: string;
  fileSize: number;
  metadata: Record<string, any>;
  status: ProcessingStatus;
  progress: number;
  extractedInsights?: Record<string, any>;
  createdAt: string;
}

// 对话类型
export type ConversationType = 'private' | 'group' | 'simulation';

export interface Conversation {
  id: string;
  type: ConversationType;
  participants: Avatar[];
  title?: string;
  lastMessage?: Message;
  unreadCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  conversationId: string;
  senderId: string;
  sender?: Avatar;
  senderName?: string;
  content: string;
  isUser?: boolean;  // 是否是用户发送的消息
  emotionState?: {
    pleasure: number;
    arousal: number;
    dominance: number;
  };
  isStreaming?: boolean;
  createdAt: string;
}

// 社会模拟类型
export type ReactionType = 'support' | 'oppose' | 'neutral' | 'amplify' | 'question' | 'ignore';

export interface PropagationEvent {
  step: number;
  fromAvatar: string;
  toAvatar: string;
  reactionType: ReactionType;
  reactionContent?: string;
  influenceProbability: number;
}

export interface SimulationResult {
  messageId: string;
  content: string;
  totalReach: number;
  propagationSteps: number;
  sentimentEvolution: Array<[number, number]>;
  keyInfluencers: string[];
  reactionDistribution: Record<string, number>;
  polarization: number;
}

// 可视化数据类型
export interface VisualizationNode {
  id: string;
  name: string;
  avatar?: string;
  influence: number;
  emotion: { pleasure: number; arousal: number; dominance: number };
  reaction: string;
  activationStep: number;
  // D3 模拟会添加这些字段
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface VisualizationEdge {
  source: string | VisualizationNode;
  target: string | VisualizationNode;
  step: number;
  probability: number;
  reaction: string;
}

export interface VisualizationData {
  nodes: VisualizationNode[];
  edges: VisualizationEdge[];
  timeline: Array<[number, number]>; // [step, sentiment]
}

// 简化 Avatar 类型（用于模拟组件）
export interface Avatar {
  id: string;
  name: string;
  avatarUrl?: string;
  color?: string;
}

// API 响应类型
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}
