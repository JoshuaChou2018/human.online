"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Users,
  Play,
  Pause,
  Settings,
  Loader2,
  Check,
  X,
  Globe,
  Eye,
  Sparkles,
  MessageSquare,
  TrendingUp,
  Info,
  Send,
  Brain,
  GitBranch,
  Clock,
  Activity,
  ChevronRight,
  RotateCcw,
  Zap,
  BarChart3,
  Flame,
  Thermometer,
  Scale,
  Radio,
  AlertTriangle,
  Wind,
  Anchor,
  MessageCircle,
  History,
  Trash2,
  Share2,
  Radio as RadioIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";

import { API_BASE_URL } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

// ============================================
// 类型定义
// ============================================

interface AvatarPoolItem {
  id: string;
  name: string;
  description: string | null;
  user_id: string;
  is_in_sandbox: boolean;
  color: string;
  avatar_type?: string;
}

// 反事实模拟消息
interface SimulationMessage {
  id: string;
  avatar_id: string;
  avatar_name: string;
  content: string;
  step: number;
  round: number;
  response_type: string;
  sentiment: number;
  stance: 'support' | 'oppose' | 'neutral';
  thinking?: string;  // LLM生成的思考过程
  emotion_emoji?: string;  // 表情符号
  target_avatar_id?: string;
  from_avatar_id?: string;
  from_name?: string;
  x?: number;
  y?: number;
}

// 传播事件
interface PropagationEvent {
  step: number;
  from_avatar_id: string;
  from_avatar_name: string;
  to_avatar_id: string;
  to_avatar_name: string;
  reaction_type: string;
  influence_probability: number;
  message?: string;
}

interface VisualizationNode {
  id: string;
  name: string;
  influence: number;
  emotion: { valence: number; arousal: number; emoji?: string; pleasure?: number };
  reaction: string;
  activation_step: number;
  x?: number;
  y?: number;
  messages?: SimulationMessage[];
}

interface VisualizationEdge {
  source: string;
  target: string;
  step: number;
  probability: number;
  reaction: string;
  animated?: boolean;
}

// 模拟结果
interface SimulationResult {
  id: string;
  title: string;
  trigger_event: string;
  max_rounds: number;
  max_steps?: number;
  status: string;
  scenario?: { name: string; atmosphere: string };
  nodes: VisualizationNode[];
  edges: VisualizationEdge[];
  messages: SimulationMessage[];
  timeline: Array<{
    step: number;
    round: number;
    topic?: string;
    sentiment_score: number;
    heat_score?: number;
    stance_distribution?: {
      support: number;
      oppose: number;
      neutral: number;
    };
    active_nodes?: number;
  }>;
  stats: {
    total_messages: number;
    total_reach?: number;
    max_depth?: number;
    polarization: number;
    key_influencers?: string[];
  };
}

// ============================================
// 预设场景
// ============================================

const SCENARIO_PRESETS = [
  {
    key: 'trump_iran',
    title: '特朗普对伊朗军事行动',
    event: '突发：特朗普发推称"伊朗核计划已越过红线，美国将在24小时内采取必要行动"',
    source: '唐纳德·特朗普',
    icon: AlertTriangle,
    color: 'from-red-500 to-orange-500',
    sentiment: -0.6,
    heat: 0.9,
    description: '特朗普宣布将对伊朗核设施采取预防性军事打击'
  },
  {
    key: 'ai_consciousness',
    title: 'AI意识觉醒',
    event: '重磅：OpenAI宣布GPT-6通过所有意识测试，AI首次展现自我认知',
    source: 'OpenAI',
    icon: Brain,
    color: 'from-purple-500 to-pink-500',
    sentiment: 0.2,
    heat: 0.95,
    description: 'OpenAI宣布其最新模型展现出自主意识和情感反应'
  },
  {
    key: 'economic_crisis',
    title: '全球金融危机',
    event: '股市崩盘：道指单日暴跌2500点，触发全球熔断机制',
    source: '彭博社',
    icon: TrendingUp,
    color: 'from-red-600 to-rose-600',
    sentiment: -0.9,
    heat: 0.95,
    description: '美股三大指数单日暴跌超过20%，触发全球金融海啸'
  },
  {
    key: 'alien_contact',
    title: '外星文明接触',
    event: '历史时刻：NASA确认收到来自4.2光年外的智慧信号',
    source: 'NASA',
    icon: RadioIcon,
    color: 'from-blue-500 to-cyan-500',
    sentiment: 0.6,
    heat: 1.0,
    description: 'NASA宣布收到来自比邻星系的结构化信号'
  },
];

// ============================================
// 组件：节点内容（不包含位置变换）
// ============================================

