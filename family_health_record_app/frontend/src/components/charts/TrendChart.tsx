'use client';

import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea
} from 'recharts';

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
}

const METRIC_LABELS: Record<string, string> = {
  axial_length: '眼轴 (Axial Length)',
  height: '身高 (Height)',
  weight: '体重 (Weight)',
  vision_acuity: '视力 (Vision Acuity)',
  glucose: '血糖 (Glucose)',
  tc: '总胆固醇 (TC)',
  tg: '甘油三酯 (TG)',
  hdl: '高密度脂蛋白 (HDL)',
  ldl: '低密度脂蛋白 (LDL)',
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
};

export const TrendChart: React.FC<TrendChartProps> = ({ data, metric, height = 240 }) => {
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
            <Line 
              type="monotone" 
              dataKey={data[0].left !== undefined ? "left" : "value"} 
              stroke="#3b82f6" 
              strokeWidth={3} 
              dot={{ r: 4, fill: '#3b82f6', strokeWidth: 2, stroke: '#fff' }} 
              activeDot={{ r: 6, strokeWidth: 0 }} 
            />
            
            {/* 右眼线 (如有) */}
            {data[0].right !== undefined && (
              <Line 
                type="monotone" 
                dataKey="right" 
                stroke="#60a5fa" 
                strokeDasharray="5 5" 
                strokeWidth={2} 
                dot={{ r: 4, fill: '#60a5fa', strokeWidth: 2, stroke: '#fff' }} 
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 左右眼区分展示 */}
      {data[0].left !== undefined && data[0].right !== undefined ? (
        <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-slate-100">
          <div>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold mb-2">左眼</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-[10px] text-slate-400 font-bold">当前</p>
                <p className="text-lg font-bold text-slate-800">
                  {(data[data.length - 1].left ?? 0).toFixed(2)}
                  <span className="text-xs font-normal text-slate-400 ml-0.5">{METRIC_UNITS[metric] || ''}</span>
                </p>
              </div>
              {data.length > 1 && (
                <div>
                  <p className="text-[10px] text-slate-400 font-bold">上次</p>
                  <p className="text-lg font-bold text-slate-600">
                    {(data[data.length - 2].left ?? 0).toFixed(2)}
                    <span className="text-xs font-normal text-slate-400 ml-0.5">{METRIC_UNITS[metric] || ''}</span>
                  </p>
                </div>
              )}
            </div>
          </div>
          <div className="border-l border-slate-100 pl-4">
            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold mb-2">右眼</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-[10px] text-slate-400 font-bold">当前</p>
                <p className="text-lg font-bold text-slate-800">
                  {(data[data.length - 1].right ?? 0).toFixed(2)}
                  <span className="text-xs font-normal text-slate-400 ml-0.5">{METRIC_UNITS[metric] || ''}</span>
                </p>
              </div>
              {data.length > 1 && (
                <div>
                  <p className="text-[10px] text-slate-400 font-bold">上次</p>
                  <p className="text-lg font-bold text-slate-600">
                    {(data[data.length - 2].right ?? 0).toFixed(2)}
                    <span className="text-xs font-normal text-slate-400 ml-0.5">{METRIC_UNITS[metric] || ''}</span>
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-slate-100">
          <div>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">当前数值</p>
            <p className="text-2xl font-bold text-slate-800 tracking-tighter">
              {(data[data.length - 1].left ?? data[data.length - 1].value ?? 0).toFixed(2)}
              <span className="text-sm font-normal text-slate-400 ml-1">{METRIC_UNITS[metric] || ''}</span>
            </p>
          </div>
          {data.length > 1 && (
            <div>
              <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">上次数值</p>
              <p className="text-2xl font-bold text-slate-600 tracking-tighter">
                {(data[data.length - 2].left ?? data[data.length - 2].value ?? 0).toFixed(2)}
                <span className="text-sm font-normal text-slate-400 ml-1">{METRIC_UNITS[metric] || ''}</span>
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
