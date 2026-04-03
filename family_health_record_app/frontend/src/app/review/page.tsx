'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  ChevronRight, FileText, AlertTriangle, CheckCircle, XCircle, Save, RefreshCw, Eye, Clock
} from 'lucide-react';
import { apiClient } from '../api/client';

type ReviewTask = {
  id: string;
  document_id: string;
  status: string;
  created_at?: string;
  member_name?: string;
  document_type?: string;
};

type ReviewTaskDetail = {
  id: string;
  document_id: string;
  status: string;
  ocr_raw_json: Record<string, any>;
  ocr_processed_items: Record<string, any>;
  confidence_score: number;
  rule_conflict_details: { error?: string[]; conflicts?: Array<{ field: string; reason: string }> };
  audit_trail: { events: Array<{ action: string; timestamp: string; user?: string }> };
  image_url?: string;
  document_type?: string;
  member_name?: string;
};

const STATUS_LABELS: Record<string, string> = {
  pending: '待审核',
  in_review: '审核中',
  approved: '已入库',
  rejected: '已退回',
  draft: '草稿',
};

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-amber-100 text-amber-700',
  in_review: 'bg-blue-100 text-blue-700',
  approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  draft: 'bg-slate-100 text-slate-600',
};

const FIELD_LABELS: Record<string, string> = {
  exam_date: '检查日期',
  left_axial_length: '左眼轴长 (mm)',
  right_axial_length: '右眼轴长 (mm)',
  left_vision: '左眼视力',
  right_vision: '右眼视力',
  left_sphere: '左眼球镜 (D)',
  right_sphere: '右眼球镜 (D)',
  left_cylinder: '左眼柱镜 (D)',
  right_cylinder: '右眼柱镜 (D)',
  left_axis: '左眼轴位 (°)',
  right_axis: '右眼轴位 (°)',
  intraocular_pressure_left: '左眼眼压 (mmHg)',
  intraocular_pressure_right: '右眼眼压 (mmHg)',
  notes: '备注',
};

function ConfidenceBar({ score }: { score: number }) {
  const color = score >= 0.8 ? 'bg-green-500' : score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500';
  const bgColor = score >= 0.8 ? 'bg-green-50' : score >= 0.6 ? 'bg-yellow-50' : 'bg-red-50';
  const textColor = score >= 0.8 ? 'text-green-700' : score >= 0.6 ? 'text-yellow-700' : 'text-red-700';
  const label = score >= 0.8 ? '高置信度' : score >= 0.6 ? '中等置信度' : '低置信度，请仔细核对';

  return (
    <div className={`rounded-xl p-3 ${bgColor}`}>
      <div className="flex items-center justify-between mb-2">
        <span className={`text-xs font-bold ${textColor}`}>OCR 置信度</span>
        <span className={`text-xs font-bold ${textColor}`}>{(score * 100).toFixed(0)}%</span>
      </div>
      <div className="w-full bg-white/50 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${Math.min(score * 100, 100)}%` }}
        />
      </div>
      <p className={`text-[10px] mt-1 ${textColor}`}>{label}</p>
    </div>
  );
}

function ConflictAlert({ conflicts }: { conflicts: string[] | Array<{ field: string; reason: string }> | undefined }) {
  if (!conflicts || conflicts.length === 0) return null;

  const messages = conflicts.map((c) =>
    typeof c === 'string' ? c : `${FIELD_LABELS[c.field] || c.field}: ${c.reason}`
  );

  return (
    <div className="rounded-xl bg-red-50 border border-red-200 p-4 space-y-2">
      <div className="flex items-center gap-2 text-red-700">
        <AlertTriangle size={18} />
        <span className="text-sm font-bold">规则冲突警告</span>
      </div>
      <ul className="space-y-1">
        {messages.map((msg, i) => (
          <li key={i} className="text-xs text-red-600 flex items-start gap-2">
            <span className="mt-0.5 w-1.5 h-1.5 bg-red-400 rounded-full flex-shrink-0" />
            {msg}
          </li>
        ))}
      </ul>
    </div>
  );
}

