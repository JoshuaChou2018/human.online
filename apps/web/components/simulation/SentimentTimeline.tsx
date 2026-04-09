'use client';

import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

interface SentimentTimelineProps {
  data: Array<[number, number]>;
  currentStep: number;
}

export function SentimentTimeline({ data, currentStep }: SentimentTimelineProps) {
  const chartData = useMemo(() => {
    return data
      .filter(([step]) => step <= currentStep)
      .map(([step, sentiment]) => ({
        step: `第${step}层`,
        sentiment: Number((sentiment * 100).toFixed(1)),
        stepNum: step,
      }));
  }, [data, currentStep]);

  return (
    <div className="h-full flex flex-col p-4">
      <h3 className="text-lg font-semibold text-slate-900 mb-2">情感演化时间线</h3>
      <p className="text-sm text-slate-500 mb-6">
        追踪信息传播过程中群体情感的变化趋势
      </p>

      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis 
              dataKey="step" 
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
            />
            <YAxis 
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              domain={[-100, 100]}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'white', 
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
              }}
              formatter={(value: number) => [`${value}%`, '情感倾向']}
            />
            <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="3 3" />
            <ReferenceLine y={30} stroke="#4ade80" strokeDasharray="3 3" strokeOpacity={0.5} label="积极" />
            <ReferenceLine y={-30} stroke="#f87171" strokeDasharray="3 3" strokeOpacity={0.5} label="消极" />
            <Line 
              type="monotone" 
              dataKey="sentiment" 
              stroke="#6366f1" 
              strokeWidth={3}
              dot={{ fill: '#6366f1', strokeWidth: 2, r: 5 }}
              activeDot={{ r: 7, fill: '#4f46e5' }}
              animationDuration={500}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 图例说明 */}
      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-400" />
          <span className="text-xs text-slate-600">积极 (&gt;30%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-slate-300" />
          <span className="text-xs text-slate-600">中性 (-30%~30%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-400" />
          <span className="text-xs text-slate-600">消极 (&lt;-30%)</span>
        </div>
      </div>
    </div>
  );
}
