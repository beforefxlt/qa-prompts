import React, { useState, useEffect } from 'react';
import { X, User, Heart, Baby, Accessibility } from 'lucide-react';

export type MemberType = 'child' | 'adult' | 'senior';

interface MemberFormProps {
  initialData?: {
    id?: string;
    name: string;
    gender: string;
    date_of_birth: string;
    member_type: string;
  };
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
  title: string;
  submitLabel: string;
}

export const MemberForm: React.FC<MemberFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  title,
  submitLabel,
}) => {
  const [isMounted, setIsMounted] = useState(false);
  const [loading, setLoading] = useState(false);

  const reverseGenderMap: Record<string, string> = { 'male': '男', 'female': '女' };
  const [formData, setFormData] = useState({
    name: initialData?.name || '',
    gender: reverseGenderMap[initialData?.gender || ''] || initialData?.gender || '男',
    birthYear: initialData?.date_of_birth ? initialData.date_of_birth.split('-')[0] : '',
    birthMonth: initialData?.date_of_birth ? parseInt(initialData.date_of_birth.split('-')[1]).toString() : '',
    member_type: initialData?.member_type || 'child',
  });

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.birthYear || !formData.birthMonth) {
      alert('请选择完整的出生年月');
      return;
    }
    
    setLoading(true);
    try {
      const formattedDate = `${formData.birthYear}-${formData.birthMonth.padStart(2, '0')}-01`;
      const genderMap: Record<string, string> = { '男': 'male', '女': 'female' };
      await onSubmit({
        name: formData.name,
        gender: genderMap[formData.gender] || formData.gender,
        date_of_birth: formattedDate,
        member_type: formData.member_type,
      });
    } catch (err) {
      console.error('Submit failed:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isMounted) {
    return (
      <div className="glass-card rounded-3xl p-6 md:p-8 flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 120 }, (_, i) => currentYear - i);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);

  return (
    <div className="glass-card rounded-3xl p-6 md:p-8 space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-blue-50 p-2 rounded-xl text-blue-600">
            <User size={24} />
          </div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">{title}</h2>
        </div>
        <button onClick={onCancel} className="text-slate-400 hover:text-slate-600 transition-colors p-2 hover:bg-slate-50 rounded-full">
          <X size={20} />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="group">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2 px-1">姓名</label>
          <input
            type="text"
            required
            maxLength={50}
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full bg-slate-50 border-2 border-transparent rounded-2xl p-4 transition-all focus:bg-white focus:border-blue-500/20 focus:ring-4 focus:ring-blue-500/5 outline-none font-medium"
            placeholder="请输入姓名"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2 px-1">性别</label>
            <select
              value={formData.gender}
              onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
              className="w-full bg-slate-50 border-2 border-transparent rounded-2xl p-4 transition-all focus:bg-white focus:border-blue-500/20 outline-none font-medium"
            >
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2 px-1">成员类型</label>
            <select
              value={formData.member_type}
              onChange={(e) => setFormData({ ...formData, member_type: e.target.value })}
              className="w-full bg-slate-50 border-2 border-transparent rounded-2xl p-4 transition-all focus:bg-white focus:border-blue-500/20 outline-none font-medium"
            >
              <option value="child">儿童</option>
              <option value="adult">成人</option>
              <option value="senior">老人</option>
            </select>
          </div>
        </div>

        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2 px-1">出生年月</label>
          <div className="grid grid-cols-2 gap-4">
            <select
              value={formData.birthYear}
              onChange={(e) => setFormData({ ...formData, birthYear: e.target.value })}
              className="w-full bg-slate-50 border-2 border-transparent rounded-2xl p-4 transition-all focus:bg-white focus:border-blue-500/20 outline-none font-medium"
              required
            >
              <option value="">年份</option>
              {years.map(y => <option key={y} value={y}>{y} 年</option>)}
            </select>
            <select
              value={formData.birthMonth}
              onChange={(e) => setFormData({ ...formData, birthMonth: e.target.value })}
              className="w-full bg-slate-50 border-2 border-transparent rounded-2xl p-4 transition-all focus:bg-white focus:border-blue-500/20 outline-none font-medium"
              required
            >
              <option value="">月份</option>
              {months.map(m => <option key={m} value={m}>{m} 月</option>)}
            </select>
          </div>
        </div>

        <div className="pt-4 flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 py-4 px-6 text-slate-500 font-bold hover:bg-slate-50 rounded-2xl transition-all"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex-[2] bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white py-4 px-8 rounded-2xl font-bold shadow-xl shadow-blue-500/30 active:scale-95 transition-all flex items-center justify-center gap-2"
          >
            {loading ? <span>正在保存...</span> : <span>{submitLabel}</span>}
          </button>
        </div>
      </form>
    </div>
  );
};
