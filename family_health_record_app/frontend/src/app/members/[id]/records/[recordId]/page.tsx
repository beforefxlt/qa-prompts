'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ChevronLeft, Calendar, MapPin, Layout, ZoomIn, FileText } from 'lucide-react';
import { apiClient } from '@/app/api/client';

export default function RecordDetailPage() {
  const router = useRouter();
  const { id, recordId } = useParams();
  const [record, setRecord] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (recordId) {
      loadRecord();
    }
  }, [recordId]);

  const loadRecord = async () => {
    try {
      const data = await apiClient.getExamRecord(recordId as string);
      setRecord(data);
    } catch (err) {
      console.error('Failed to load record:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return null;

  return (
    <main className="max-w-4xl mx-auto p-4 md:p-8 space-y-6 bg-slate-50 min-h-screen pb-20">
      <header className="flex items-center gap-4">
        <button onClick={() => router.back()} className="p-2 hover:bg-white rounded-full transition-all text-slate-400">
          <ChevronLeft size={24} />
        </button>
        <div>
          <h1 className="text-xl font-bold text-slate-800">检查详情</h1>
          <p className="text-xs text-slate-500">记录 ID: {recordId?.slice(0, 8)}</p>
        </div>
      </header>

      {/* 1. 基础信息卡片 */}
      <section className="glass-card rounded-[32px] p-6 grid grid-cols-2 gap-4">
         <div className="flex items-center gap-3">
            <div className="bg-blue-50 p-2 rounded-xl text-blue-500">
              <Calendar size={20} />
            </div>
            <div>
              <p className="text-[10px] text-slate-400 font-bold uppercase">检查日期</p>
              <p className="font-bold text-slate-800">{record?.exam_date}</p>
            </div>
         </div>
         <div className="flex items-center gap-3">
            <div className="bg-slate-100 p-2 rounded-xl text-slate-500">
              <MapPin size={20} />
            </div>
            <div>
              <p className="text-[10px] text-slate-400 font-bold uppercase">检查机构</p>
              <p className="font-bold text-slate-800 truncate">{record?.institution || '未知机构'}</p>
            </div>
         </div>
      </section>

      {/* 2. 原始图预览 */}
      <section className="space-y-4">
         <h2 className="text-lg font-bold text-slate-800 px-2 flex items-center gap-2">
            <Layout size={18} className="text-blue-500" /> 原始检查单 (脱敏预览)
         </h2>
         <div className="glass-card rounded-[32px] overflow-hidden relative group">
            {record?.document?.desensitized_url ? (
              <img 
                src={record.document.desensitized_url} 
                alt="Exam Record" 
                className="w-full h-auto object-cover min-h-[300px]"
              />
            ) : (
              <div className="h-64 bg-slate-100 flex items-center justify-center text-slate-400">
                <FileText size={48} className="opacity-20" />
              </div>
            )}
            <div className="absolute top-4 right-4 bg-white/80 backdrop-blur-md p-2 rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity">
               <ZoomIn size={20} className="text-slate-600" />
            </div>
         </div>
      </section>

      {/* 3. 指标详情列表 */}
      <section className="space-y-4">
         <h2 className="text-lg font-bold text-slate-800 px-2 flex items-center gap-2">
            <FileText size={18} className="text-blue-500" /> 提取指标列表
         </h2>
         <div className="space-y-3">
            {record?.observations?.map((obs: any, idx: number) => (
              <div key={idx} className="glass-card rounded-2xl p-5 flex items-center justify-between">
                 <div className="flex items-center gap-4">
                    <div className="w-1.5 h-8 bg-blue-500 rounded-full"></div>
                    <div>
                       <p className="font-bold text-slate-800">
                         {obs.metric_code === 'axial_length' ? '眼轴长度' : 
                          obs.metric_code === 'vision_acuity' ? '视力' : 
                          obs.metric_code === 'height' ? '身高' : 
                          obs.metric_code === 'weight' ? '体重' : obs.metric_code}
                       </p>
                       <p className="text-[10px] text-slate-400 font-bold uppercase">
                          {obs.side ? (obs.side === 'left' ? '左侧 (Left)' : '右侧 (Right)') : '单侧/通用'}
                       </p>
                    </div>
                 </div>
                 <div className="text-right">
                    <p className={`text-xl font-black tracking-tighter ${obs.is_abnormal ? 'text-red-500' : 'text-slate-800'}`}>
                       {obs.value_numeric || obs.value_text}
                       <span className="text-xs font-normal text-slate-400 ml-1">{obs.unit}</span>
                    </p>
                    {obs.is_abnormal && (
                      <span className="text-[10px] bg-red-50 text-red-500 px-2 py-0.5 rounded-full font-bold">异常情况</span>
                    )}
                 </div>
              </div>
            ))}
         </div>
      </section>
    </main>
  );
}
