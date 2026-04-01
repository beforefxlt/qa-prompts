'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import { ChevronLeft, Info, Calendar, Filter } from 'lucide-react';
import { apiClient } from '@/app/api/client';
import { TrendChart } from '@/components/charts/TrendChart';

const METRICS = [
  { key: 'axial_length', label: '眼轴' },
  { key: 'height', label: '身高' },
  { key: 'weight', label: '体重' },
  { key: 'vision_acuity', label: '视力' },
  { key: 'glucose', label: '血糖' },
  { key: 'tc', label: '总胆固醇' },
  { key: 'tg', label: '甘油三酯' },
  { key: 'hdl', label: 'HDL' },
  { key: 'ldl', label: 'LDL' },
];

function TrendsContent() {
  const router = useRouter();
  const { id } = useParams();
  const searchParams = useSearchParams();
  const initialMetric = searchParams.get('metric') || 'axial_length';
  
  const [member, setMember] = useState<any>(null);
  const [selectedMetric, setSelectedMetric] = useState(initialMetric);
  const [trendData, setTrendData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadMemberAndTrends();
    }
  }, [id, selectedMetric]);

  const loadMemberAndTrends = async () => {
    setLoading(true);
    try {
      const [m, t] = await Promise.all([
        apiClient.getMember(id as string),
        apiClient.getTrends(id as string, selectedMetric)
      ]);
      setMember(m);
      
      // 格式化趋势数据为 TrendChart 要求的格式
      const series = (t.series || []).map((s: any) => ({
        date: s.date.slice(5),
        left: s.side === 'left' ? s.value : undefined,
        right: s.side === 'right' ? s.value : undefined,
        value: (s.side === null || s.side === undefined) ? s.value : undefined, // 兼容单列数据
      })).reduce((acc: any[], curr: any) => {
        const existing = acc.find(item => item.date === curr.date);
        if (existing) {
          if (curr.left !== undefined) existing.left = curr.left;
          if (curr.right !== undefined) existing.right = curr.right;
          if (curr.value !== undefined) existing.value = curr.value;
        } else {
          acc.push(curr);
        }
        return acc;
      }, []);
      
      setTrendData({ ...t, series });
    } catch (err) {
      console.error('Failed to load trends:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="max-w-4xl mx-auto p-4 md:p-8 space-y-6 bg-slate-50 min-h-screen">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 hover:bg-white rounded-full transition-all text-slate-400">
            <ChevronLeft size={24} />
          </button>
          <div>
            <h1 className="text-xl font-bold font-sans tracking-tight text-slate-800">趋势分析</h1>
            <p className="text-xs text-slate-500">{member?.name}</p>
          </div>
        </div>
      </header>

      {/* 指标切换 */}
      <div className="flex gap-2 overflow-x-auto pb-4 -mx-4 px-4 no-scrollbar">
        {METRICS.map((m) => (
          <button
            key={m.key}
            onClick={() => setSelectedMetric(m.key)}
            className={`px-5 py-2.5 rounded-full text-sm font-bold whitespace-nowrap transition-all border-2 ${
              selectedMetric === m.key
                ? 'bg-blue-600 text-white border-blue-600 shadow-lg shadow-blue-500/20'
                : 'bg-white text-slate-500 border-transparent hover:border-slate-200'
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="glass-card rounded-[32px] p-12 flex items-center justify-center">
            <div className="animate-pulse text-slate-300 font-bold">数据加载中...</div>
        </div>
      ) : (
        <section className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
           {/* 图表主卡片 */}
           <div className="glass-card rounded-[32px] p-6 shadow-xl shadow-slate-900/5">
              <TrendChart data={trendData?.series || []} metric={selectedMetric} height={320} />
           </div>

           {/* 报警与建议 */}
           {trendData?.alert_status === 'warning' && (
             <div className="glass-card rounded-[32px] p-6 border-l-4 border-red-500 bg-red-50/20">
                <div className="flex items-start gap-4">
                  <div className="bg-red-50 p-2 rounded-xl text-red-500">
                    <Info size={20} />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800">异常提醒</h3>
                    <p className="text-sm text-slate-500 mt-1 leading-relaxed">
                      当前观测指标超出了建议参考区间（{trendData.reference_range || '未定义'}）。建议咨询专业医生意见，并保持定期监测。
                    </p>
                  </div>
                </div>
             </div>
           )}

           {/* 历史记录列表入口 (示意) */}
           <div className="space-y-4">
              <h2 className="text-lg font-bold text-slate-800 px-2 flex items-center gap-2">
                <Calendar size={18} className="text-blue-500" /> 历史记录
              </h2>
              <div className="space-y-3">
                 {(trendData?.series || []).slice().reverse().map((s: any, idx: number) => (
                    <div 
                      key={idx} 
                      className="glass-card rounded-2xl p-4 flex items-center justify-between hover:bg-slate-50 transition-colors cursor-pointer"
                      onClick={() => {/* 这里的 s 没有 record_id，通常需要后端返回记录 ID */}}
                    >
                       <div className="flex items-center gap-4">
                          <div className="bg-slate-100 p-2 rounded-lg text-slate-400">
                             <Calendar size={18} />
                          </div>
                          <div>
                             <p className="font-bold text-slate-800">{s.date}</p>
                             <p className="text-[10px] text-slate-400 uppercase font-bold">{s.side ? (s.side === 'left' ? '左眼' : '右眼') : '检查值'}</p>
                          </div>
                       </div>
                       <div className="text-right">
                          <p className="text-lg font-black text-slate-800 tracking-tighter">{s.value || (s.left ?? s.right)}</p>
                       </div>
                    </div>
                 ))}
              </div>
           </div>
        </section>
      )}
    </main>
  );
}

export default function TrendsPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <TrendsContent />
    </Suspense>
  );
}
