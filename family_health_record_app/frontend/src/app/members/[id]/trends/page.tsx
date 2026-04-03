'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import { 
  ChevronLeft, TrendingUp, Calendar, AlertCircle, 
  ArrowUpRight, ArrowDownRight, Info, Edit, Trash2,
  Activity, BarChart3
} from 'lucide-react';
import { apiClient } from '@/app/api/client';
import { UI_TEXT } from '@/constants/ui-text';
import { TrendChart } from '@/components/charts/TrendChart';
import { EditObservationOverlay } from '@/components/records/EditObservationOverlay';

export default function TrendPage() {
  const { id } = useParams();
  const searchParams = useSearchParams();
  const metric = searchParams.get('metric') || 'axial_length';
  const router = useRouter();
  
  const [trendData, setTrendData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [editingObs, setEditingObs] = useState<{ id: string, value: number, label: string, unit: string } | null>(null);

  useEffect(() => {
    loadTrendData();
  }, [id, metric]);

  const loadTrendData = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getVisionDashboard(id as string);
      const metricData = (data as any)[metric];
      
      // 将扁平 series [{date, value, side}] 按日期分组为 [{date, left, right}]
      const rawSeries = metricData?.series || [];
      const byDate = new Map<string, any>();
      rawSeries.forEach((s: any) => {
        if (!byDate.has(s.date)) {
          byDate.set(s.date, { date: s.date });
        }
        const entry = byDate.get(s.date);
        if (s.side === 'left') entry.left = s.value;
        else if (s.side === 'right') entry.right = s.value;
        else entry.value = s.value;
      });
      const groupedSeries = Array.from(byDate.values()).sort((a: any, b: any) => a.date.localeCompare(b.date));
      
      setTrendData({ ...metricData, series: groupedSeries });
    } catch (err) {
      console.error('Failed to load trend data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getMetricLabel = () => {
    switch(metric) {
      case 'axial_length': return '眼轴长度趋势';
      case 'vision_va': return '视力变化趋势';
      case 'height': return '身高增长轨迹';
      case 'weight': return '体重变化轨迹';
      default: return '指标趋势';
    }
  };

  const getUnitLabel = () => {
    switch(metric) {
      case 'axial_length': return 'mm';
      case 'height': return 'cm';
      case 'weight': return 'kg';
      default: return '';
    }
  };

  const handleDeleteRecord = async (examRecordId: string) => {
    if (!confirm(UI_TEXT.CONFIRM_DELETE_RECORD)) return;
    try {
      await apiClient.deleteExamRecord(examRecordId);
      loadTrendData();
    } catch (err) {
      alert('删除失败');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin text-blue-600"><TrendingUp size={32} /></div>
      </div>
    );
  }

  const unit = getUnitLabel();

  return (
    <main className="max-w-4xl mx-auto p-4 md:p-8 space-y-8 pb-32 bg-slate-50 min-h-screen">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 hover:bg-white rounded-full transition-all text-slate-400">
            <ChevronLeft size={24} />
          </button>
          <div>
            <h1 className="text-xl font-bold text-slate-800">{getMetricLabel()}</h1>
            <p className="text-xs text-slate-400 font-medium">数据更新至: {new Date().toLocaleDateString()}</p>
          </div>
        </div>
        <div className="bg-white p-2 rounded-2xl shadow-sm border border-slate-100 flex gap-1">
           {['axial_length', 'vision_va', 'height'].map(m => (
             <button 
               key={m}
               onClick={() => router.push(`/members/${id}/trends?metric=${m}`)}
               className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${metric === m ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20' : 'text-slate-400 hover:bg-slate-50'}`}
             >
               {m === 'axial_length' ? '眼轴' : m === 'vision_va' ? '视力' : '身高'}
             </button>
           ))}
        </div>
      </header>

      {/* Chart Card */}
      <div className="glass-card rounded-[40px] p-6 md:p-10 shadow-2xl shadow-blue-900/5 relative overflow-hidden bg-white">
        <div className="flex items-center justify-between mb-8">
           <div className="flex items-center gap-3">
              <div className="bg-blue-50 p-2.5 rounded-2xl text-blue-600">
                <BarChart3 size={20} />
              </div>
              <div>
                <h2 className="font-bold text-slate-800">趋势分析图</h2>
                <p className="text-[10px] text-slate-400 uppercase font-bold tracking-widest">Statistical Analysis</p>
              </div>
           </div>
           {trendData?.growth_rate !== undefined && (
             <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-black ${trendData.growth_rate >= 0 ? 'bg-amber-50 text-amber-600' : 'bg-green-50 text-green-600'}`}>
                {trendData.growth_rate >= 0 ? <ArrowUpRight size={14}/> : <ArrowDownRight size={14}/>}
                {Math.abs(trendData.growth_rate).toFixed(2)} {unit}/年
             </div>
           )}
        </div>
        
        <div className="h-[300px] w-full">
          <TrendChart 
            data={trendData?.series || []} 
            metric={metric}
            referenceRange={trendData?.reference_range}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            {/* Comparison Details */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
               {trendData?.comparison && Object.entries(trendData.comparison).map(([side, data]: [string, any]) => {
                  const isPositive = data.delta > 0;
                  const deltaColor = isPositive ? 'text-amber-600 bg-amber-50' : 'text-green-600 bg-green-50';
                  const deltaSign = isPositive ? '+' : '';
                  const sideLabel = side === 'left' ? UI_TEXT.LABEL_LEFT_EYE : UI_TEXT.LABEL_RIGHT_EYE;

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
                           <p className="text-[10px] text-slate-400 font-bold uppercase">{UI_TEXT.LABEL_CURRENT}</p>
                           <p className="text-lg font-bold text-slate-800">{data.current.toFixed(2)}<span className="text-[10px] ml-0.5">{unit}</span></p>
                        </div>
                        <div>
                           <p className="text-[10px] text-slate-400 font-bold uppercase">{UI_TEXT.LABEL_PREVIOUS}</p>
                           <p className="text-lg font-bold text-slate-600">{data.previous.toFixed(2)}<span className="text-[10px] ml-0.5">{unit}</span></p>
                        </div>
                      </div>
                    </div>
                  );
                })}
            </div>

            {trendData?.alert_status === 'warning' && (
              <div className="glass-card rounded-[32px] p-6 border-l-4 border-red-500 bg-red-50/20">
                 <div className="flex items-start gap-4">
                   <div className="bg-red-50 p-2 rounded-xl text-red-500">
                     <Info size={20} />
                   </div>
                   <div>
                     <h3 className="font-bold text-slate-800">{UI_TEXT.LABEL_ALERT_TITLE}</h3>
                     <p className="text-sm text-slate-500 mt-1 leading-relaxed">
                       当前观测指标超出了建议参考区间（{trendData.reference_range || UI_TEXT.NO_RECORDS}）。建议咨询专业医生意见，并保持定期监测。
                     </p>
                   </div>
                 </div>
              </div>
            )}

            <div className="space-y-4">
               <h2 className="text-lg font-bold text-slate-800 px-2 flex items-center gap-2">
                 <Calendar size={18} className="text-blue-500" /> {UI_TEXT.LABEL_HISTORICAL_LIST}
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
                                  <span className="text-[10px] text-slate-400 font-bold uppercase transition-colors group-hover/item:text-blue-500">{UI_TEXT.LABEL_LEFT_EYE}</span>
                                  <div className="flex items-center gap-1.5 translate-x-1.5">
                                    <span className="text-lg font-black text-slate-800 tracking-tighter">{s.left.toFixed(2)}</span>
                                    <button 
                                      onClick={() => setEditingObs({ id: s.left_obs_id, value: s.left, label: UI_TEXT.LABEL_LEFT_EYE, unit: unit })}
                                      className="opacity-0 group-hover/item:opacity-100 p-1 rounded-md hover:bg-slate-100 text-blue-600 transition-all"
                                      data-testid={`edit-obs-${s.left_obs_id}`}
                                      title={UI_TEXT.ACTION_EDIT_VALUE}
                                    >
                                      <Edit size={12} />
                                    </button>
                                  </div>
                               </div>
                             )}
                             {s.right !== undefined && (
                               <div className="flex flex-col items-end border-l border-slate-100 pl-4 sm:pl-8 group/item">
                                  <span className="text-[10px] text-slate-400 font-bold uppercase transition-colors group-hover/item:text-blue-500">{UI_TEXT.LABEL_RIGHT_EYE}</span>
                                  <div className="flex items-center gap-1.5 translate-x-1.5">
                                    <span className="text-lg font-black text-slate-800 tracking-tighter">{s.right.toFixed(2)}</span>
                                    <button 
                                      onClick={() => setEditingObs({ id: s.right_obs_id, value: s.right, label: UI_TEXT.LABEL_RIGHT_EYE, unit: unit })}
                                      className="opacity-0 group-hover/item:opacity-100 p-1 rounded-md hover:bg-slate-100 text-blue-600 transition-all"
                                      data-testid={`edit-obs-${s.right_obs_id}`}
                                      title={UI_TEXT.ACTION_EDIT_VALUE}
                                    >
                                      <Edit size={12} />
                                    </button>
                                  </div>
                               </div>
                             )}
                             {s.value !== undefined && (
                               <div className="flex flex-col items-end group/item">
                                  <span className="text-[10px] text-slate-400 font-bold uppercase transition-colors group-hover/item:text-blue-500">{UI_TEXT.LABEL_VALUE}</span>
                                  <div className="flex items-center gap-1.5 translate-x-1.5">
                                    <span className="text-lg font-black text-slate-800 tracking-tighter">{s.value.toFixed(2)}</span>
                                    <button 
                                      onClick={() => setEditingObs({ id: s.obs_id, value: s.value, label: UI_TEXT.LABEL_VALUE, unit: unit })}
                                      className="opacity-0 group-hover/item:opacity-100 p-1 rounded-md hover:bg-slate-100 text-blue-600 transition-all"
                                      data-testid={`edit-obs-${s.obs_id}`}
                                      title={UI_TEXT.ACTION_EDIT_VALUE}
                                    >
                                      <Edit size={12} />
                                    </button>
                                  </div>
                               </div>
                             )}
                          </div>
                          
                          <button 
                            onClick={() => handleDeleteRecord(s.exam_record_id)}
                            className="p-3 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-2xl transition-all"
                            data-testid={`delete-exam-${s.exam_record_id}`}
                            title={UI_TEXT.ACTION_DELETE_RECORD}
                          >
                             <Trash2 size={20} />
                          </button>
                        </div>
                     </div>
                  ))}
               </div>
            </div>
          </div>
          
          <div className="space-y-6">
             <div className="glass-card rounded-[32px] p-6 bg-white border border-slate-100 space-y-4">
                <h3 className="font-bold text-slate-800 flex items-center gap-2">
                  <Activity size={18} className="text-blue-500" /> 指标概览
                </h3>
                <div className="space-y-3">
                   <div className="p-4 bg-slate-50 rounded-2xl">
                      <p className="text-[10px] text-slate-400 font-bold uppercase">{UI_TEXT.LABEL_LIMIT_RANGE}</p>
                      <p className="text-sm font-bold text-slate-700 mt-1">{trendData?.reference_range || UI_TEXT.NO_RECORDS}</p>
                   </div>
                   <div className="p-4 bg-slate-50 rounded-2xl">
                      <p className="text-[10px] text-slate-400 font-bold uppercase">最新状态</p>
                      <div className="flex items-center gap-2 mt-1">
                         <div className={`w-2 h-2 rounded-full ${trendData?.alert_status === 'warning' ? 'bg-red-500' : 'bg-green-500'}`} />
                         <span className="text-sm font-bold text-slate-700">{trendData?.alert_status === 'warning' ? '需要关注' : '正常'}</span>
                      </div>
                   </div>
                </div>
             </div>
          </div>
      </div>

      {editingObs && (
        <EditObservationOverlay
          obsId={editingObs.id}
          initialValue={editingObs.value}
          label={editingObs.label}
          unit={editingObs.unit}
          apiClient={apiClient}
          onClose={() => setEditingObs(null)}
          onSuccess={() => loadTrendData()}
        />
      )}
    </main>
  );
}
