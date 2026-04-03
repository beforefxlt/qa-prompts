'use client';

import React, { useState } from 'react';
import { X, Plus, Trash2, Save, Calendar, Landmark, Activity } from 'lucide-react';
import { UI_TEXT } from '@/constants/ui-text';

type ObservationInput = {
  metric_code: string;
  value_numeric: number;
  unit: string;
  side: string | null;
};

const METRIC_OPTIONS = [
  { code: 'height', label: '身高', unit: 'cm', min: 30, max: 250 },
  { code: 'weight', label: '体重', unit: 'kg', min: 2, max: 500 },
  { code: 'axial_length', label: '眼轴长度', unit: 'mm', min: 15, max: 35 },
  { code: 'vision_acuity', label: '视力', unit: 'decimal' },
];

export function ManualEntryOverlay({ 
  memberId, 
  onClose, 
  onSuccess,
  apiClient 
}: { 
  memberId: string; 
  onClose: () => void; 
  onSuccess: () => void;
  apiClient: any;
}) {
  const [examDate, setExamDate] = useState(new Date().toISOString().split('T')[0]);
  const [institution, setInstitution] = useState('');
  const [observations, setObservations] = useState<ObservationInput[]>([
    { metric_code: 'height', value_numeric: NaN as any, unit: 'cm', side: null }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

    const addObservation = () => {
    setObservations([...observations, { metric_code: 'height', value_numeric: NaN as any, unit: 'cm', side: null }]);
  };

  const removeObservation = (index: number) => {
    setObservations(observations.filter((_, i) => i !== index));
  };

  const updateObservation = (index: number, field: keyof ObservationInput, value: any) => {
    const newObs = [...observations];
    if (field === 'metric_code') {
      const option = METRIC_OPTIONS.find(o => o.code === value);
      newObs[index].metric_code = value;
      newObs[index].unit = option?.unit || '';
    } else {
      (newObs[index] as any)[field] = value;
    }
    setObservations(newObs);
  };

  const handleSubmit = async () => {
    if (observations.length === 0) {
        setError('请至少添加一个指标');
        return;
    }
    
    const hasInvalidValue = observations.some(o => {
      if (isNaN(o.value_numeric) || o.value_numeric <= 0) return true;
      const metric = METRIC_OPTIONS.find(m => m.code === o.metric_code);
      if (metric?.min !== undefined && metric?.max !== undefined) {
        return o.value_numeric < metric.min || o.value_numeric > metric.max;
      }
      return false;
    });
    if (hasInvalidValue) {
        setError('请为所有指标填写有效数值（必须大于 0 且在合理范围内）');
        return;
    }
    
    setLoading(true);
    setError(null);
    try {
      await apiClient.createManualExam(memberId, {
        exam_date: examDate,
        institution_name: institution,
        observations: observations
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || '录入失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-[100] flex items-center justify-center p-4 animate-in fade-in duration-300">
      <div className="bg-white rounded-[32px] w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-300">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="bg-blue-100 p-2 rounded-xl text-blue-600">
              <Activity size={24} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-800">{UI_TEXT.ACTION_MANUAL_ENTRY}</h2>
              <p className="text-xs text-slate-400">填写纸质检查单上的具体数值</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-200 rounded-full transition-colors text-slate-400">
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {error && (
            <div className="bg-red-50 text-red-600 p-4 rounded-2xl text-sm font-medium border border-red-100 animate-shake whitespace-pre-wrap">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 px-1">
                <Calendar size={12} /> {UI_TEXT.LABEL_EXAM_DATE}
              </label>
              <input 
                type="date" 
                value={examDate}
                onChange={e => setExamDate(e.target.value)}
                className="w-full bg-slate-50 border-transparent focus:bg-white focus:ring-2 focus:ring-blue-500 rounded-2xl p-3.5 text-sm transition-all"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1.5 px-1">
                <Landmark size={12} /> {UI_TEXT.LABEL_INSTITUTION}
              </label>
              <input 
                type="text" 
                placeholder="例如：市第一眼科医院"
                value={institution}
                onChange={e => setInstitution(e.target.value)}
                className="w-full bg-slate-50 border-transparent focus:bg-white focus:ring-2 focus:ring-blue-500 rounded-2xl p-3.5 text-sm transition-all"
              />
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between px-1">
              <label className="text-xs font-bold text-slate-400 uppercase">{UI_TEXT.LABEL_OBSERVATIONS}</label>
              <button 
                onClick={addObservation}
                className="text-xs font-bold text-blue-600 flex items-center gap-1 hover:bg-blue-50 px-3 py-1.5 rounded-full transition-all"
              >
                <Plus size={14} /> {UI_TEXT.BTN_ADD_METRIC}
              </button>
            </div>

            <div className="space-y-3">
              {observations.map((obs, idx) => (
                <div key={idx} className="bg-slate-50 rounded-2xl p-4 flex flex-wrap md:flex-nowrap items-end gap-3 border border-transparent hover:border-slate-200 transition-all">
                  <div className="flex-1 min-w-[120px] space-y-1">
                    <label className="text-[10px] font-bold text-slate-400 uppercase px-1">类型</label>
                    <select 
                      value={obs.metric_code}
                      onChange={e => updateObservation(idx, 'metric_code', e.target.value)}
                      className="w-full bg-white rounded-xl p-2.5 text-sm border-transparent focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
                    >
                      {METRIC_OPTIONS.map(opt => (
                        <option key={opt.code} value={opt.code}>{opt.label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="flex-1 min-w-[100px] space-y-1">
                    <label className="text-[10px] font-bold text-slate-400 uppercase px-1">数值 ({obs.unit})</label>
                    <input 
                      type="number" 
                      step="0.01"
                      value={obs.value_numeric || ''}
                      onChange={e => updateObservation(idx, 'value_numeric', parseFloat(e.target.value))}
                      className="w-full bg-white rounded-xl p-2.5 text-sm border-transparent focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
                    />
                  </div>

                  {['axial_length', 'vision_acuity'].includes(obs.metric_code) && (
                    <div className="w-24 space-y-1">
                      <label className="text-[10px] font-bold text-slate-400 uppercase px-1">侧向</label>
                      <select 
                        value={obs.side || ''}
                        onChange={e => updateObservation(idx, 'side', e.target.value || null)}
                        className="w-full bg-white rounded-xl p-2.5 text-sm border-transparent focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
                      >
                        <option value="">通用</option>
                        <option value="left">左眼</option>
                        <option value="right">右眼</option>
                      </select>
                    </div>
                  )}

                  <button 
                    onClick={() => removeObservation(idx)}
                    className="p-2.5 text-slate-300 hover:text-red-500 transition-colors mb-0.5"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-3">
          <button 
            onClick={onClose}
            className="px-6 py-3 rounded-2xl text-slate-500 font-bold hover:bg-slate-200 transition-all active:scale-95 text-sm"
          >
            取消
          </button>
          <button 
            onClick={handleSubmit}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-10 py-3 rounded-2xl shadow-lg shadow-blue-600/20 font-bold flex items-center gap-2 active:scale-95 disabled:opacity-50 transition-all text-sm"
          >
            {loading ? <Save size={18} className="animate-spin" /> : <Save size={18} />}
            保存记录
          </button>
        </div>
      </div>
    </div>
  );
}
