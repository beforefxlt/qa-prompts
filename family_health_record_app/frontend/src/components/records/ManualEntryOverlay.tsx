'use client';

import React, { useState } from 'react';
import { X, Plus, Trash2, Save, Calendar, Landmark, Activity, Eye } from 'lucide-react';
import { UI_TEXT } from '@/constants/ui-text';

type SingleObservationInput = {
  metric_code: string;
  value_numeric: number;
  unit: string;
  side: null;
};

type EyeObservationInput = {
  metric_code: 'axial_length' | 'vision_acuity';
  left_value: number | null;
  right_value: number | null;
  unit: string;
};

type ObservationRow = {
  id: string;
} & (SingleObservationInput | EyeObservationInput);

const METRIC_OPTIONS = [
  { code: 'height', label: '身高', unit: 'cm', min: 30, max: 250 },
  { code: 'weight', label: '体重', unit: 'kg', min: 2, max: 500 },
  { code: 'axial_length', label: '眼轴长度', unit: 'mm', min: 15, max: 35 },
  { code: 'vision_acuity', label: '视力', unit: 'decimal' },
];

const EYE_METRICS = ['axial_length', 'vision_acuity'];

function isEyeInput(row: ObservationRow): row is ObservationRow & EyeObservationInput {
  return EYE_METRICS.includes(row.metric_code);
}