function NetworkNodeContent({
  node,
  isActive,
  isSelected,
  currentMessages,
}: {
  node: VisualizationNode;
  isActive: boolean;
  isSelected: boolean;
  currentMessages: SimulationMessage[];
}) {
  const size = Math.max(28, Math.min(52, node.influence * 4 + 20));
  const getEmotionColor = (valence: number) => {
    if (valence > 0.3) return "#22c55e";
    if (valence < -0.3) return "#ef4444";
    return "#64748b";
  };

  return (
    <g opacity={isActive ? 1 : 0.3}>
      {/* 选中光环 */}
      {isSelected && (
        <circle
          r={size + 12}
          fill="none"
          stroke="#6366f1"
          strokeWidth="3"
          strokeDasharray="4,4"
          className="animate-spin"
          style={{ animationDuration: '3s' }}
        />
      )}
      
      {/* 外圈 - 情绪颜色 */}
      <circle
        r={size + 4}
        fill="none"
        stroke={getEmotionColor(node.emotion.valence)}
        strokeWidth={2}
        opacity={0.3}
      />
      
      {/* 节点圆形 */}
      <circle
        r={size}
        fill="white"
        stroke={getEmotionColor(node.emotion.valence)}
        strokeWidth={3}
        className="transition-all duration-300 shadow-lg"
        filter="drop-shadow(0 2px 4px rgba(0,0,0,0.1))"
      />
      
      {/* 表情符号 */}
      <text
        textAnchor="middle"
        dy="0.35em"
        fontSize={size * 0.55}
        style={{ userSelect: 'none' }}
      >
        {node.emotion?.emoji || '😐'}
      </text>

      {/* 激活步骤标记 */}
      {node.activation_step > 0 && (
        <g>
          <circle
            r={11}
            cx={size * 0.7}
            cy={-size * 0.7}
            fill="#6366f1"
            stroke="white"
            strokeWidth={2}
          />
          <text
            textAnchor="middle"
            x={size * 0.7}
            y={-size * 0.7}
            dy="0.35em"
            fontSize="10"
            fill="white"
            fontWeight="bold"
          >
            {node.activation_step}
          </text>
        </g>
      )}

      {/* 最新消息提示点 */}
      {currentMessages.length > 0 && (
        <circle
          r={5}
          cx={size * 0.8}
          cy={size * 0.8}
          fill="#10b981"
          className="animate-pulse"
        />
      )}

      {/* 名称标签 - 放在节点下方 */}
      <text
        textAnchor="middle"
        dy={size + 24}
        fontSize="13"
        fill="#334155"
        fontWeight={isActive ? "bold" : "normal"}
        style={{ userSelect: 'none' }}
      >
        {node.name}
      </text>
    </g>
  );
}

// ============================================
// 组件：传播网络图（带拖拽、缩放、平移）
// ============================================

