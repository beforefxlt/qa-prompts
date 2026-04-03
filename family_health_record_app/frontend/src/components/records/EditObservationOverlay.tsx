'use client';

import React, { useState } from 'react';
import { X, Save, Edit3 } from 'lucide-react';
import { UI_TEXT } from '@/constants/ui-text';

export function EditObservationOverlay({ 
  obsId, 
  initialValue, 
  label,
  unit,
  onClose, 
  onSuccess,
  apiClient 
}: { 
  obsId: string; 
  initialValue: number;
  label: string;
  unit: string;
  onClose: () => void; 
  onSuccess: () => void;
  apiClient: any;
}) {
  const [value, setValue] = useState(initialValue.toString());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    const num = parseFloat(value);
    if (isNaN(num) || num <= 0) {
        setError('请输入有效数字（必须大于 0）');
        return;
    }
    
    setLoading(true);
    setError(null);
    try {
      await apiClient.updateObservation(obsId, num);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || '更新失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[110] flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-[28px] w-full max-w-sm shadow-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-blue-50 p-1.5 rounded-lg text-blue-600">
              <Edit3 size={18} />
            </div>
            <h2 className="font-bold text-slate-800">修改{label}</h2>
          </div>
          <button onClick={onClose} className="text-slate-300 hover:text-slate-500 transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-xl text-xs font-medium border border-red-100">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-slate-400 uppercase px-1">新数值 ({unit})</label>
            <div className="relative">
              <input 
                type="number" 
                step="0.01"
                autoFocus
                value={value}
                onChange={e => setValue(e.target.value)}
                className="w-full bg-slate-50 border-2 border-transparent focus:border-blue-500 focus:bg-white rounded-2xl p-4 text-xl font-black text-slate-800 transition-all outline-none"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300 font-bold">{unit}</span>
            </div>
          </div>
        </div>

        <div className="p-5 bg-slate-50 flex gap-3">
          <button 
            onClick={onClose}
            className="flex-1 py-3 rounded-xl text-slate-500 font-bold hover:bg-slate-200 transition-all text-sm"
          >
            取消
          </button>
          <button 
            onClick={handleSubmit}
            disabled={loading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl shadow-lg shadow-blue-500/20 font-bold flex items-center justify-center gap-2 active:scale-95 disabled:opacity-50 transition-all text-sm"
          >
            {loading ? <Save size={16} className="animate-spin" /> : <Save size={16} />}
            保存
          </button>
        </div>
      </div>
    </div>
  );
}
