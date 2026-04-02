'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { 
  ChevronLeft, Settings, User, Eye, ArrowUpRight, 
  TrendingUp, Calendar, AlertCircle, PlusCircle, Camera
} from 'lucide-react';
import { apiClient } from '@/app/api/client';
import { TrendChart } from '@/components/charts/TrendChart';
import { UploadOverlay } from '@/components/upload/UploadOverlay';


export default function MemberDashboard() {
  const { id } = useParams();
  const router = useRouter();
  const [member, setMember] = useState<any>(null);
  const [visionData, setVisionData] = useState<any>(null);
  const [growthData, setGrowthData] = useState<any>(null);
  const [pendingTasks, setPendingTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    if (id) {
      loadAllData();
    }
  }, [id]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [m, v, g, t] = await Promise.all([
        apiClient.getMember(id as string),
        apiClient.getVisionDashboard(id as string),
        apiClient.getGrowthDashboard(id as string),
        apiClient.getReviewTasks()
      ]);
      setMember(m);
      setVisionData(v);
      setGrowthData(g);
      // 仅显示该成员的待审核项
      setPendingTasks((t || []).filter((task: any) => task.member_id === id));
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  // 将 API 返回的 {date, value, side} 格式转换为 TrendChart 期望的 {date, left, right} 格式
  const transformSeries = (series: any[]) => {
    if (!series || series.length === 0) return [];
    
    // 按日期分组
    const byDate = new Map<string, { date: string; left?: number; right?: number; value?: number }>();
    
    for (const item of series) {
      const date = item.date;
      if (!byDate.has(date)) {
        byDate.set(date, { date });
      }
      const entry = byDate.get(date)!;
      
      if (item.side === 'left') {
        entry.left = item.value;
      } else if (item.side === 'right') {
        entry.right = item.value;
      } else {
        // 没有 side 的指标（如身高、体重）
        entry.value = item.value;
      }
    }
    
    return Array.from(byDate.values());
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin text-blue-600"><TrendingUp size={32} /></div>
      </div>
    );
  }

  return (
    <main className="max-w-4xl mx-auto p-4 md:p-8 space-y-8 pb-32 bg-slate-50 min-h-screen">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push('/')} className="p-2 hover:bg-white rounded-full transition-all text-slate-400">
            <ChevronLeft size={24} />
          </button>
          <div className="bg-blue-600 rounded-full p-2.5 text-white shadow-lg shadow-blue-500/20">
            <User size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold font-sans tracking-tight text-slate-800">{member?.name}</h1>
            <p className="text-xs text-slate-500">{member?.date_of_birth} · {member?.gender}</p>
          </div>
        </div>
        <button 
          onClick={() => router.push(`/members/${id}/edit`)}
          className="p-3 text-slate-400 hover:text-blue-600 hover:bg-white rounded-2xl transition-all"
        >
          <Settings size={22} />
        </button>
      </header>

      {/* 待审核项 (如有) */}
      {pendingTasks.length > 0 && (
        <section className="glass-card rounded-[32px] p-6 border-l-4 border-amber-400 shadow-xl shadow-amber-900/5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-amber-50 p-2.5 rounded-2xl text-amber-500">
              <AlertCircle size={24} />
            </div>
            <div>
              <p className="font-bold text-slate-800">有待确认的检查单 ({pendingTasks.length})</p>
              <p className="text-xs text-slate-500">智能分析需要人工核实</p>
            </div>
          </div>
          <button 
            onClick={() => router.push('/review')}
            className="bg-amber-500 hover:bg-amber-600 text-white px-5 py-2.5 rounded-2xl font-bold text-sm shadow-lg shadow-amber-500/20 active:scale-95 transition-all"
          >
            去核查
          </button>
        </section>
      )}

      {/* 视力与眼轴看板 (儿童特供) */}
      {member?.member_type === 'child' && (
        <section className="space-y-6">
          <div className="flex items-center justify-between px-2">
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <Eye size={20} className="text-blue-500" /> 近视防控看板
            </h2>
            <button 
              onClick={() => router.push(`/members/${id}/trends?metric=axial_length`)}
              className="text-xs font-bold text-blue-600 flex items-center gap-1 hover:bg-blue-50 px-3 py-1.5 rounded-full transition-all"
            >
              详细趋势 <ArrowUpRight size={14} />
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="glass-card rounded-[32px] p-6 space-y-4 hover:shadow-xl transition-all group">
                 <TrendChart data={transformSeries(visionData?.axial_length?.series || [])} metric="axial_length" height={180} />
              </div>
             
             <div className="glass-card rounded-[32px] p-6 flex flex-col justify-between hover:shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-slate-700">生长速度预警</h3>
                  <div className={`p-1.5 rounded-lg ${visionData?.axial_length?.alert_status === 'warning' ? 'bg-red-50 text-red-500' : 'bg-green-50 text-green-500'}`}>
                    <AlertCircle size={18} />
                  </div>
                </div>
                {visionData?.growth_deviation ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-slate-50 rounded-2xl">
                      <p className="text-[10px] text-slate-400 font-bold uppercase mb-1">预计年增长</p>
                      <p className="text-3xl font-black text-slate-800 tracking-tighter">
                        {visionData.axial_length?.growth_rate != null 
                          ? `${visionData.axial_length.growth_rate >= 0 ? '+' : ''}${visionData.axial_length.growth_rate.toFixed(2)}`
                          : 'N/A'} 
                        <span className="text-sm font-normal text-slate-400 ml-1">mm/year</span>
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-slate-400 py-8 text-center italic">
                    近期数据不足，无法计算增长率
                  </div>
                )}
             </div>
          </div>
        </section>
      )}

      {/* 生长发育看板 */}
      <section className="space-y-6">
        <div className="flex items-center justify-between px-2">
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <TrendingUp size={20} className="text-green-500" /> 生长发育看板
          </h2>
          <button 
            onClick={() => router.push(`/members/${id}/trends?metric=height`)}
            className="text-xs font-bold text-blue-600 flex items-center gap-1 hover:bg-blue-50 px-3 py-1.5 rounded-full transition-all"
          >
            指标详情 <ArrowUpRight size={14} />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-card rounded-[32px] p-6 hover:shadow-xl transition-all">
            <TrendChart data={transformSeries(growthData?.height?.series || [])} metric="height" height={180} />
          </div>
          <div className="glass-card rounded-[32px] p-6 hover:shadow-xl transition-all">
            <TrendChart data={transformSeries(growthData?.weight?.series || [])} metric="weight" height={180} />
          </div>
        </div>
      </section>

      {/* Global Upload Trigger */}
      <div className="fixed bottom-10 left-1/2 -translate-x-1/2 z-50">
        <button
          onClick={() => setShowUpload(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-5 rounded-[24px] shadow-2xl shadow-blue-600/40 font-bold flex items-center gap-3 active:scale-95 transition-all text-lg group"
        >
          <Camera size={24} className="group-hover:scale-110 transition-transform" />
          录入新检查单
        </button>
      </div>

      {showUpload && (
        <UploadOverlay 
          memberId={id as string} 
          apiClient={apiClient} 
          onClose={() => setShowUpload(false)} 
          onSuccess={() => loadAllData()}
        />
      )}
    </main>
  );
}
