'use client';

import React, { useState } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea 
} from 'recharts';
import { 
  Plus, Upload, ShieldAlert, CheckCircle2, ChevronRight, Settings, Camera, User
} from 'lucide-react';
import { apiClient } from './api/client';

export default function Dashboard() {
  const [chartData, setChartData] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [showManualForm, setShowManualForm] = useState(false);
  const [selectedMember, setSelectedMember] = useState('女儿 (晓萌)');
  const [memberId, setMemberId] = useState('0'); // 示例 UUID 占位

  // 模拟 OCR 宕机容灾状态
  const [isOCRDown, setIsOCRDown] = useState(false);

  React.useEffect(() => {
    async function loadData() {
      try {
        const trends = await apiClient.getTrends(memberId, 'axial_length');
        // 将后端接口格式适配为 Recharts 格式
        const formatted = trends.series.map((s: any) => ({
          date: s.date.slice(5), // 只保留 MM-DD
          left: s.value, 
          right: s.value - 0.3 // 模拟右眼偏移
        }));
        setChartData(formatted);
      } catch (err) {
        console.error('Failed to load trends:', err);
      }
    }
    loadData();
  }, [memberId]);

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8 space-y-8 pb-20">
      {/* 1. Header & Member Switcher */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 rounded-full p-2 text-white">
            <User size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold font-sans tracking-tight">{selectedMember}</h1>
            <p className="text-xs text-slate-500">2026/03/30 最后更新</p>
          </div>
        </div>
        <button className="p-2 text-slate-400 hover:text-blue-600 transition-colors">
          <Settings size={20} />
        </button>
      </header>

      {/* 2. Dashboard - Main Charts (Plugin Based) */}
      <section className="grid grid-cols-1 md:grid-cols-1 gap-6">
        {/* 指标卡片: 儿童眼轴 (动态渲染示例) */}
        <div className="glass-card rounded-3xl p-6 relative overflow-hidden">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-semibold text-slate-700 flex items-center gap-2">
              <span className="w-2 h-6 bg-blue-500 rounded-full"></span>
              儿童眼轴 (Axial Length)
            </h3>
            <span className="text-xs font-medium px-2 py-1 bg-green-50 text-green-600 rounded-full">
              正向增长中
            </span>
          </div>

          <div className="h-[240px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis domain={[22, 25]} stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                />
                {/* 合规参考带: 23-24mm 为正常示例区 */}
                <ReferenceArea y1={22.5} y2={24} fill="#10b981" fillOpacity={0.05} />
                <Line type="monotone" dataKey="left" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4, fill: '#3b82f6' }} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="right" stroke="#60a5fa" strokeDasharray="5 5" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-slate-100">
            <div>
              <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">左眼 L</p>
              <p className="text-2xl font-bold text-slate-800 tracking-tighter">23.5 <span className="text-sm font-normal text-slate-400">mm</span></p>
            </div>
            <div>
              <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">右眼 R</p>
              <p className="text-2xl font-bold text-slate-800 tracking-tighter">23.2 <span className="text-sm font-normal text-slate-400">mm</span></p>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Global Upload & Fallback Trigger */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-4">
        {/* 容灾测试触发器 (仅调试，用于模拟 OCR 断开) */}
        {!showManualForm && (
          <button 
            onClick={() => setIsOCRDown(!isOCRDown)}
            className={`text-[10px] px-3 py-1 rounded-full transition-all ${isOCRDown ? 'bg-red-500 text-white' : 'bg-slate-200 text-slate-500'}`}
          >
             模拟接口状态: {isOCRDown ? '500 ERROR' : '200 OK'}
          </button>
        )}

        <button 
          onClick={async () => {
            if (isOCRDown) {
               setShowManualForm(true);
            } else {
               setIsUploading(true);
               try {
                 // 模拟文件上传动作
                 await apiClient.uploadDocument(new File([], 'test.jpg'));
                 // 延迟模拟状态刷新
                 setTimeout(() => setIsUploading(false), 2000);
               } catch (err) {
                 setIsOCRDown(true); // 容灾自动切换
                 setIsUploading(false);
               }
            }
          }}
          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-full shadow-2xl shadow-blue-400/40 font-bold flex items-center gap-3 active:scale-95 transition-all"
        >
          <Camera size={20} />
          {isUploading ? '智能提取中...' : '录入新检查单'}
        </button>
      </div>

      {/* 4. Fallback Manual Form (Step 2 - 容灾 UI) */}
      {showManualForm && (
        <div className="fixed inset-0 bg-white/80 backdrop-blur-md z-50 p-6 flex flex-col items-center justify-center animate-in fade-in zoom-in duration-300">
           <div className="w-full max-w-sm glass-card p-8 rounded-3xl space-y-6">
              <div className="flex items-center gap-3 text-red-600 mb-4">
                <ShieldAlert size={28} />
                <h2 className="text-lg font-bold">提取失败，改为手工录入</h2>
              </div>
              <p className="text-sm text-slate-500">智能服务暂不可用，请输入当前检测项数值。</p>
              
              <div className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-400 uppercase">左眼轴 (mm)</label>
                  <input type="number" step="0.01" className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500" placeholder="23.XX" />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-400 uppercase">右眼轴 (mm)</label>
                  <input type="number" step="0.01" className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500" placeholder="23.XX" />
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button 
                  onClick={() => setShowManualForm(false)}
                  className="flex-1 py-3 text-slate-400 font-semibold"
                >
                  取消
                </button>
                <button 
                  onClick={() => setShowManualForm(false)}
                  className="flex-1 bg-blue-600 text-white py-3 rounded-2xl font-bold shadow-lg shadow-blue-500/30"
                >
                  保存数据
                </button>
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