function FieldEditor({
  label,
  value,
  isConflict,
  onChange,
  type = 'text',
}: {
  label: string;
  value: any;
  isConflict: boolean;
  onChange: (val: string) => void;
  type?: string;
}) {
  // 处理 [object Object] 问题：如果是数组（如 observations），将其转换为可读字符串
  const displayValue = Array.isArray(value) 
    ? value.map(v => `${FIELD_LABELS[v.metric_code] || v.metric_code}: ${v.value_numeric}${v.unit || ''}${v.side ? `(${v.side})` : ''}`).join(', ')
    : typeof value === 'object' ? JSON.stringify(value) : value;

  return (
    <div className="space-y-1">
      <label className="text-xs font-bold text-slate-400 uppercase block">{label}</label>
      {Array.isArray(value) ? (
        <div className={`w-full rounded-xl p-3 border text-sm ${isConflict ? 'bg-red-50 border-red-300' : 'bg-slate-50 border-transparent'}`}>
            {value.map((v, i) => (
                <div key={i} className="flex justify-between border-b last:border-0 border-slate-200 py-1">
                    <span className="text-slate-600 font-medium">{FIELD_LABELS[v.metric_code] || v.metric_code}</span>
                    <span className="text-blue-600 font-bold">{v.value_numeric}{v.unit} {v.side && <span className="text-[10px] opacity-50 uppercase">{v.side}</span>}</span>
                </div>
            ))}
        </div>
      ) : (
        <input
          type={type}
          value={displayValue ?? ''}
          onChange={(e) => onChange(e.target.value)}
          className={`w-full rounded-xl p-3 border transition-all focus:ring-2 focus:ring-blue-500 focus:outline-none ${
            isConflict
              ? 'bg-red-50 border-red-300 text-red-800'
              : 'bg-slate-50 border-transparent'
          }`}
        />
      )}
    </div>
  );
}

