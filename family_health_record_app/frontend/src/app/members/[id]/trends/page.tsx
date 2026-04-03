'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import { 
  ChevronLeft, TrendingUp, Calendar, Info, ArrowUpRight, 
  Trash2, Edit, Save, X 
} from 'lucide-react';
import { apiClient } from '@/app/api/client';
import { TrendChart } from '@/components/charts/TrendChart';
import { EditObservationOverlay } from '@/components/records/EditObservationOverlay';

const METRICS = [
  { key: 'axial_length', label: '眼轴' },
  { key: 'height', label: '身高' },
  { key: 'weight', label: '体重' },
  { key: 'vision_acuity', label: '视力' },
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
  const [editingObs, setEditingObs] = useState<{ id: string; value: number; label: string; unit: string } | null>(null);

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
      
      const byDate = new Map<string, any>();
      (t.series || []).forEach((s: any) => {
        const dateKey = s.date;
        if (!byDate.has(dateKey)) {
          byDate.set(dateKey, { date: dateKey, exam_record_id: s.exam_record_id });
        }
        const entry = byDate.get(dateKey);
        if (s.side === 'left') {
          entry.left = s.value;
          entry.left_obs_id = s.observation_id;
        } else if (s.side === 'right') {
          entry.right = s.value;
          entry.right_obs_id = s.observation_id;
        } else {
          entry.value = s.value;
          entry.obs_id = s.observation_id;
        }
      });
      
      const series = Array.from(byDate.values()).sort((a: any, b: any) => a.date.localeCompare(b.date));
      setTrendData({ ...t, series });
    } catch (err) {
      console.error('Failed to load trends:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (examRecordId: string) => {
    if (!confirm('确定要删除这条检查记录及其所有指标吗？此操作不可撤销。')) return;
    try {
      await apiClient.deleteExamRecord(examRecordId);
      loadMemberAndTrends();
    } catch (err: any) {
      alert(err.message || '删除失败');
    }
  };

  const getUnitLabel = () => {
    switch (selectedMetric) {
      case 'axial_length': return 'mm';
      case 'height': return 'cm';
      case 'weight': return 'kg';
      case 'vision_acuity': return 'decimal';
      default: return '';
    }
  };

  return (
    <main className="max-w-4xl mx-auto p-4 md:p-8 space-y-6 bg-slate-50 min-h-screen">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 hover:bg-white rounded-full transition-all text-slate-400">
            <ChevronLeft size={24} />
          </button>
          <div className="bg-blue-600 rounded-full p-2 text-white shadow-lg shadow-blue-500/10">
            <TrendingUp size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold font-sans tracking-tight text-slate-800">趋势分析</h1>
            <p className="text-xs text-slate-500">{member?.name}</p>
          </div>
        </div>
      </header>

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
        <section className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
           <div className="glass-card rounded-[32px] p-6 shadow-xl shadow-slate-900/5">
              <TrendChart data={trendData?.series || []} metric={selectedMetric} height={320} />
              
              {trendData?.comparison && (
                <div className="mt-8 pt-6 border-t border-slate-100">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">最近两次检查对比分析</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {['left', 'right', 'value'].map((side) => {
                      const data = trendData.comparison[side];
                      if (!data) return null;
                      const sideLabel = side === 'left' ? '左眼' : side === 'right' ? '右眼' : '检查值';
                      const deltaColor = data.delta > 0 ? 'text-red-500' : data.delta < 0 ? 'text-green-500' : 'text-slate-400';
                      const deltaSign = data.delta > 0 ? '+' : '';
                      const unit = getUnitLabel();
                      
                      return (
                        <div key={side} className="bg-slate-50/50 rounded-2xl p-4 border border-slate-100">
                          <div className="flex justify-between items-center mb-3">
                            <span className="text-xs font-bold text-slate-500">{sideLabel}</span>
                            <span className={`text-xs font-black px-2 py-0.5 rounded-full bg-white border border-slate-100 ${deltaColor}`}>
                              {deltaSign}{data.delta.toFixed(3)}{unit}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                               <p className="text-[10px] text-slate-400 font-bold uppercase">当前</p>
                               <p className="text-lg font-bold text-slate-800">{data.current.toFixed(2)}<span className="text-[10px] ml-0.5">{unit}</span></p>
                            </div>
                            <div>
                               <p className="text-[10px] text-slate-400 font-bold uppercase">上次</p>
                               <p className="text-lg font-bold text-slate-600">{data.previous.toFixed(2)}<span className="text-[10px] ml-0.5">{unit}</span></p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
           </div>

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

           <div className="space-y-4">
              <h2 className="text-lg font-bold text-slate-800 px-2 flex items-center gap-2">
                <Calendar size={18} className="text-blue-500" /> 历史记录清单
              </h2>
              <div className="space-y-3">
                 {(trendData?.series || []).slice().reverse().map((s: any, idx: number) => (
                    <div 
                      key={idx} 
                      className="glass-card rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:shadow-lg transition-all border border-transparent hover:border-slate-100"
                    >
                       <div className="flex items-center gap-4">
                          <div className="bg-blue-50 text-blue-500 p-2.5 rounded-xl">
                             <Calendar size={20} />
                          </div>
                          <div>
                             <p className="font-bold text-slate-800">{s.date}</p>
                             <p className="text-[10px] text-slate-400 uppercase font-bold tracking-tighter">检查记录</p>
                          </div>
                       </div>
                       <div className="flex items-center gap-6 sm:gap-12">
                         <div className="flex gap-4 sm:gap-8 overflow-x-auto no-scrollbar">
                            {s.left !== undefined && (
                              <div className="flex flex-col items-end group/item">
                                 <span className="text-[10px] text-slate-400 font-bold uppercase transition-colors group-hover/item:text-blue-500">左眼</span>
                                 <div className="flex items-center gap-1.5 translate-x-1.5">
                                   <span className="text-lg font-black text-slate-800 tracking-tighter">{s.left.toFixed(2)}</span>
                                   <button 
                                     onClick={() => setEditingObs({ id: s.left_obs_id, value: s.left, label: '左眼指标', unit: getUnitLabel() })}
                                     className="opacity-0 group-hover/item:opacity-100 p-1 rounded-md hover:bg-slate-100 text-blue-600 transition-all"
                                   >
                                     <Edit size={12} />
                                   </button>
                                 </div>
                              </div>
                            )}
                            {s.right !== undefined && (
                              <div className="flex flex-col items-end border-l border-slate-100 pl-4 sm:pl-8 group/item">
                                 <span className="text-[10px] text-slate-400 font-bold uppercase transition-colors group-hover/item:text-blue-500">右眼</span>
                                 <div className="flex items-center gap-1.5 translate-x-1.5">
                                   <span className="text-lg font-black text-slate-800 tracking-tighter">{s.right.toFixed(2)}</span>
                                   <button 
                                     onClick={() => setEditingObs({ id: s.right_obs_id, value: s.right, label: '右眼指标', unit: getUnitLabel() })}
                                     className="opacity-0 group-hover/item:opacity-100 p-1 rounded-md hover:bg-slate-100 text-blue-600 transition-all"
                                   >
                                     <Edit size={12} />
                                   </button>
                                 </div>
                              </div>
                            )}
                            {s.value !== undefined && (
                              <div className="flex flex-col items-end group/item">
                                 <span className="text-[10px] text-slate-400 font-bold uppercase transition-colors group-hover/item:text-blue-500">数值</span>
                                 <div className="flex items-center gap-1.5 translate-x-1.5">
                                   <span className="text-lg font-black text-slate-800 tracking-tighter">{s.value.toFixed(2)}</span>
                                   <button 
                                     onClick={() => setEditingObs({ id: s.obs_id, value: s.value, label: '指标数值', unit: getUnitLabel() })}
                                     className="opacity-0 group-hover/item:opacity-100 p-1 rounded-md hover:bg-slate-100 text-blue-600 transition-all"
                                   >
                                     <Edit size={12} />
                                   </button>
                                 </div>
                              </div>
                            )}
                         </div>
                         <div className="flex items-center border-l border-slate-100 pl-4">
                            <button 
                              onClick={() => handleDelete(s.exam_record_id)}
                              className="p-2 text-slate-300 hover:text-red-500 transition-colors"
                              title="删除记录"
                            >
                              <Trash2 size={18} />
                            </button>
                         </div>
                       </div>
                    </div>
                 ))}
              </div>
           </div>
        </section>
      )}

      {editingObs && (
        <EditObservationOverlay
          obsId={editingObs.id}
          initialValue={editingObs.value}
          label={editingObs.label}
          unit={editingObs.unit}
          apiClient={apiClient}
          onClose={() => setEditingObs(null)}
          onSuccess={() => loadMemberAndTrends()}
        />
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
