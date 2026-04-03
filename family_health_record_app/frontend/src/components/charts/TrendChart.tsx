'use client';

import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea
} from 'recharts';
import { EyeMode } from './EyeModeToggle';

type ChartPoint = {
  date: string;
  left?: number;
  right?: number;
  value?: number; // 兼容单列数据
};

interface TrendChartProps {
  data: ChartPoint[];
  metric: string;
  height?: number | string;
  referenceRange?: string;
  eyeMode?: EyeMode;
}

const METRIC_LABELS: Record<string, string> = {
  axial_length: '眼轴',
  height: '身高',
  weight: '体重',
  vision_acuity: '视力',
  glucose: '血糖',
  tc: '总胆固醇',
  tg: '甘油三酯',
  hdl: '高密度脂蛋白',
  ldl: '低密度脂蛋白',
  hemoglobin: '血红蛋白',
  hba1c: '糖化血红蛋白',
};

const METRIC_UNITS: Record<string, string> = {
  axial_length: 'mm',
  height: 'cm',
  weight: 'kg',
  glucose: 'mmol/L',
  tc: 'mmol/L',
  tg: 'mmol/L',
  hdl: 'mmol/L',
  ldl: 'mmol/L',
  hemoglobin: 'g/L',
  hba1c: '%',
};

export const TrendChart: React.FC<TrendChartProps> = ({ data, metric, height = 240, eyeMode = 'both' }) => {
  const label = METRIC_LABELS[metric] || metric;

  if (!data || data.length === 0) {
    return (
      <div style={{ height }} className="flex items-center justify-center text-slate-400 text-sm bg-slate-50/50 rounded-2xl border border-dashed border-slate-200">
        暂无数据，上传检查单后自动展示
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-700 flex items-center gap-2">
          <span className="w-2 h-6 bg-blue-500 rounded-full"></span>
          {label}
        </h3>
        <span className="text-xs font-medium px-2 py-1 bg-green-50 text-green-600 rounded-full">
          {data.length} 条记录
        </span>
      </div>

      <div style={{ height: typeof height === 'number' ? `${height}px` : height }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis 
              dataKey="date" 
              stroke="#94a3b8" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false}
              dy={10}
            />
            <YAxis 
              stroke="#94a3b8" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false}
              dx={-10}
            />
            <Tooltip
              contentStyle={{ 
                borderRadius: '16px', 
                border: 'none', 
                boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
                padding: '12px'
              }}
            />
            {/* 默认各指标的参考区间背景（示例：眼轴） */}
            {metric === 'axial_length' && (
              <ReferenceArea y1={22.5} y2={24} fill="#10b981" fillOpacity={0.05} />
            )}
            
            {/* 左眼/主数据线 */}
            {data[0].left !== undefined && (
              <Line 
                type="monotone" 
                dataKey="left" 
                stroke={eyeMode === 'right' ? '#cbd5e1' : '#3b82f6'} 
                strokeWidth={eyeMode === 'right' ? 1 : 3} 
                strokeOpacity={eyeMode === 'right' ? 0.3 : 1}
                dot={{ r: eyeMode === 'right' ? 3 : 4, fill: eyeMode === 'right' ? '#cbd5e1' : '#3b82f6', strokeWidth: 2, stroke: '#fff' }} 
                activeDot={{ r: eyeMode === 'right' ? 4 : 6, strokeWidth: 0 }} 
              />
            )}
            
            {/* 右眼线 (如有) */}
            {data[0].right !== undefined && (
              <Line 
                type="monotone" 
                dataKey="right" 
                stroke={eyeMode === 'left' ? '#cbd5e1' : (eyeMode === 'both' ? '#60a5fa' : '#3b82f6')}
                strokeDasharray={eyeMode === 'both' ? '5 5' : 'none'}
                strokeWidth={eyeMode === 'left' ? 1 : (eyeMode === 'both' ? 2 : 3)} 
                strokeOpacity={eyeMode === 'left' ? 0.3 : 1}
                dot={{ r: eyeMode === 'left' ? 3 : 4, fill: eyeMode === 'left' ? '#cbd5e1' : (eyeMode === 'both' ? '#60a5fa' : '#3b82f6'), strokeWidth: 2, stroke: '#fff' }} 
                activeDot={{ r: eyeMode === 'left' ? 4 : 6, strokeWidth: 0 }} 
              />
            )}

            {/* 非眼部指标（身高/体重等） */}
            {data[0].value !== undefined && data[0].left === undefined && data[0].right === undefined && (
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#3b82f6" 
                strokeWidth={3} 
                dot={{ r: 4, fill: '#3b82f6', strokeWidth: 2, stroke: '#fff' }} 
                activeDot={{ r: 6, strokeWidth: 0 }} 
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