export default function ReviewPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ReviewTaskDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [editedItems, setEditedItems] = useState<Record<string, any>>({});
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTasks();
  }, []);

  async function loadTasks() {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getReviewTasks();
      const list = Array.isArray(data) ? data : data.tasks || data.items || [];
      setTasks(list);
    } catch (e: any) {
      console.error('Failed to load review tasks:', e);
      setError(e.message || '加载审核任务失败');
      setTasks([]);
    } finally {
      setLoading(false);
    }
  }

  async function loadTaskDetail(taskId: string) {
    try {
      setDetailLoading(true);
      setSelectedTaskId(taskId);
      setError(null);
      const data = await apiClient.getReviewTask(taskId);
      setDetail(data);
      // 同时保留其它非 metric 字段如 exam_date, institution 等
      setEditedItems(data.ocr_processed_items || {});
    } catch (e: any) {
      console.error('Failed to load task detail:', e);
      setError(e.message || '加载任务详情失败');
    } finally {
      setDetailLoading(false);
    }
  }

  function handleFieldChange(field: string, value: string) {
    const num = parseFloat(value);
    setEditedItems((prev) => ({ ...prev, [field]: !isNaN(num) && value !== '' ? num : value }));
  }

  async function handleAction(action: 'approve' | 'reject' | 'draft') {
    if (!selectedTaskId) return;
    setActionLoading(action);
    try {
      const revisedItems: any[] = [];
      
      for (const [key, value] of Object.entries(editedItems)) {
        if (key === 'exam_date') {
          revisedItems.push({ metric_code: 'exam_date', value });
        } else if (key === 'observations' && Array.isArray(value)) {
          for (const obs of value) {
            revisedItems.push({
              metric_code: obs.metric_code,
              side: obs.side || null,
              value_numeric: typeof obs.value_numeric === 'string' ? parseFloat(obs.value_numeric) : obs.value_numeric,
              unit: obs.unit || '',
            });
          }
        } else if (typeof value === 'string') {
          const num = parseFloat(value);
          if (!isNaN(num)) {
            revisedItems.push({ metric_code: key, value_numeric: num });
          } else {
            revisedItems.push({ metric_code: key, value });
          }
        } else if (typeof value === 'number') {
          revisedItems.push({ metric_code: key, value_numeric: value });
        }
      }

      switch (action) {
        case 'approve':
          await apiClient.approveReviewTask(selectedTaskId, revisedItems);
          break;
        case 'reject':
          await apiClient.rejectReviewTask(selectedTaskId);
          break;
        case 'draft':
          await apiClient.saveDraftReviewTask(selectedTaskId, revisedItems);
          break;
      }

      setSelectedTaskId(null);
      setDetail(null);
      setEditedItems({});
      await loadTasks();
    } catch (e: any) {
      console.error(`Failed to ${action} task:`, e);
      setError(e.message || `操作失败: ${action}`);
    } finally {
      setActionLoading(null);
    }
  }

  function getConflictFields(): Set<string> {
    if (!detail?.rule_conflict_details) return new Set();
    const conflicts = detail.rule_conflict_details;
    const fields = new Set<string>();

    if (Array.isArray(conflicts.conflicts)) {
      conflicts.conflicts.forEach((c) => fields.add(c.field));
    }

    if (Array.isArray(conflicts.error)) {
      conflicts.error.forEach((msg) => {
        Object.keys(FIELD_LABELS).forEach((key) => {
          if (msg.includes(FIELD_LABELS[key]) || msg.includes(key)) {
            fields.add(key);
          }
        });
      });
    }

    return fields;
  }

  const conflictFields = getConflictFields();

  const isPending = detail?.status === 'pending' || detail?.status === 'in_review' || detail?.status === 'draft';

  // Task list view
  if (!selectedTaskId) {
    return (
      <div className="max-w-4xl mx-auto p-4 md:p-8 space-y-6 pb-28">
        <header className="flex items-center gap-3">
          <button
            onClick={() => router.push('/')}
            className="p-2 text-slate-400 hover:text-blue-600 transition-colors"
          >
            <ChevronRight size={20} className="rotate-180" />
          </button>
          <div className="flex items-center gap-3">
            <div className="bg-amber-100 rounded-full p-2 text-amber-600">
              <FileText size={22} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800">OCR 识别结果审核</h1>
              <p className="text-xs text-slate-400">{tasks.length} 个待处理任务</p>
            </div>
          </div>
        </header>

        {error && (
          <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-700 flex items-center gap-2">
            <AlertTriangle size={16} />
            {error}
            <button onClick={loadTasks} className="ml-auto text-xs underline">重试</button>
          </div>
        )}

        {loading ? (
          <div className="glass-card rounded-3xl p-12 text-center">
            <RefreshCw size={32} className="mx-auto text-slate-300 animate-spin mb-4" />
            <p className="text-slate-400 text-sm">加载审核任务...</p>
          </div>
        ) : tasks.length === 0 ? (
          <div className="glass-card rounded-3xl p-12 text-center space-y-4">
            <div className="bg-green-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle size={32} className="text-green-500" />
            </div>
            <h2 className="text-lg font-bold text-slate-700">暂无待审核任务</h2>
            <p className="text-sm text-slate-400">所有 OCR 识别结果已处理完毕</p>
            <button
              onClick={() => router.push('/')}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              返回首页
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {tasks.map((task) => (
              <button
                key={task.id}
                onClick={() => loadTaskDetail(task.id)}
                className="glass-card rounded-2xl p-5 w-full text-left hover:shadow-lg transition-all active:scale-[0.98] group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="bg-amber-50 rounded-full p-3 text-amber-600 group-hover:bg-amber-100 transition-colors">
                      <Eye size={20} />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-800">
                        {task.member_name || task.document_type || `文档 #${task.document_id.slice(0, 8)}`}
                      </p>
                      <div className="flex items-center gap-2 mt-1 text-xs text-slate-400">
                        <Clock size={12} />
                        <span>{task.created_at ? new Date(task.created_at).toLocaleString('zh-CN') : '未知时间'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${STATUS_COLORS[task.status] || 'bg-slate-100 text-slate-600'}`}>
                      {STATUS_LABELS[task.status] || task.status}
                    </span>
                    <ChevronRight size={18} className="text-slate-300 group-hover:text-blue-500 transition-colors" />
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Detail view
  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-6 pb-32">
      <header className="flex items-center gap-3">
        <button
          onClick={() => {
            setSelectedTaskId(null);
            setDetail(null);
            setEditedItems({});
          }}
          className="p-2 text-slate-400 hover:text-blue-600 transition-colors"
        >
          <ChevronRight size={20} className="rotate-180" />
        </button>
        <div className="flex items-center gap-3">
          <div className="bg-amber-100 rounded-full p-2 text-amber-600">
            <FileText size={22} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">OCR 识别结果审核</h1>
            <p className="text-xs text-slate-400">任务 #{selectedTaskId.slice(0, 8)}</p>
          </div>
        </div>
        {detail && (
          <span className={`ml-auto text-xs px-2.5 py-1 rounded-full font-medium ${STATUS_COLORS[detail.status] || 'bg-slate-100 text-slate-600'}`}>
            {STATUS_LABELS[detail.status] || detail.status}
          </span>
        )}
      </header>

      {error && (
        <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-700 flex items-center gap-2">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      {detailLoading ? (
        <div className="glass-card rounded-3xl p-12 text-center">
          <RefreshCw size={32} className="mx-auto text-slate-300 animate-spin mb-4" />
          <p className="text-slate-400 text-sm">加载任务详情...</p>
        </div>
      ) : detail ? (
        <>
          {/* Confidence Score */}
          <ConfidenceBar score={detail.confidence_score ?? 0} />

          {/* Rule Conflict Alerts */}
          <ConflictAlert
            conflicts={detail.rule_conflict_details?.error || detail.rule_conflict_details?.conflicts}
          />

          {/* Main Content: Two Column Layout */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left: Image Preview */}
            <div className="glass-card rounded-3xl p-6 space-y-4">
              <h2 className="text-sm font-bold text-slate-600 flex items-center gap-2">
                <Eye size={16} />
                脱敏图预览
              </h2>
              <div className="bg-slate-100 rounded-2xl aspect-[3/4] flex items-center justify-center overflow-hidden border border-slate-200">
                {detail.image_url ? (
                  <img
                    src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${detail.image_url}`}
                    alt="脱敏文档预览"
                    className="w-full h-full object-contain"
                    onError={(e) => {
                      console.error('Image load failed');
                      (e.target as HTMLImageElement).src = 'https://placehold.co/400x600/f1f5f9/94a3b8?text=Image+Load+Failed';
                    }}
                  />
                ) : (
                  <div className="text-center text-slate-400">
                    <FileText size={48} className="mx-auto mb-3 opacity-50" />
                    <p className="text-sm">文档预览区域</p>
                    <p className="text-xs mt-1">文档 ID: {detail.document_id.slice(0, 8)}</p>
                  </div>
                )}
              </div>
              {detail.member_name && (
                <p className="text-xs text-slate-500">
                  成员: <span className="font-medium">{detail.member_name}</span>
                </p>
              )}
              {detail.document_type && (
                <p className="text-xs text-slate-500">
                  类型: <span className="font-medium">{detail.document_type}</span>
                </p>
              )}
            </div>

            {/* Right: Structured Fields Form */}
            <div className="glass-card rounded-3xl p-6 space-y-4">
              <h2 className="text-sm font-bold text-slate-600 flex items-center gap-2">
                <FileText size={16} />
                结构化字段
              </h2>
              <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
                {Object.entries(editedItems).map(([key, value]) => (
                  <FieldEditor
                    key={key}
                    label={FIELD_LABELS[key] || key}
                    value={value}
                    isConflict={conflictFields.has(key)}
                    onChange={(val) => handleFieldChange(key, val)}
                    type={key === 'exam_date' ? 'date' : 'text'}
                  />
                ))}
                {Object.keys(editedItems).length === 0 && (
                  <p className="text-sm text-slate-400 text-center py-8">暂无可编辑字段</p>
                )}
              </div>
            </div>
          </div>

          {/* Audit Trail */}
          {detail.audit_trail?.events && detail.audit_trail.events.length > 0 && (
            <div className="glass-card rounded-3xl p-6 space-y-3">
              <h2 className="text-sm font-bold text-slate-600 flex items-center gap-2">
                <Clock size={16} />
                审核轨迹
              </h2>
              <div className="space-y-2">
                {detail.audit_trail.events.map((event, i) => (
                  <div key={i} className="flex items-center gap-3 text-xs">
                    <span className="w-2 h-2 bg-blue-400 rounded-full flex-shrink-0" />
                    <span className="text-slate-500 flex-1">{event.action}</span>
                    <span className="text-slate-400">
                      {new Date(event.timestamp).toLocaleString('zh-CN')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="glass-card rounded-3xl p-12 text-center">
          <p className="text-slate-400 text-sm">无法加载任务详情</p>
        </div>
      )}

      {/* Fixed Bottom Action Bar */}
      {detail && isPending && (
        <div className="fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-lg border-t border-slate-200 p-4 z-50">
          <div className="max-w-6xl mx-auto flex items-center gap-3">
            <button
              onClick={() => handleAction('reject')}
              disabled={!!actionLoading}
              className="flex-1 md:flex-none px-6 py-3 rounded-xl border-2 border-red-200 text-red-600 font-semibold hover:bg-red-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 active:scale-95"
            >
              <XCircle size={18} />
              退回重识别
            </button>
            <button
              onClick={() => handleAction('draft')}
              disabled={!!actionLoading}
              className="flex-1 md:flex-none px-6 py-3 rounded-xl border-2 border-slate-200 text-slate-600 font-semibold hover:bg-slate-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 active:scale-95"
            >
              <Save size={18} />
              保存草稿
            </button>
            <button
              onClick={() => handleAction('approve')}
              disabled={!!actionLoading}
              className="flex-1 md:flex-none px-8 py-3 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-700 shadow-lg shadow-blue-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 active:scale-95"
            >
              {actionLoading === 'approve' ? (
                <RefreshCw size={18} className="animate-spin" />
              ) : (
                <CheckCircle size={18} />
              )}
              确认入库
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
