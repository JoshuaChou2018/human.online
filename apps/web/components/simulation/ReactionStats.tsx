'use client';

import { SimulationResult, VisualizationData } from '@/types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { cn } from '@/lib/utils';

interface ReactionStatsProps {
  result: SimulationResult;
  distribution: VisualizationData;
}

const REACTION_COLORS: Record<string, string> = {
  support: '#4ade80',
  oppose: '#f87171',
  neutral: '#94a3b8',
  amplify: '#fbbf24',
  question: '#60a5fa',
  ignore: '#d1d5db',
};

const REACTION_LABELS: Record<string, string> = {
  support: '支持',
  oppose: '反对',
  neutral: '中性',
  amplify: '放大',
  question: '质疑',
  ignore: '忽略',
};

export function ReactionStats({ result, distribution }: ReactionStatsProps) {
  const chartData = Object.entries(result.reactionDistribution).map(([type, count]) => ({
    type: REACTION_LABELS[type] || type,
    count,
    color: REACTION_COLORS[type] || '#94a3b8',
  }));

  return (
    <div className="h-full flex flex-col p-4">
      <h3 className="text-lg font-semibold text-slate-900 mb-2">反应分布统计</h3>
      <p className="text-sm text-slate-500 mb-6">
        数字分身群体对言论的反应类型分布
      </p>

      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ top: 20, right: 30, left: 60, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
            <XAxis 
              type="number" 
              stroke="#64748b"
              fontSize={12}
            />
            <YAxis 
              type="category" 
              dataKey="type"
              stroke="#64748b"
              fontSize={12}
              width={50}
            />
            <Tooltip 
              cursor={{ fill: '#f1f5f9' }}
              contentStyle={{ 
                backgroundColor: 'white', 
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
              }}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={32}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 关键洞察 */}
      <div className="mt-6 pt-4 border-t">
        <h4 className="text-sm font-medium text-slate-900 mb-3">关键洞察</h4>
        <div className="grid grid-cols-2 gap-3">
          <InsightCard
            label="主要反应"
            value={getDominantReaction(result.reactionDistribution)}
            color="indigo"
          />
          <InsightCard
            label="情绪倾向"
            value={getSentimentLabel(result.sentimentEvolution)}
            color={getSentimentColor(result.sentimentEvolution)}
          />
          <InsightCard
            label="传播效率"
            value={`${((result.totalReach / 20) * 100).toFixed(0)}%`}
            color="emerald"
          />
          <InsightCard
            label="讨论热度"
            value={getHeatLevel(result)}
            color="amber"
          />
        </div>
      </div>
    </div>
  );
}

function InsightCard({ 
  label, 
  value, 
  color 
}: { 
  label: string; 
  value: string; 
  color: string;
}) {
  const colorClasses: Record<string, string> = {
    indigo: 'bg-indigo-50 text-indigo-700',
    emerald: 'bg-emerald-50 text-emerald-700',
    amber: 'bg-amber-50 text-amber-700',
    red: 'bg-red-50 text-red-700',
    green: 'bg-green-50 text-green-700',
    slate: 'bg-slate-50 text-slate-700',
  };

  return (
    <div className={cn('p-3 rounded-lg', colorClasses[color] || colorClasses.slate)}>
      <p className="text-xs opacity-70">{label}</p>
      <p className="font-semibold">{value}</p>
    </div>
  );
}

function getDominantReaction(distribution: Record<string, number>): string {
  const sorted = Object.entries(distribution).sort((a, b) => b[1] - a[1]);
  return REACTION_LABELS[sorted[0]?.[0]] || '未知';
}

function getSentimentLabel(evolution: Array<[number, number]>): string {
  if (evolution.length === 0) return '中性';
  const lastValue = evolution[evolution.length - 1][1];
  if (lastValue > 0.3) return '积极';
  if (lastValue < -0.3) return '消极';
  return '中性';
}

function getSentimentColor(evolution: Array<[number, number]>): string {
  if (evolution.length === 0) return 'slate';
  const lastValue = evolution[evolution.length - 1][1];
  if (lastValue > 0.3) return 'green';
  if (lastValue < -0.3) return 'red';
  return 'slate';
}

function getHeatLevel(result: SimulationResult): string {
  const totalReactions = Object.values(result.reactionDistribution).reduce((a, b) => a + b, 0);
  if (totalReactions > 10) return '极高';
  if (totalReactions > 7) return '高';
  if (totalReactions > 4) return '中等';
  return '低';
}
