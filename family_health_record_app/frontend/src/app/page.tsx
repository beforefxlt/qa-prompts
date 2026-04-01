'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  User, Plus, ChevronRight, Settings, 
  FileText, AlertCircle, TrendingUp, Calendar,
  RotateCcw
} from 'lucide-react';
import { apiClient } from '@/app/api/client';

export default function HomePage() {
  const router = useRouter();
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    // 延迟加载以确保 Hydration 完成
    const timer = setTimeout(() => {
      loadMembers();
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  const loadMembers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getMembers();
      setMembers(data || []);
    } catch (err: any) {
      console.error('Failed to load members:', err);
      setError(err.message || '无法连接到服务器，请检查后端状态');
    } finally {
      setLoading(false);
    }
  };

  const MEMBER_TYPE_LABELS: Record<string, string> = {
    child: '儿童',
    adult: '成人',
    senior: '老人',
  };

  const MEMBER_TYPE_COLORS: Record<string, string> = {
    child: 'bg-blue-100 text-blue-700 border-blue-200',
    adult: 'bg-green-100 text-green-700 border-green-200',
    senior: 'bg-amber-100 text-amber-700 border-amber-200',
  };

  // 严格的 Hydration 保护：挂载前仅渲染骨架，挂载后渲染完整内容
  if (!isMounted) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center gap-2">
          <div className="w-12 h-12 bg-blue-100 rounded-2xl flex items-center justify-center text-blue-500">
            <TrendingUp size={24} />
          </div>
          <div className="h-2 w-16 bg-slate-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center">
        <div className="glass-card rounded-[40px] p-10 max-w-md w-full space-y-6 shadow-2xl">
          <div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mx-auto text-red-500">
            <AlertCircle size={40} />
          </div>
          <div className="space-y-2">
            <h1 className="text-xl font-bold text-slate-800">服务连接异常</h1>
            <p className="text-slate-500 text-sm leading-relaxed">{error}</p>
          </div>
          <button
            onClick={loadMembers}
            className="w-full bg-slate-900 hover:bg-slate-800 text-white py-4 rounded-2xl font-bold transition-all flex items-center justify-center gap-2"
          >
            <RotateCcw size={20} />
            <span>重试连接</span>
          </button>
        </div>
      </main>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center text-blue-600">
             <TrendingUp size={32} />
          </div>
          <p className="text-slate-400 font-bold text-xs tracking-widest uppercase">SYMBOLS LOADING</p>
        </div>
      </div>
    );
  }

  return (
    <main className="max-w-4xl mx-auto p-4 md:p-8 space-y-8 bg-slate-50 min-h-screen pb-20">
      <header className="flex items-center justify-between px-2">
        <div className="flex items-center gap-3">
           <div className="w-10 h-10 bg-blue-600 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
             <TrendingUp size={24} />
           </div>
           <h1 className="text-2xl font-black text-slate-800 tracking-tighter">家庭成员</h1>
        </div>
        <button className="p-3 text-slate-400 hover:text-blue-600 hover:bg-white rounded-2xl transition-all">
          <Settings size={22} />
        </button>
      </header>

      {members.length === 0 ? (
        <div className="glass-card rounded-[40px] p-10 md:p-16 max-w-md mx-auto w-full space-y-8 shadow-2xl shadow-blue-900/5 text-center">
          <div className="w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center mx-auto text-blue-600 shadow-inner">
            <User size={48} />
          </div>
          <div className="space-y-4">
            <h1 className="text-2xl font-bold text-slate-800 tracking-tight">欢迎使用家庭检查单管理</h1>
            <div className="text-slate-500 text-sm leading-relaxed space-y-1">
              <p>记录家人健康足迹，从添加第一位成员开始。</p>
              <p>我们将为您智能分析等核心指标趋势。</p>
            </div>
          </div>
          <button
            onClick={() => router.push('/members/new')}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-5 rounded-[24px] font-bold shadow-xl shadow-blue-500/30 active:scale-95 transition-all text-lg flex items-center justify-center gap-2"
          >
            <Plus size={24} />
            <span>添加第一位成员</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {members.map((m) => (
            <button
              key={m.id}
              onClick={() => router.push(`/members/${m.id}`)}
              className="group glass-card rounded-[32px] p-6 text-left hover:shadow-2xl hover:shadow-slate-200 transition-all active:scale-[0.98] border-2 border-transparent hover:border-blue-500/10 flex flex-col justify-between min-h-[160px]"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-white rounded-[20px] flex items-center justify-center text-blue-600 shadow-sm group-hover:bg-blue-600 group-hover:text-white transition-all duration-500">
                    <User size={28} />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-800 tracking-tight">{m.name}</h3>
                    <div className={`mt-1 inline-block text-[10px] px-2.5 py-1 rounded-full font-black uppercase border tracking-widest ${MEMBER_TYPE_COLORS[m.member_type]}`}>
                       {MEMBER_TYPE_LABELS[m.member_type]}
                    </div>
                  </div>
                </div>
                <div className="text-right flex flex-col items-end opacity-40 group-hover:opacity-100 transition-all">
                  <ChevronRight size={24} className="text-slate-300 group-hover:text-blue-500 transition-colors" />
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                 <span className="flex items-center gap-1.5 font-medium">
                    <Calendar size={14} className="text-slate-300" />
                    {m.last_check_date ? `${m.last_check_date} 最后检查` : '尚无记录'}
                 </span>
                 {m.pending_review_count > 0 && (
                   <span className="flex items-center gap-1 text-red-500 font-bold px-2 py-1 bg-red-50 rounded-lg">
                      <AlertCircle size={12} /> {m.pending_review_count} 待核
                   </span>
                 )}
              </div>
            </button>
          ))}

          <button
            onClick={() => router.push('/members/new')}
            className="border-2 border-dashed border-slate-200 rounded-[32px] p-6 text-slate-400 hover:border-blue-400 hover:text-blue-500 hover:bg-blue-50/30 transition-all flex flex-col items-center justify-center gap-3 min-h-[160px] group"
          >
            <div className="bg-white p-3 rounded-2xl shadow-sm group-hover:shadow-md transition-shadow">
              <Plus size={28} />
            </div>
            <span className="font-bold tracking-tight">添加家庭成员</span>
          </button>
        </div>
      )}

      <footer className="fixed bottom-10 left-1/2 -translate-x-1/2 w-full max-w-sm px-6">
         <div className="bg-slate-900/90 backdrop-blur-xl rounded-[24px] p-3 flex items-center justify-between shadow-2xl">
            <button className="flex-1 flex flex-col items-center gap-1 text-blue-400">
               <TrendingUp size={24} />
               <span className="text-[10px] font-black uppercase">成员</span>
            </button>
            <div className="w-px h-6 bg-white/10"></div>
            <button 
              onClick={() => router.push('/review')}
              className="flex-1 flex flex-col items-center gap-1 text-slate-400 hover:text-white transition-colors"
            >
               <FileText size={24} />
               <span className="text-[10px] font-black uppercase">审核箱</span>
            </button>
         </div>
      </footer>
    </main>
  );
}
