'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea
} from 'recharts';
import {
  ShieldAlert, Settings, Camera, User, Plus, ChevronRight, FileText, AlertCircle, X
} from 'lucide-react';
import { apiClient } from './api/client';

type TrendPoint = {
  date: string;
  value: number;
};

type ChartPoint = {
  date: string;
  left: number;
  right: number;
};

type Member = {
  id: string;
  name: string;
  gender: string;
  date_of_birth: string;
  member_type: string;
  last_check_date?: string;
  pending_review_count?: number;
};

const MEMBER_TYPE_LABELS: Record<string, string> = {
  child: '儿童',
  adult: '成人',
  senior: '老人',
};

const MEMBER_TYPE_COLORS: Record<string, string> = {
  child: 'bg-blue-100 text-blue-700',
  adult: 'bg-green-100 text-green-700',
  senior: 'bg-amber-100 text-amber-700',
};

export default function Dashboard() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const memberId = searchParams.get('memberId');
  const memberName = searchParams.get('memberName');

  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [showManualForm, setShowManualForm] = useState(false);
  const [isOCRDown, setIsOCRDown] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState('axial_length');
  const [pendingTasks, setPendingTasks] = useState<number>(0);

  // Create member form state
  const [newMember, setNewMember] = useState({
    name: '',
    gender: '男',
    date_of_birth: '',
    member_type: 'child',
  });

  // Edit member form state
  const [editMember, setEditMember] = useState({
    id: '',
    name: '',
    gender: '',
    date_of_birth: '',
    member_type: '',
  });

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load members on mount
  useEffect(() => {
    loadMembers();
    loadPendingTasks();
  }, []);

  async function loadPendingTasks() {
    try {
      const tasks = await apiClient.getReviewTasks();
      setPendingTasks((tasks || []).length);
    } catch {
      setPendingTasks(0);
    }
  }

  // Load chart data when memberId changes
  useEffect(() => {
    if (memberId) {
      loadChartData(memberId);
    }
  }, [memberId]);

  async function loadMembers() {
    try {
      const data = await apiClient.getMembers();
      const normalized = (data || []).map((m: any) => ({
        ...m,
        id: m.id || m.member_id,
        member_id: m.id || m.member_id,
      }));
      setMembers(normalized);
    } catch (e) {
      console.error('Failed to load members:', e);
      setMembers([]);
    } finally {
      setLoading(false);
    }
  }

  async function loadChartData(mid: string, metric?: string) {
    const targetMetric = metric || selectedMetric;
    try {
      const trends = await apiClient.getTrends(mid, targetMetric);
      const formatted = (trends.series || []).map((s: any) => ({
        date: s.date.slice(5),
        left: s.side === 'left' ? s.value : (s.side === 'right' ? undefined : s.value),
        right: s.side === 'right' ? s.value : undefined,
      })).reduce((acc: any[], curr: any) => {
        const existing = acc.find((item) => item.date === curr.date);
        if (existing) {
          if (curr.left !== undefined) existing.left = curr.left;
          if (curr.right !== undefined) existing.right = curr.right;
        } else {
          acc.push({
            date: curr.date,
            left: curr.left ?? (acc.length > 0 ? acc[acc.length - 1].left : 0),
            right: curr.right ?? (acc.length > 0 ? (acc[acc.length - 1].right ?? acc[acc.length - 1].left - 0.3) : 0),
          });
        }
        return acc;
      }, []);
      setChartData(formatted);
    } catch {
      console.error('Failed to load trends');
      setChartData([]);
    }
  }

  function handleMetricChange(metric: string) {
    setSelectedMetric(metric);
    if (memberId) {
      loadChartData(memberId, metric);
    }
  }

  function handleEditMember(member: Member) {
    setEditMember({
      id: member.id,
      name: member.name,
      gender: member.gender,
      date_of_birth: member.date_of_birth,
      member_type: member.member_type,
    });
    setShowEditForm(true);
  }

  async function handleUpdateMember(e: React.FormEvent) {
    e.preventDefault();
    try {
      await apiClient.updateMember(editMember.id, {
        name: editMember.name,
        gender: editMember.gender,
        date_of_birth: editMember.date_of_birth,
        member_type: editMember.member_type,
      });
      setShowEditForm(false);
      await loadMembers();
    } catch (err) {
      console.error('Failed to update member:', err);
    }
  }

  async function handleDeleteMember(memberId: string) {
    if (!confirm('确认删除该成员？历史检查数据将保留但不再展示。')) return;
    try {
      await apiClient.deleteMember(memberId);
      await loadMembers();
      if (searchParams.get('memberId') === memberId) {
        router.push('/');
      }
    } catch (err) {
      console.error('Failed to delete member:', err);
    }
  }

  async function handleCreateMember(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await apiClient.createMember(newMember);
      setShowCreateForm(false);
      setNewMember({ name: '', gender: '男', date_of_birth: '', member_type: 'child' });
      await loadMembers();
      // Auto navigate to the new member's dashboard
      router.push(`/?memberId=${created.member_id}&memberName=${encodeURIComponent(created.name)}`);
    } catch (e) {
      console.error('Failed to create member:', e);
    }
  }

  function handleSelectMember(member: Member) {
    router.push(`/?memberId=${member.id}&memberName=${encodeURIComponent(member.name)}`);
  }

  function handleBackToList() {
    router.push('/');
  }

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !memberId) return;

    setIsUploading(true);
    try {
      const uploadRes = await apiClient.uploadDocument(file, memberId);
      await apiClient.submitOcr(uploadRes.document_id);
      await loadChartData(memberId);
      setIsUploading(false);
    } catch {
      setIsOCRDown(true);
      setIsUploading(false);
    }
  };

  // Empty state: no members
  if (!loading && members.length === 0) {
    return (
      <div className="max-w-4xl mx-auto p-4 md:p-8 min-h-screen flex flex-col items-center justify-center">
        {!showCreateForm ? (
          <div className="glass-card rounded-3xl p-8 md:p-12 text-center space-y-6 max-w-md w-full">
            <div className="bg-blue-50 w-20 h-20 rounded-full flex items-center justify-center mx-auto">
              <User size={40} className="text-blue-600" />
            </div>
            <h1 className="text-2xl font-bold text-slate-800 tracking-tight">
              欢迎使用家庭检查单管理
            </h1>
            <p className="text-slate-500 text-sm leading-relaxed">
              请先添加家庭成员，才能开始记录检查数据
            </p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-2xl shadow-xl shadow-blue-400/30 font-bold flex items-center gap-2 mx-auto active:scale-95 transition-all"
            >
              <Plus size={20} />
              添加第一位成员
            </button>
          </div>
        ) : (
          <div className="glass-card rounded-3xl p-8 max-w-md w-full space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-slate-800">添加成员</h2>
              <button onClick={() => setShowCreateForm(false)} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreateMember} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-400 uppercase block mb-1">姓名</label>
                <input
                  type="text"
                  required
                  value={newMember.name}
                  onChange={(e) => setNewMember({ ...newMember, name: e.target.value })}
                  className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500"
                  placeholder="请输入姓名"
                />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-400 uppercase block mb-1">性别</label>
                <select
                  value={newMember.gender}
                  onChange={(e) => setNewMember({ ...newMember, gender: e.target.value })}
                  className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500"
                >
                  <option value="男">男</option>
                  <option value="女">女</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-bold text-slate-400 uppercase block mb-1">出生日期</label>
                <input
                  type="date"
                  required
                  value={newMember.date_of_birth}
                  onChange={(e) => setNewMember({ ...newMember, date_of_birth: e.target.value })}
                  className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-400 uppercase block mb-1">成员类型</label>
                <select
                  value={newMember.member_type}
                  onChange={(e) => setNewMember({ ...newMember, member_type: e.target.value })}
                  className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500"
                >
                  <option value="child">儿童</option>
                  <option value="adult">成人</option>
                  <option value="senior">老人</option>
                </select>
              </div>
              <button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-2xl font-bold shadow-lg shadow-blue-500/30 active:scale-95 transition-all"
              >
                保存
              </button>
            </form>
          </div>
        )}
      </div>
    );
  }

  // Member list view (no specific member selected)
  if (!memberId) {
    return (
      <div className="max-w-4xl mx-auto p-4 md:p-8 space-y-6 pb-28">
        <header className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-slate-800">家庭成员</h1>
          <button className="p-2 text-slate-400 hover:text-blue-600 transition-colors">
            <Settings size={20} />
          </button>
        </header>

        <div className="space-y-3">
          {members.map((m) => (
            <button
              key={m.id}
              onClick={() => handleSelectMember(m)}
              className="glass-card rounded-2xl p-5 w-full text-left hover:shadow-lg transition-all active:scale-[0.98] flex items-center justify-between group"
            >
              <div className="flex items-center gap-4">
                <div className="bg-blue-50 rounded-full p-3 text-blue-600 group-hover:bg-blue-100 transition-colors">
                  <User size={22} />
                </div>
                <div>
                  <p className="font-semibold text-slate-800">{m.name}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${MEMBER_TYPE_COLORS[m.member_type] || 'bg-slate-100 text-slate-600'}`}>
                    {MEMBER_TYPE_LABELS[m.member_type] || m.member_type}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-3 text-right">
                <div className="text-xs text-slate-400">
                  {m.last_check_date ? (
                    <span>{m.last_check_date} 最后检查</span>
                  ) : (
                    <span className="flex items-center gap-1 text-amber-500">
                      <FileText size={12} /> 无记录
                    </span>
                  )}
                  {m.pending_review_count && m.pending_review_count > 0 && (
                    <span className="flex items-center gap-1 text-red-500 ml-2">
                      <AlertCircle size={12} /> {m.pending_review_count} 待审核
                    </span>
                  )}
                </div>
                <ChevronRight size={18} className="text-slate-300 group-hover:text-blue-500 transition-colors" />
              </div>
              {/* Edit/Delete actions */}
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={(e) => { e.stopPropagation(); handleEditMember(m); }}
                  className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
                  title="编辑"
                >
                  <Settings size={14} />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDeleteMember(m.id); }}
                  className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                  title="删除"
                >
                  <X size={14} />
                </button>
              </div>
            </button>
          ))}
        </div>

        <button
          onClick={() => setShowCreateForm(true)}
          className="w-full border-2 border-dashed border-slate-200 rounded-2xl p-4 text-slate-400 hover:border-blue-400 hover:text-blue-500 transition-all flex items-center justify-center gap-2"
        >
          <Plus size={18} />
          添加成员
        </button>

        {/* Create member modal */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-end md:items-center justify-center p-4 animate-in fade-in">
            <div className="glass-card rounded-3xl p-6 max-w-md w-full space-y-5 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-slate-800">添加成员</h2>
                <button onClick={() => setShowCreateForm(false)} className="text-slate-400 hover:text-slate-600">
                  <X size={20} />
                </button>
              </div>
              <form onSubmit={handleCreateMember} className="space-y-4">
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase block mb-1">姓名</label>
                  <input
                    type="text"
                    required
                    value={newMember.name}
                    onChange={(e) => setNewMember({ ...newMember, name: e.target.value })}
                    className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500"
                    placeholder="请输入姓名"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase block mb-1">性别</label>
                  <select
                    value={newMember.gender}
                    onChange={(e) => setNewMember({ ...newMember, gender: e.target.value })}
                    className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="男">男</option>
                    <option value="女">女</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase block mb-1">出生日期</label>
                  <input
                    type="date"
                    required
                    value={newMember.date_of_birth}
                    onChange={(e) => setNewMember({ ...newMember, date_of_birth: e.target.value })}
                    className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase block mb-1">成员类型</label>
                  <select
                    value={newMember.member_type}
                    onChange={(e) => setNewMember({ ...newMember, member_type: e.target.value })}
                    className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="child">儿童</option>
                    <option value="adult">成人</option>
                    <option value="senior">老人</option>
                  </select>
                </div>
                <button
                  type="submit"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-2xl font-bold shadow-lg shadow-blue-500/30 active:scale-95 transition-all"
                >
                  保存
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Edit member modal */}
        {showEditForm && (
          <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-end md:items-center justify-center p-4 animate-in fade-in">
            <div className="glass-card rounded-3xl p-6 max-w-md w-full space-y-5 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-slate-800">编辑成员</h2>
                <button onClick={() => setShowEditForm(false)} className="text-slate-400 hover:text-slate-600">
                  <X size={20} />
                </button>
              </div>
              <form onSubmit={handleUpdateMember} className="space-y-4">
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase block mb-1">姓名</label>
                  <input
                    type="text"
                    required
                    value={editMember.name}
                    onChange={(e) => setEditMember({ ...editMember, name: e.target.value })}
                    className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase block mb-1">性别</label>
                  <select
                    value={editMember.gender}
                    onChange={(e) => setEditMember({ ...editMember, gender: e.target.value })}
                    className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="男">男</option>
                    <option value="女">女</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase block mb-1">出生日期</label>
                  <input
                    type="date"
                    required
                    value={editMember.date_of_birth}
                    onChange={(e) => setEditMember({ ...editMember, date_of_birth: e.target.value })}
                    className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase block mb-1">成员类型</label>
                  <select
                    value={editMember.member_type}
                    onChange={(e) => setEditMember({ ...editMember, member_type: e.target.value })}
                    className="w-full bg-slate-50 border-none rounded-xl p-3 focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="child">儿童</option>
                    <option value="adult">成人</option>
                    <option value="senior">老人</option>
                  </select>
                </div>
                <button
                  type="submit"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-2xl font-bold shadow-lg shadow-blue-500/30 active:scale-95 transition-all"
                >
                  保存修改
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Fixed upload button */}
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2">
          <input
            type="file"
            accept="image/*"
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileChange}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="bg-slate-400 text-white px-6 py-3 rounded-full shadow-lg font-semibold flex items-center gap-2 active:scale-95 transition-all"
          >
            <Camera size={18} />
            录入新检查单
          </button>
          <p className="text-[10px] text-slate-400 text-center mt-2">请先选择成员</p>
        </div>
      </div>
    );
  }

  // Member dashboard view (existing logic, now with real memberId)
  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8 space-y-8 pb-20">
      {/* 1. Header & Member Switcher */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={handleBackToList} className="text-slate-400 hover:text-blue-600 transition-colors">
            <ChevronRight size={20} className="rotate-180" />
          </button>
          <div className="bg-blue-600 rounded-full p-2 text-white">
            <User size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold font-sans tracking-tight">{memberName}</h1>
            <p className="text-xs text-slate-500">2026/03/30 最后更新</p>
          </div>
        </div>
        <button className="p-2 text-slate-400 hover:text-blue-600 transition-colors">
          <Settings size={20} />
        </button>
      </header>

      {/* 2. Dashboard - Main Charts (Plugin Based) */}
      <section className="space-y-6">
        {/* Metric Switcher */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {[
            { key: 'axial_length', label: '眼轴' },
            { key: 'height', label: '身高' },
            { key: 'weight', label: '体重' },
            { key: 'vision_acuity', label: '视力' },
            { key: 'glucose', label: '血糖' },
            { key: 'tc', label: '总胆固醇' },
            { key: 'tg', label: '甘油三酯' },
            { key: 'hdl', label: 'HDL' },
            { key: 'ldl', label: 'LDL' },
          ].map((m) => (
            <button
              key={m.key}
              onClick={() => handleMetricChange(m.key)}
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                selectedMetric === m.key
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-400/30'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        {/* Chart Card */}
        <div className="glass-card rounded-3xl p-6 relative overflow-hidden">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-semibold text-slate-700 flex items-center gap-2">
              <span className="w-2 h-6 bg-blue-500 rounded-full"></span>
              {selectedMetric === 'axial_length' && '儿童眼轴 (Axial Length)'}
              {selectedMetric === 'height' && '身高 (Height)'}
              {selectedMetric === 'weight' && '体重 (Weight)'}
              {selectedMetric === 'vision_acuity' && '视力 (Vision Acuity)'}
              {selectedMetric === 'glucose' && '血糖 (Glucose)'}
              {selectedMetric === 'tc' && '总胆固醇 (TC)'}
              {selectedMetric === 'tg' && '甘油三酯 (TG)'}
              {selectedMetric === 'hdl' && '高密度脂蛋白 (HDL)'}
              {selectedMetric === 'ldl' && '低密度脂蛋白 (LDL)'}
            </h3>
            {chartData.length > 0 && (
              <span className="text-xs font-medium px-2 py-1 bg-green-50 text-green-600 rounded-full">
                {chartData.length} 条记录
              </span>
            )}
          </div>

          <div className="h-[240px] w-full">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                  />
                  <ReferenceArea y1={22.5} y2={24} fill="#10b981" fillOpacity={0.05} />
                  <Line type="monotone" dataKey="left" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4, fill: '#3b82f6' }} activeDot={{ r: 6 }} />
                  <Line type="monotone" dataKey="right" stroke="#60a5fa" strokeDasharray="5 5" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                暂无数据，上传检查单后自动展示
              </div>
            )}
          </div>

          {chartData.length > 0 && (
            <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-slate-100">
              <div>
                <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">左 / 当前</p>
                <p className="text-2xl font-bold text-slate-800 tracking-tighter">
                  {chartData[chartData.length - 1].left.toFixed(1)}
                  <span className="text-sm font-normal text-slate-400"> {selectedMetric === 'axial_length' ? 'mm' : selectedMetric === 'height' ? 'cm' : selectedMetric === 'weight' ? 'kg' : ''}</span>
                </p>
              </div>
              <div>
                <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">右 / 上次</p>
                <p className="text-2xl font-bold text-slate-800 tracking-tighter">
                  {chartData.length > 1 ? chartData[chartData.length - 2].left.toFixed(1) : '--'}
                  <span className="text-sm font-normal text-slate-400"> {selectedMetric === 'axial_length' ? 'mm' : selectedMetric === 'height' ? 'cm' : selectedMetric === 'weight' ? 'kg' : ''}</span>
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Pending Review Tasks */}
        {pendingTasks > 0 && (
          <div className="glass-card rounded-3xl p-6 border-l-4 border-amber-400">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertCircle className="text-amber-500" size={24} />
                <div>
                  <p className="font-semibold text-slate-700">待审核检查单 ({pendingTasks})</p>
                  <p className="text-xs text-slate-400">有检查单需要人工确认</p>
                </div>
              </div>
              <button
                onClick={() => router.push('/review')}
                className="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all"
              >
                去审核
              </button>
            </div>
          </div>
        )}
      </section>

      {/* 3. Global Upload & Fallback Trigger */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-4">
        {!showManualForm && (
          <button
            onClick={() => setIsOCRDown(!isOCRDown)}
            className={`text-[10px] px-3 py-1 rounded-full transition-all ${isOCRDown ? 'bg-red-500 text-white' : 'bg-slate-200 text-slate-500'}`}
          >
             模拟接口状态: {isOCRDown ? '500 ERROR' : '200 OK'}
          </button>
        )}

        <input
          type="file"
          accept="image/*"
          className="hidden"
          ref={fileInputRef}
          onChange={handleFileChange}
        />

        <button
          onClick={() => {
            if (isOCRDown) {
               setShowManualForm(true);
            } else {
               fileInputRef.current?.click();
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
