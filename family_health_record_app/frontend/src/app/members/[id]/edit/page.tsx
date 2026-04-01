'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { MemberForm } from '@/components/forms/MemberForm';
import { apiClient } from '@/app/api/client';
import { Trash2, AlertTriangle } from 'lucide-react';

export default function EditMemberPage() {
  const router = useRouter();
  const { id } = useParams();
  const [member, setMember] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
       loadMember();
    }
  }, [id]);

  const loadMember = async () => {
    try {
      const data = await apiClient.getMember(id as string);
      setMember(data);
    } catch (err) {
      console.error('Failed to load member:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (data: any) => {
    try {
      await apiClient.updateMember(id as string, data);
      router.push(`/members/${id}`);
    } catch (err) {
      console.error('Failed to update member:', err);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('确认删除该成员？历史检查记录将保留但不再展示。')) {
      try {
        await apiClient.deleteMember(id as string);
        router.push('/');
      } catch (err) {
        console.error('Failed to delete member:', err);
      }
    }
  };

  if (loading) return null;

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <MemberForm
          title="修改成员档案"
          submitLabel="更新信息"
          initialData={member}
          onSubmit={handleSubmit}
          onCancel={() => router.back()}
        />

        <div className="glass-card rounded-3xl p-6 border-l-4 border-red-400 bg-red-50/20">
          <div className="flex items-start gap-4">
            <div className="bg-red-50 p-2.5 rounded-2xl text-red-500">
              <AlertTriangle size={20} />
            </div>
            <div className="flex-1">
              <h3 className="font-bold text-slate-800">危险操作</h3>
              <p className="text-xs text-slate-500 mt-1">删除成员将导致该成员无法在列表中显示。</p>
              <button 
                onClick={handleDelete}
                className="mt-4 flex items-center gap-2 text-red-600 font-bold text-sm bg-red-100 hover:bg-red-200 px-4 py-2 rounded-xl transition-all"
              >
                <Trash2 size={16} /> 删除此成员
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
