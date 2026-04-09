'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { VisualizationData } from '@/types';
import { cn } from '@/lib/utils';

interface SocialNetworkGraphProps {
  data: VisualizationData;
  currentStep: number;
  isPlaying: boolean;
}

export function SocialNetworkGraph({
  data,
  currentStep,
  isPlaying,
}: SocialNetworkGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // 响应式尺寸
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // D3 可视化
  useEffect(() => {
    if (!svgRef.current || !data) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { width, height } = dimensions;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // 创建主容器
    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // 缩放行为
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom as any);

    // 准备数据
    const nodes = data.nodes.map((n) => ({ ...n }));
    const links = data.edges
      .filter((e) => e.step <= currentStep)
      .map((e) => ({ ...e }));

    // 节点影响力作为大小依据
    const sizeScale = d3
      .scaleLinear()
      .domain([0, 10])
      .range([20, 60]);

    // 情绪颜色映射
    const emotionColor = (pleasure: number) => {
      if (pleasure > 0.3) return '#4ade80'; // 绿色 - 积极
      if (pleasure < -0.3) return '#f87171'; // 红色 - 消极
      return '#94a3b8'; // 灰色 - 中性
    };

    // 反应类型图标
    const reactionIcon = (type: string) => {
      const icons: Record<string, string> = {
        support: '👍',
        oppose: '👎',
        neutral: '😐',
        amplify: '📢',
        question: '❓',
        ignore: '👻',
        none: '●',
      };
      return icons[type] || '●';
    };

    // 创建力导向模拟
    const simulation = d3
      .forceSimulation(nodes as any)
      .force(
        'link',
        d3
          .forceLink(links as any)
          .id((d: any) => d.id)
          .distance(100)
          .strength(0.5)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(innerWidth / 2, innerHeight / 2))
      .force('collision', d3.forceCollide().radius((d: any) => sizeScale(d.influence) + 10));

    // 绘制连线
    const linkGroup = g.append('g').attr('class', 'links');

    const link = linkGroup
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#cbd5e1')
      .attr('stroke-width', (d) => Math.max(1, d.probability * 4))
      .attr('stroke-opacity', 0.6)
      .attr('stroke-dasharray', (d) => (d.reaction === 'ignore' ? '4,4' : 'none'));

    // 箭头标记
    svg
      .append('defs')
      .selectAll('marker')
      .data(['end'])
      .enter()
      .append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#94a3b8');

    // 绘制节点组
    const nodeGroup = g.append('g').attr('class', 'nodes');

    const node = nodeGroup
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .style('cursor', 'pointer')
      .call(
        d3
          .drag<SVGGElement, any>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      )
      .on('click', (event, d) => {
        event.stopPropagation();
        setSelectedNode(selectedNode === d.id ? null : d.id);
      });

    // 节点圆形背景
    node
      .append('circle')
      .attr('r', (d) => sizeScale(d.influence))
      .attr('fill', 'white')
      .attr('stroke', (d) => emotionColor(d.emotion.pleasure))
      .attr('stroke-width', 3)
      .attr('opacity', (d) => (d.activationStep <= currentStep ? 1 : 0.3))
      .transition()
      .duration(300)
      .attr('r', (d) => sizeScale(d.influence));

    // 节点头像/首字母
    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-0.2em')
      .attr('font-size', (d) => `${sizeScale(d.influence) * 0.5}px`)
      .attr('font-weight', 'bold')
      .attr('fill', '#334155')
      .text((d) => d.name.charAt(0));

    // 节点名称
    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.2em')
      .attr('font-size', '10px')
      .attr('fill', '#64748b')
      .text((d) => d.name);

    // 反应图标
    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dx', (d) => sizeScale(d.influence) * 0.7)
      .attr('dy', (d) => -sizeScale(d.influence) * 0.7)
      .attr('font-size', '14px')
      .text((d) => reactionIcon(d.reaction))
      .attr('opacity', (d) => (d.activationStep > 0 && d.activationStep <= currentStep ? 1 : 0));

    // 激活步骤标记
    node
      .append('circle')
      .attr('r', 8)
      .attr('cx', (d) => sizeScale(d.influence) * 0.8)
      .attr('cy', (d) => sizeScale(d.influence) * 0.8)
      .attr('fill', '#6366f1')
      .attr('opacity', (d) => (d.activationStep > 0 && d.activationStep <= currentStep ? 1 : 0));

    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('x', (d) => sizeScale(d.influence) * 0.8)
      .attr('y', (d) => sizeScale(d.influence) * 0.8)
      .attr('dy', '0.3em')
      .attr('font-size', '8px')
      .attr('fill', 'white')
      .attr('font-weight', 'bold')
      .text((d) => d.activationStep)
      .attr('opacity', (d) => (d.activationStep > 0 && d.activationStep <= currentStep ? 1 : 0));

    // 选中状态
    node
      .filter((d: any) => d.id === selectedNode)
      .append('circle')
      .attr('r', (d) => sizeScale(d.influence) + 8)
      .attr('fill', 'none')
      .attr('stroke', '#6366f1')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '4,4');

    // 更新位置
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // 背景点击取消选择
    svg.on('click', () => setSelectedNode(null));

    return () => {
      simulation.stop();
    };
  }, [data, dimensions, currentStep, selectedNode]);

  const selectedNodeData = selectedNode
    ? data.nodes.find((n) => n.id === selectedNode)
    : null;

  return (
    <div ref={containerRef} className="relative w-full h-full">
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="w-full h-full"
      />

      {/* 图例 */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur rounded-lg p-3 shadow-lg border">
        <p className="text-xs font-medium text-slate-700 mb-2">图例</p>
        <div className="space-y-1.5 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-400" />
            <span className="text-slate-600">积极情绪</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-slate-400" />
            <span className="text-slate-600">中性情绪</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-400" />
            <span className="text-slate-600">消极情绪</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-indigo-100 border border-indigo-400 flex items-center justify-center text-[8px]">
              1
            </span>
            <span className="text-slate-600">激活顺序</span>
          </div>
        </div>
      </div>

      {/* 选中节点详情 */}
      {selectedNodeData && (
        <div className="absolute top-4 right-4 bg-white/95 backdrop-blur rounded-lg p-4 shadow-lg border w-56">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-medium">
              {selectedNodeData.name.charAt(0)}
            </div>
            <div>
              <p className="font-medium text-slate-900">{selectedNodeData.name}</p>
              <p className="text-xs text-slate-500">影响力: {selectedNodeData.influence.toFixed(1)}</p>
            </div>
          </div>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">激活步骤</span>
              <span className="font-medium">
                {selectedNodeData.activationStep > 0 ? selectedNodeData.activationStep : '未激活'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">反应</span>
              <span className="font-medium capitalize">{selectedNodeData.reaction}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">情绪状态</span>
              <div className="flex items-center gap-1">
                <span
                  className={cn(
                    'w-2 h-2 rounded-full',
                    selectedNodeData.emotion.pleasure > 0.3 && 'bg-green-400',
                    selectedNodeData.emotion.pleasure < -0.3 && 'bg-red-400',
                    selectedNodeData.emotion.pleasure >= -0.3 &&
                      selectedNodeData.emotion.pleasure <= 0.3 &&
                      'bg-slate-400'
                  )}
                />
                <span className="text-xs">
                  {selectedNodeData.emotion.pleasure > 0.3
                    ? '积极'
                    : selectedNodeData.emotion.pleasure < -0.3
                    ? '消极'
                    : '中性'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