function PropagationNetwork({
  nodes,
  edges,
  messages,
  currentStep,
  currentRound,
  selectedNode,
  onNodeClick
}: {
  nodes: VisualizationNode[];
  edges: VisualizationEdge[];
  messages: SimulationMessage[];
  currentStep: number;
  currentRound: number;
  selectedNode: string | null;
  onNodeClick: (nodeId: string) => void;
}) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [nodePositions, setNodePositions] = useState<Map<string, { x: number; y: number }>>(new Map());
  const simulationRef = useRef<any>(null);
  const isDraggingRef = useRef(false);
  
  // 缩放和平移状态
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const isPanningRef = useRef(false);
  const panStartRef = useRef({ x: 0, y: 0 });

  // 初始化d3力导向模拟
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (nodes.length === 0) return;
    
    const d3 = require('d3');
    
    const width = dimensions.width;
    const height = dimensions.height;
    
    // 如果已有位置，复用；否则初始化
    const currentPositions = nodePositions;
    
    // 准备节点数据
    const nodeData = nodes.map(n => {
      const existing = currentPositions.get(n.id);
      return {
        id: n.id,
        x: existing?.x ?? width / 2 + (Math.random() - 0.5) * 200,
        y: existing?.y ?? height / 2 + (Math.random() - 0.5) * 200,
        fx: existing ? existing.x : null,
        fy: existing ? existing.y : null,
      };
    });
    
    // 准备边数据 - 只包含已存在节点之间的边
    const nodeIds = new Set(nodes.map(n => n.id));
    const linkData = edges
      .filter(e => nodeIds.has(e.source) && nodeIds.has(e.target))
      .map(e => ({
        source: e.source,
        target: e.target,
      }));

    // 如果已有模拟，先停止
    if (simulationRef.current) {
      simulationRef.current.stop();
    }

    // 创建力导向模拟
    const simulation = d3.forceSimulation(nodeData as any)
      .force('link', d3.forceLink(linkData).id((d: any) => d.id).distance(120).strength(0.5))
      .force('charge', d3.forceManyBody().strength(-800))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(60))
      .alphaDecay(0.02)  // 较慢的衰减，让布局更稳定
      .velocityDecay(0.3);

    simulation.on('tick', () => {
      const newPositions = new Map<string, { x: number; y: number }>();
      nodeData.forEach((d: any) => {
        newPositions.set(d.id, { x: d.x, y: d.y });
      });
      setNodePositions(newPositions);
    });

    // 30秒后降低能量，让布局稳定
    const stabilizeTimer = setTimeout(() => {
      simulation.alphaDecay(0.1);
    }, 30000);

    simulationRef.current = simulation;

    return () => {
      clearTimeout(stabilizeTimer);
      simulation.stop();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes.length, dimensions.width, dimensions.height]); // 节点数量或尺寸变化时重新初始化

  // 更新边连接（不改变节点位置）
  useEffect(() => {
    if (!simulationRef.current || edges.length === 0) return;
    
    const d3 = require('d3');
    
    // 获取当前模拟中的节点ID集合
    const simNodes = simulationRef.current.nodes() as any[];
    const nodeIds = new Set(simNodes.map((n: any) => n.id));
    
    // 只添加已存在节点之间的边
    const linkData = edges
      .filter(e => nodeIds.has(e.source) && nodeIds.has(e.target))
      .map(e => ({
        source: e.source,
        target: e.target,
      }));
    
    (simulationRef.current.force('link') as any).links(linkData);
    simulationRef.current.alpha(0.3).restart();
  }, [edges]);

  // 窗口大小变化
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };
    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  // 坐标转换（考虑缩放和平移）
  const screenToSvg = (screenX: number, screenY: number) => {
    const svgRect = svgRef.current?.getBoundingClientRect();
    if (!svgRect) return { x: screenX, y: screenY };
    
    return {
      x: (screenX - svgRect.left - transform.x) / transform.k,
      y: (screenY - svgRect.top - transform.y) / transform.k,
    };
  };

  // 拖拽节点处理
  const handleDragStart = (e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation();
    isDraggingRef.current = true;
    if (!simulationRef.current) return;
    
    const node = simulationRef.current.nodes().find((n: any) => n.id === nodeId);
    if (!node) return;

    const startPos = screenToSvg(e.clientX, e.clientY);
    node.fx = startPos.x;
    node.fy = startPos.y;
    simulationRef.current.alphaTarget(0.3).restart();

    const handleDrag = (event: MouseEvent) => {
      event.preventDefault();
      const pos = screenToSvg(event.clientX, event.clientY);
      node.fx = pos.x;
      node.fy = pos.y;
    };

    const handleDragEnd = () => {
      isDraggingRef.current = false;
      // 保持固定位置，不释放
      simulationRef.current.alphaTarget(0);
      document.removeEventListener('mousemove', handleDrag);
      document.removeEventListener('mouseup', handleDragEnd);
    };

    document.addEventListener('mousemove', handleDrag);
    document.addEventListener('mouseup', handleDragEnd);
  };

  // 缩放处理
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const scaleFactor = e.deltaY > 0 ? 0.9 : 1.1;
    const newK = Math.max(0.2, Math.min(3, transform.k * scaleFactor));
    
    // 以鼠标位置为中心缩放
    const svgRect = svgRef.current?.getBoundingClientRect();
    if (!svgRect) return;
    
    const mouseX = e.clientX - svgRect.left;
    const mouseY = e.clientY - svgRect.top;
    
    const newX = mouseX - (mouseX - transform.x) * (newK / transform.k);
    const newY = mouseY - (mouseY - transform.y) * (newK / transform.k);
    
    setTransform({ x: newX, y: newY, k: newK });
  };

  // 平移处理
  const handlePanStart = (e: React.MouseEvent) => {
    if (isDraggingRef.current) return;
    isPanningRef.current = true;
    panStartRef.current = { x: e.clientX - transform.x, y: e.clientY - transform.y };

    const handlePanMove = (event: MouseEvent) => {
      if (!isPanningRef.current) return;
      setTransform(prev => ({
        ...prev,
        x: event.clientX - panStartRef.current.x,
        y: event.clientY - panStartRef.current.y,
      }));
    };

    const handlePanEnd = () => {
      isPanningRef.current = false;
      document.removeEventListener('mousemove', handlePanMove);
      document.removeEventListener('mouseup', handlePanEnd);
    };

    document.addEventListener('mousemove', handlePanMove);
    document.addEventListener('mouseup', handlePanEnd);
  };

  // 重置视图
  const resetView = () => {
    setTransform({ x: 0, y: 0, k: 1 });
  };

  const { width, height } = dimensions;

  // 获取当前可见的边（带动画效果）
  const visibleEdges = edges.filter((e) => e.step <= currentStep);
  
  // 获取当前可见的消息
  const visibleMessages = messages.filter(m => 
    m.step <= currentStep && m.round <= currentRound
  );

  // 按节点分组消息
  const messagesByNode = useMemo(() => {
    const map = new Map<string, SimulationMessage[]>();
    visibleMessages.forEach(msg => {
      if (!map.has(msg.avatar_id)) {
        map.set(msg.avatar_id, []);
      }
      map.get(msg.avatar_id)!.push(msg);
    });
    return map;
  }, [visibleMessages]);

  return (
    <div ref={containerRef} className="relative w-full h-full bg-slate-50 rounded-xl overflow-hidden">
      <svg 
        ref={svgRef} 
        width={width} 
        height={height} 
        className="w-full h-full cursor-grab active:cursor-grabbing"
        onWheel={handleWheel}
        onMouseDown={handlePanStart}
      >
        {/* 变换组 */}
        <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}>
          {/* 连线 - 带动画路径 */}
          {visibleEdges.map((edge, idx) => {
            const source = nodePositions.get(edge.source);
            const target = nodePositions.get(edge.target);
            if (!source || !target) return null;

            const isNew = edge.step === currentStep;
            
            return (
              <g key={`${edge.source}-${edge.target}-${idx}`}>
                {/* 背景线 */}
                <line
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke="#e2e8f0"
                  strokeWidth={Math.max(2, edge.probability * 5)}
                  strokeOpacity={0.3}
                />
                {/* 前景动画线 */}
                <line
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke={isNew ? "#6366f1" : "#64748b"}
                  strokeWidth={isNew ? 3 : Math.max(1, edge.probability * 3)}
                  strokeOpacity={isNew ? 1 : 0.6}
                  className={isNew ? "animate-pulse" : "transition-all duration-500"}
                  markerEnd="url(#arrowhead)"
                  strokeDasharray={isNew ? "none" : "5,5"}
                >
                  {isNew && (
                    <animate
                      attributeName="stroke-dasharray"
                      from="0,1000"
                      to="1000,0"
                      dur="1s"
                      fill="freeze"
                    />
                  )}
                </line>
                {/* 传播概率标签 */}
                {isNew && (
                  <g
                    transform={`translate(${(source.x + target.x) / 2}, ${(source.y + target.y) / 2})`}
                  >
                    <circle r="14" fill="white" stroke="#6366f1" strokeWidth="2" />
                    <text textAnchor="middle" dy="0.3em" fontSize="10" fill="#6366f1" fontWeight="bold">
                      {(edge.probability * 100).toFixed(0)}%
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* 箭头标记 */}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="12"
              markerHeight="8"
              refX="28"
              refY="4"
              orient="auto"
            >
              <polygon points="0 0, 12 4, 0 8" fill="#6366f1" fillOpacity="0.8" />
            </marker>
          </defs>

          {/* 节点 */}
          {nodes.map((node) => {
            const pos = nodePositions.get(node.id);
            if (!pos) return null;

            const isActive = node.activation_step >= 0 && node.activation_step <= currentStep;
            const nodeMessages = messagesByNode.get(node.id) || [];

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                className="cursor-move"
                onMouseDown={(e) => handleDragStart(e, node.id)}
                onClick={(e) => {
                  e.stopPropagation();
                  onNodeClick(node.id);
                }}
              >
                <NetworkNodeContent
                  node={node}
                  isActive={isActive}
                  isSelected={selectedNode === node.id}
                  currentMessages={nodeMessages}
              />
            </g>
          );
        })}
        </g>
      </svg>

      {/* 图例 */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur rounded-xl p-4 shadow-lg border text-sm">
        <p className="font-medium text-slate-700 mb-2">图例</p>
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-green-400" />
            <span className="text-slate-600">积极情绪</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-slate-400" />
            <span className="text-slate-600">中性情绪</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-400" />
            <span className="text-slate-600">消极情绪</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-0.5 bg-indigo-500" />
            <span className="text-slate-600">传播路径</span>
          </div>
        </div>
      </div>

      {/* 活跃统计 */}
      <div className="absolute top-4 right-4 bg-white/90 backdrop-blur rounded-xl p-3 shadow-lg border">
        <div className="flex items-center gap-4 text-sm">
          <div className="text-center">
            <p className="text-2xl font-bold text-indigo-600">
              {nodes.filter(n => n.activation_step >= 0 && n.activation_step <= currentStep).length}
            </p>
            <p className="text-xs text-slate-500">已激活</p>
          </div>
          <div className="w-px h-8 bg-slate-200" />
          <div className="text-center">
            <p className="text-2xl font-bold text-amber-500">
              {visibleMessages.length}
            </p>
            <p className="text-xs text-slate-500">消息</p>
          </div>
        </div>
      </div>

      {/* 缩放控制 */}
      <div className="absolute bottom-4 right-4 flex flex-col gap-2">
        <div className="bg-white/90 backdrop-blur rounded-lg shadow-lg border p-1">
          <button
            onClick={() => setTransform(prev => ({ ...prev, k: Math.min(3, prev.k * 1.2) }))}
            className="w-8 h-8 flex items-center justify-center hover:bg-slate-100 rounded"
            title="放大"
          >
            +
          </button>
          <div className="h-px bg-slate-200 my-1" />
          <button
            onClick={() => setTransform(prev => ({ ...prev, k: Math.max(0.2, prev.k / 1.2) }))}
            className="w-8 h-8 flex items-center justify-center hover:bg-slate-100 rounded"
            title="缩小"
          >
            −
          </button>
        </div>
        <button
          onClick={resetView}
          className="bg-white/90 backdrop-blur rounded-lg shadow-lg border px-3 py-2 text-xs font-medium hover:bg-slate-100"
          title="重置视图"
        >
          重置
        </button>
      </div>
    </div>
  );
}

// ============================================
// 主页面
// ============================================

export default function SimulatePage() {
  const router = useRouter();
  
  // 状态管理
  const [mode, setMode] = useState<'setup' | 'running' | 'results'>('setup');
  const [simulationType, setSimulationType] = useState<'propagation' | 'counterfactual'>('counterfactual');
  
  // 场景设置
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [customEvent, setCustomEvent] = useState('');
  const [message, setMessage] = useState('');
  const [maxSteps, setMaxSteps] = useState(5);
  const [maxRounds, setMaxRounds] = useState(3);
  
  // 参与者
  const [avatarPool, setAvatarPool] = useState<AvatarPoolItem[]>([]);
  const [selectedAvatarIds, setSelectedAvatarIds] = useState<Set<string>>(new Set());
  const [initiatorId, setInitiatorId] = useState<string | null>(null);
  
  // 模拟结果
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [currentRound, setCurrentRound] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // 获取认证头
  const getAuthHeaders = () => {
    const token = useAuthStore.getState().token;
    return {
      "Content-Type": "application/json",
      Authorization: token ? `Bearer ${token}` : "",
    };
  };

  // 加载分身池
  const fetchAvatarPool = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sandbox/pool`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setAvatarPool(data);
        if (data.length > 0) {
          const allIds = new Set<string>(data.map((a: AvatarPoolItem) => a.id));
          setSelectedAvatarIds(allIds);
          if (!initiatorId) setInitiatorId(data[0].id);
        }
      }
    } catch (error) {
      console.error("Error fetching avatar pool:", error);
    }
  }, [initiatorId]);

  useEffect(() => {
    fetchAvatarPool();
  }, [fetchAvatarPool]);

  // 计算最大步骤
  const calculatedMaxStep = useMemo(() => {
    if (!result) return 0;
    return result.timeline?.length || result.stats?.max_depth || 0;
  }, [result]);

  // 自动播放
  const handlePlayPause = () => {
    if (isPlaying) {
      setIsPlaying(false);
    } else {
      if (currentStep >= calculatedMaxStep && currentRound >= (result?.max_rounds || 1)) {
        setCurrentStep(0);
        setCurrentRound(1);
      }
      setIsPlaying(true);
    }
  };

  useEffect(() => {
    if (!isPlaying || !result) return;
    
    const maxStep = calculatedMaxStep;
    const maxRound = result.max_rounds || 1;
    
    if (currentStep >= maxStep && currentRound >= maxRound) {
      setIsPlaying(false);
      return;
    }

    const interval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev >= maxStep) {
          // 进入下一轮
          if (currentRound < maxRound) {
            setCurrentRound(r => r + 1);
            return 0;
          }
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 1500);

    return () => clearInterval(interval);
  }, [isPlaying, calculatedMaxStep, currentRound, result]);

  // 运行模拟（流式实时模式）
  const runSimulation = async () => {
    // 检查登录状态
    const { isAuthenticated } = useAuthStore.getState();
    if (!isAuthenticated) {
      toast.error("请先登录后再运行模拟", {
        action: {
          label: "去登录",
          onClick: () => router.push("/auth/login"),
        },
      });
      return;
    }

    if (selectedAvatarIds.size === 0) {
      toast.error("请至少选择一个分身参与模拟");
      return;
    }
    if (!initiatorId) {
      toast.error("请选择发起者");
      return;
    }
    
    const eventText = selectedPreset 
      ? SCENARIO_PRESETS.find(p => p.key === selectedPreset)?.event 
      : (customEvent || message);
      
    if (!eventText) {
      toast.error("请输入或选择触发事件");
      return;
    }

    setLoading(true);
    setMode('running');
    
    // 初始化空结果
    const initialResult: SimulationResult = {
      id: '',
      title: '数字社会模拟',
      trigger_event: eventText,
      scenario: { name: '', atmosphere: '' },
      status: 'running',
      nodes: [],
      edges: [],
      timeline: [],
      stats: { total_messages: 0, total_reach: 0, polarization: 0 },
      messages: [],
      max_steps: maxSteps,
      max_rounds: maxRounds,
    };
    setResult(initialResult);

    try {
      // 使用流式API
      const response = await fetch(`${API_BASE_URL}/simulations/counterfactual/stream`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          preset: selectedPreset,
          custom_event: eventText,
          avatar_ids: Array.from(selectedAvatarIds),
          initiator_id: initiatorId,
          max_steps: maxSteps,
          max_rounds: maxRounds,
        }),
      });

      if (!response.ok) {
        throw new Error('Simulation failed');
      }

      // 读取流式数据
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              handleStreamEvent(event);
            } catch (e) {
              console.error('Failed to parse event:', line);
            }
          }
        }
      }
      
      toast.success('模拟完成！');
    } catch (error) {
      console.error('Simulation error:', error);
      toast.error('模拟运行失败');
      setMode('setup');
    } finally {
      setLoading(false);
    }
  };

  // 处理流式事件
  const handleStreamEvent = (event: any) => {
    setResult(prev => {
      if (!prev) return prev;
      
      switch (event.type) {
        case 'start':
          return {
            ...prev,
            id: event.data.simulation_id,
            scenario: event.data.scenario,
          };
          
        case 'node_activate':
          // 添加或更新节点
          const existingNodeIndex = prev.nodes.findIndex(n => n.id === event.data.avatar_id);
          const newNode = {
            id: event.data.avatar_id,
            name: event.data.avatar_name,
            influence: 0.5,
            emotion: { valence: 0, arousal: 0.5, emoji: '😐' },
            reaction: 'activated',
            activation_step: event.data.step,
          };
          
          if (existingNodeIndex >= 0) {
            const updatedNodes = [...prev.nodes];
            updatedNodes[existingNodeIndex] = { ...updatedNodes[existingNodeIndex], ...newNode };
            return { ...prev, nodes: updatedNodes };
          } else {
            return { ...prev, nodes: [...prev.nodes, newNode] };
          }
          
        case 'message':
          // 添加消息
          const newMessage = {
            id: event.data.id,
            avatar_id: event.data.avatar_id,
            avatar_name: event.data.avatar_name,
            content: event.data.content,
            thinking: event.data.thinking,
            step: event.step,
            round: event.round,
            response_type: event.data.response_type,
            sentiment: event.data.sentiment,
            stance: event.data.stance,
            emotion_emoji: event.data.emotion_emoji,
          };
          
          // 更新节点表情
          const nodeIndex = prev.nodes.findIndex(n => n.id === event.data.avatar_id);
          let updatedNodes = prev.nodes;
          if (nodeIndex >= 0) {
            updatedNodes = [...prev.nodes];
            updatedNodes[nodeIndex] = {
              ...updatedNodes[nodeIndex],
              emotion: {
                ...updatedNodes[nodeIndex].emotion,
                valence: event.data.sentiment,
                emoji: event.data.emotion_emoji,
              }
            };
          }
          
          // 自动跟随最新步骤
          setCurrentStep(event.step);
          
          return {
            ...prev,
            nodes: updatedNodes,
            messages: [...prev.messages, newMessage],
            stats: {
              ...prev.stats,
              total_messages: prev.stats.total_messages + 1,
            }
          };
          
        case 'edge_create':
          // 添加边
          const newEdge = {
            source: event.data.source,
            target: event.data.target,
            step: event.data.step,
            probability: event.data.probability,
            reaction: event.data.reaction,
          };
          return {
            ...prev,
            edges: [...prev.edges, newEdge],
          };
          
        case 'step_complete':
          // 更新当前步骤
          setCurrentStep(event.step);
          return {
            ...prev,
            stats: {
              ...prev.stats,
              total_reach: event.data.activated_count,
            }
          };
          
        case 'complete':
          // 模拟完成，更新所有数据
          return {
            ...prev,
            nodes: event.data.nodes || prev.nodes,
            edges: event.data.edges || prev.edges,
            messages: event.data.messages || prev.messages,
            stats: event.data.stats || prev.stats,
          };
          
        case 'error':
          toast.error(event.data.error || '模拟出错');
          return prev;
          
        default:
          return prev;
      }
    });
  };

  // 重置
  const reset = () => {
    setMode('setup');
    setResult(null);
    setCurrentStep(0);
    setCurrentRound(1);
    setIsPlaying(false);
    setSelectedNode(null);
  };

  // 渲染情绪仪表盘
  const renderSentimentGauge = (value: number) => {
    const percentage = ((value + 1) / 2) * 100;
    const color = value > 0.3 ? 'bg-green-500' : value < -0.3 ? 'bg-red-500' : 'bg-yellow-500';
    const label = value > 0.3 ? '正面' : value < -0.3 ? '负面' : '中性';
    
    return (
      <div className="flex items-center gap-3">
        <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
          <div className={cn("h-full transition-all duration-500", color)} style={{ width: `${percentage}%` }} />
        </div>
        <span className={cn("text-sm font-medium", value > 0.3 ? 'text-green-600' : value < -0.3 ? 'text-red-600' : 'text-yellow-600')}>
          {label}
        </span>
      </div>
    );
  };

  // 获取当前时间线数据
  const currentTimelineData = useMemo(() => {
    if (!result?.timeline) return null;
    return result.timeline.find(t => t.step === currentStep && t.round === currentRound) || result.timeline[result.timeline.length - 1];
  }, [result, currentStep, currentRound]);

  // 设置步骤
  const [setupStep, setSetupStep] = useState(1);

  // 渲染设置界面
  if (mode === 'setup') {
    return (
      <div className="min-h-screen bg-slate-50">
        <header className="bg-white border-b sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => router.push("/")}>
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <Globe className="w-4 h-4 text-white" />
                </div>
                <h1 className="font-bold text-lg">数字社会模拟器</h1>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-6 py-8">
          {/* 未登录提示 */}
          {!useAuthStore.getState().isAuthenticated && (
            <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                  <Users className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <p className="font-medium text-amber-900">需要登录</p>
                  <p className="text-sm text-amber-700">登录后即可运行数字社会模拟</p>
                </div>
              </div>
              <Button 
                onClick={() => router.push("/auth/login")}
                className="bg-amber-600 hover:bg-amber-700 text-white"
              >
                去登录
              </Button>
            </div>
          )}

          {/* 步骤指示器 */}
          <div className="flex items-center gap-2 mb-8">
            {[1, 2, 3].map((step) => (
              <button
                key={step}
                onClick={() => setSetupStep(step)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg transition-all",
                  setupStep === step
                    ? "bg-indigo-600 text-white"
                    : "bg-white text-slate-600 hover:bg-slate-100"
                )}
              >
                <span className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-sm font-bold">
                  {step}
                </span>
                <span className="text-sm font-medium">
                  {step === 1 ? '选择场景' : step === 2 ? '选择分身' : '模拟设置'}
                </span>
              </button>
            ))}
          </div>

          {/* 步骤 1: 场景选择 */}
          {setupStep === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold mb-4">预设场景（反事实模拟）</h2>
                <div className="grid md:grid-cols-2 gap-4">
                  {SCENARIO_PRESETS.map((preset) => (
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
                        <div className={cn("w-10 h-10 rounded-lg bg-gradient-to-br flex items-center justify-center shrink-0", preset.color)}>
                          <preset.icon className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <h3 className="font-medium">{preset.title}</h3>
                          <p className="text-sm text-slate-500 mt-1">{preset.description}</p>
                          <p className="text-xs text-slate-400 mt-2">{preset.event}</p>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="text-lg font-semibold mb-4">或自定义事件</h2>
                <Card className="p-4">
                  <Textarea
                    placeholder="输入你想模拟的事件... 例如：明天太阳突然熄灭"
                    value={customEvent}
                    onChange={(e) => {
                      setCustomEvent(e.target.value);
                      if (e.target.value) setSelectedPreset(null);
                    }}
                    className="min-h-[100px]"
                  />
                </Card>
              </div>

              <div className="flex justify-end">
                <Button onClick={() => setSetupStep(2)}>
                  下一步 <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </div>
          )}

          {/* 步骤 2: 分身选择 */}
          {setupStep === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold mb-4">选择发起者</h2>
                <div className="flex flex-wrap gap-2">
                  {avatarPool.map((avatar) => (
                    <button
                      key={avatar.id}
                      onClick={() => setInitiatorId(avatar.id)}
                      className={cn(
                        "flex items-center gap-2 px-3 py-2 rounded-lg border transition-all",
                        initiatorId === avatar.id
                          ? "border-indigo-500 bg-indigo-50 ring-2 ring-indigo-200"
                          : "border-slate-200 hover:border-indigo-300"
                      )}
                    >
                      <div className={cn("w-6 h-6 rounded-full bg-gradient-to-br", avatar.color)} />
                      <span className="text-sm">{avatar.name}</span>
                      {initiatorId === avatar.id && <Check className="w-4 h-4 text-indigo-600" />}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="text-lg font-semibold mb-4">选择参与者（{selectedAvatarIds.size} 已选）</h2>
                <div className="flex flex-wrap gap-2">
                  {avatarPool.map((avatar) => (
                    <button
                      key={avatar.id}
                      onClick={() => {
                        setSelectedAvatarIds(prev => {
                          const newSet = new Set(prev);
                          if (newSet.has(avatar.id)) newSet.delete(avatar.id);
                          else newSet.add(avatar.id);
                          return newSet;
                        });
                      }}
                      className={cn(
                        "flex items-center gap-2 px-3 py-2 rounded-lg border transition-all",
                        selectedAvatarIds.has(avatar.id)
                          ? "border-indigo-500 bg-indigo-50"
                          : "border-slate-200 opacity-50 hover:opacity-100"
                      )}
                    >
                      <div className={cn("w-6 h-6 rounded-full bg-gradient-to-br", avatar.color)} />
                      <span className="text-sm">{avatar.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setSetupStep(1)}>
                  上一步
                </Button>
                <Button onClick={() => setSetupStep(3)}>
                  下一步 <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </div>
          )}

          {/* 步骤 3: 设置 */}
          {setupStep === 3 && (
            <div className="space-y-6">
              <Card className="p-6">
                <h2 className="text-lg font-semibold mb-4">模拟参数</h2>
                <div className="space-y-6">
                  <div>
                    <label className="text-sm font-medium mb-2 block">传播深度（步数）</label>
                    <div className="flex items-center gap-4">
                      <input
                        type="range"
                        min={1}
                        max={50}
                        value={maxSteps}
                        onChange={(e) => setMaxSteps(Number(e.target.value))}
                        className="flex-1"
                      />
                      <span className="text-lg font-bold text-indigo-600 w-8">{maxSteps}</span>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">对话轮次</label>
                    <div className="flex items-center gap-4">
                      <input
                        type="range"
                        min={1}
                        max={20}
                        value={maxRounds}
                        onChange={(e) => setMaxRounds(Number(e.target.value))}
                        className="flex-1"
                      />
                      <span className="text-lg font-bold text-indigo-600 w-8">{maxRounds}</span>
                    </div>
                  </div>
                </div>
              </Card>

              <Button
                size="lg"
                className="w-full"
                onClick={runSimulation}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    运行模拟中...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5 mr-2" />
                    开始数字社会模拟
                  </>
                )}
              </Button>

              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setSetupStep(2)}>
                  上一步
                </Button>
              </div>
            </div>
          )}
        </main>
      </div>
    );
  }

  // 渲染结果界面
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={reset}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="font-bold text-lg">{result?.title || '模拟结果'}</h1>
              <p className="text-xs text-slate-500">{result?.trigger_event}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handlePlayPause}>
              {isPlaying ? <Pause className="w-4 h-4 mr-1" /> : <Play className="w-4 h-4 mr-1" />}
              {isPlaying ? '暂停' : '播放'}
            </Button>
            <Button variant="outline" size="sm" onClick={reset}>
              <RotateCcw className="w-4 h-4 mr-1" />
              重置
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-4">
        {result && (
          <div className="grid grid-cols-12 gap-4 h-[calc(100vh-140px)]">
            {/* 左侧：网络可视化 */}
            <div className="col-span-8 bg-white rounded-xl border overflow-hidden">
              <PropagationNetwork
                nodes={result.nodes}
                edges={result.edges}
                messages={result.messages}
                currentStep={currentStep}
                currentRound={currentRound}
                selectedNode={selectedNode}
                onNodeClick={setSelectedNode}
              />
            </div>

            {/* 右侧：控制面板和详情 */}
            <div className="col-span-4 space-y-4 overflow-auto">
              {/* 播放控制 */}
              <Card className="p-4">
                <div className="flex items-center gap-4 mb-4">
                  <span className="text-sm font-medium">进度</span>
                  <input
                    type="range"
                    min={0}
                    max={calculatedMaxStep}
                    value={currentStep}
                    onChange={(e) => {
                      setCurrentStep(Number(e.target.value));
                      setIsPlaying(false);
                    }}
                    className="flex-1"
                  />
                  <span className="text-sm text-slate-600">
                    第 {currentRound} 轮 · 步骤 {currentStep}/{calculatedMaxStep}
                  </span>
                </div>

                {/* 当前状态 */}
                {currentTimelineData && (
                  <div className="space-y-3 pt-3 border-t">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-slate-600 flex items-center gap-1">
                          <Scale className="w-4 h-4" /> 情绪
                        </span>
                      </div>
                      {renderSentimentGauge(currentTimelineData.sentiment_score)}
                    </div>

                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-slate-600 flex items-center gap-1">
                          <Flame className="w-4 h-4" /> 热度
                        </span>
                        <span className="text-sm">{((currentTimelineData.heat_score || 0) * 100).toFixed(0)}%</span>
                      </div>
                      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-orange-500 transition-all"
                          style={{ width: `${(currentTimelineData.heat_score || 0) * 100}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="text-sm text-slate-600 mb-1">立场分布</div>
                      <div className="flex h-2 rounded-full overflow-hidden">
                        <div className="bg-green-500" style={{ width: `${(currentTimelineData.stance_distribution?.support || 0) * 100}%` }} />
                        <div className="bg-red-500" style={{ width: `${(currentTimelineData.stance_distribution?.oppose || 0) * 100}%` }} />
                        <div className="bg-slate-300" style={{ width: `${(currentTimelineData.stance_distribution?.neutral || 0) * 100}%` }} />
                      </div>
                      <div className="flex justify-between text-xs mt-1">
                        <span className="text-green-600">支持</span>
                        <span className="text-red-600">反对</span>
                        <span className="text-slate-500">中立</span>
                      </div>
                    </div>
                  </div>
                )}
              </Card>

              {/* 消息流 */}
              <Card className="p-4 flex-1">
                <h3 className="font-medium mb-3 flex items-center gap-2">
                  <MessageCircle className="w-4 h-4 text-indigo-600" />
                  当前对话
                </h3>
                <div className="space-y-3 max-h-[400px] overflow-auto">
                  {result.messages
                    .filter(m => m.step <= currentStep && m.round <= currentRound)
                    .slice(-5)
                    .map((msg, idx) => (
                      <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className={cn(
                          "p-3 rounded-lg text-sm",
                          msg.stance === 'support' ? 'bg-green-50 border border-green-200' :
                          msg.stance === 'oppose' ? 'bg-red-50 border border-red-200' :
                          'bg-slate-50 border border-slate-200'
                        )}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-lg">{msg.emotion_emoji || '😐'}</span>
                          <span className="font-medium">{msg.avatar_name}</span>
                          <Badge variant="outline" className="text-[10px]">
                            {msg.response_type}
                          </Badge>
                          <span className={cn("text-xs ml-auto",
                            msg.sentiment > 0 ? 'text-green-600' :
                            msg.sentiment < 0 ? 'text-red-600' :
                            'text-slate-500'
                          )}>
                            {msg.sentiment > 0 ? '支持' : msg.sentiment < 0 ? '反对' : '中立'}
                          </span>
                        </div>
                        
                        {/* 思考过程 */}
                        {msg.thinking && (
                          <div className="mb-2 p-2 bg-white/50 rounded border border-dashed border-slate-300">
                            <p className="text-xs text-slate-500 flex items-center gap-1">
                              <Brain className="w-3 h-3" />
                              内心思考
                            </p>
                            <p className="text-xs text-slate-600 italic line-clamp-2">{msg.thinking}</p>
                          </div>
                        )}
                        
                        {/* 发言内容 */}
                        <p className="text-slate-800">{msg.content}</p>
                      </motion.div>
                    ))}
                </div>
              </Card>

              {/* 统计 */}
              <Card className="p-4">
                <h3 className="font-medium mb-3">模拟统计</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-2 bg-slate-50 rounded-lg">
                    <p className="text-2xl font-bold text-indigo-600">{result.stats?.total_messages || 0}</p>
                    <p className="text-xs text-slate-500">总消息</p>
                  </div>
                  <div className="text-center p-2 bg-slate-50 rounded-lg">
                    <p className="text-2xl font-bold text-indigo-600">
                      {((result.stats?.polarization || 0) * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs text-slate-500">极化程度</p>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