let rowIdCounter = 0;

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
  const [rows, setRows] = useState<ObservationRow[]>([
    { id: `row-${rowIdCounter++}`, metric_code: 'height', value_numeric: NaN as any, unit: 'cm', side: null }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addRow = () => {
    setRows([...rows, { id: `row-${rowIdCounter++}`, metric_code: 'height', value_numeric: NaN as any, unit: 'cm', side: null }]);
  };

  const removeRow = (id: string) => {
    setRows(rows.filter(r => r.id !== id));
  };

  const updateMetricCode = (id: string, newCode: string) => {
    const option = METRIC_OPTIONS.find(o => o.code === newCode);
    setRows(rows.map(r => {
      if (r.id !== id) return r;
      if (EYE_METRICS.includes(newCode)) {
        return { id: r.id, metric_code: newCode as 'axial_length' | 'vision_acuity', left_value: null, right_value: null, unit: option?.unit || '' };
      }
      return { id: r.id, metric_code: newCode, value_numeric: NaN as any, unit: option?.unit || '', side: null };
    }));
  };

  const handleSubmit = async () => {
    if (rows.length === 0) {
      setError('请至少添加一个指标');
      return;
    }

    const observations: Array<{ metric_code: string; value_numeric: number; unit: string; side: string | null }> = [];

    for (const row of rows) {
      if (isEyeInput(row)) {
        if (row.left_value !== null) {
          const metric = METRIC_OPTIONS.find(m => m.code === row.metric_code);
          if (metric?.min !== undefined && metric?.max !== undefined) {
            if (row.left_value < metric.min || row.left_value > metric.max) {
              setError(`${metric.label} 左眼数值 ${row.left_value} 超出合理范围 (${metric.min}-${metric.max})`);
              return;
            }
          }
          observations.push({
            metric_code: row.metric_code,
            value_numeric: row.left_value,
            unit: row.unit,
            side: 'left',
          });
        }
        if (row.right_value !== null) {
          const metric = METRIC_OPTIONS.find(m => m.code === row.metric_code);
          if (metric?.min !== undefined && metric?.max !== undefined) {
            if (row.right_value < metric.min || row.right_value > metric.max) {
              setError(`${metric.label} 右眼数值 ${row.right_value} 超出合理范围 (${metric.min}-${metric.max})`);
              return;
            }
          }
          observations.push({
            metric_code: row.metric_code,
            value_numeric: row.right_value,
            unit: row.unit,
            side: 'right',
          });
        }
      } else {
        if (isNaN(row.value_numeric) || row.value_numeric <= 0) {
          const metric = METRIC_OPTIONS.find(m => m.code === row.metric_code);
          setError(`请为「${metric?.label || row.metric_code}」填写有效数值（必须大于 0 且在合理范围内）`);
          return;
        }
        const metric = METRIC_OPTIONS.find(m => m.code === row.metric_code);
        if (metric?.min !== undefined && metric?.max !== undefined) {
          if (row.value_numeric < metric.min || row.value_numeric > metric.max) {
            setError(`${metric.label} 数值 ${row.value_numeric} 超出合理范围 (${metric.min}-${metric.max})`);
            return;
          }
        }
        observations.push({
          metric_code: row.metric_code,
          value_numeric: row.value_numeric,
          unit: row.unit,
          side: null,
        });
      }
    }

    if (observations.length === 0) {
      setError('请至少填写一个指标的数值');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await apiClient.createManualExam(memberId, {
        exam_date: examDate,
        institution_name: institution,
        observations,
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
                onClick={addRow}
                className="text-xs font-bold text-blue-600 flex items-center gap-1 hover:bg-blue-50 px-3 py-1.5 rounded-full transition-all"
              >
                <Plus size={14} /> {UI_TEXT.BTN_ADD_METRIC}
              </button>
            </div>

            <div className="space-y-3">
              {rows.map((row) => (
                <div key={row.id} className="bg-slate-50 rounded-2xl p-4 border border-transparent hover:border-slate-200 transition-all">
                  <div className="flex items-start gap-3">
                    <div className="w-36 space-y-1 shrink-0">
                      <label className="text-[10px] font-bold text-slate-400 uppercase px-1">类型</label>
                      <select
                        value={row.metric_code}
                        onChange={e => updateMetricCode(row.id, e.target.value)}
                        className="w-full bg-white rounded-xl p-2.5 text-sm border-transparent focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
                      >
                        {METRIC_OPTIONS.map(opt => (
                          <option key={opt.code} value={opt.code}>{opt.label}</option>
                        ))}
                      </select>
                    </div>

                    {isEyeInput(row) ? (
                      <div className="flex-1 grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-slate-400 uppercase px-1 flex items-center gap-1">
                            <Eye size={10} /> 左眼 ({row.unit})
                          </label>
                          <input
                            type="number"
                            step="0.01"
                            placeholder="—"
                            value={row.left_value ?? ''}
                            onChange={e => {
                              const val = e.target.value === '' ? null : parseFloat(e.target.value);
                              setRows(rows.map(r => r.id === row.id ? { ...r, left_value: val } : r));
                            }}
                            className="w-full bg-white rounded-xl p-2.5 text-sm border-transparent focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-slate-400 uppercase px-1 flex items-center gap-1">
                            <Eye size={10} /> 右眼 ({row.unit})
                          </label>
                          <input
                            type="number"
                            step="0.01"
                            placeholder="—"
                            value={row.right_value ?? ''}
                            onChange={e => {
                              const val = e.target.value === '' ? null : parseFloat(e.target.value);
                              setRows(rows.map(r => r.id === row.id ? { ...r, right_value: val } : r));
                            }}
                            className="w-full bg-white rounded-xl p-2.5 text-sm border-transparent focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
                          />
                        </div>
                      </div>
                    ) : (
                      <div className="flex-1 space-y-1">
                        <label className="text-[10px] font-bold text-slate-400 uppercase px-1">数值 ({row.unit})</label>
                        <input
                          type="number"
                          step="0.01"
                          value={row.value_numeric || ''}
                          onChange={e => {
                            const val = e.target.value === '' ? NaN : parseFloat(e.target.value);
                            setRows(rows.map(r => r.id === row.id ? { ...r, value_numeric: val } : r));
                          }}
                          className="w-full bg-white rounded-xl p-2.5 text-sm border-transparent focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
                        />
                      </div>
                    )}

                    <button
                      onClick={() => removeRow(row.id)}
                      className="p-2.5 text-slate-300 hover:text-red-500 transition-colors mt-5 shrink-0"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
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
