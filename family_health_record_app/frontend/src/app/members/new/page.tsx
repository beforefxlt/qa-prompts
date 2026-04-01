'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { MemberForm } from '@/components/forms/MemberForm';
import { apiClient } from '@/app/api/client';

export default function CreateMemberPage() {
  const router = useRouter();

  const handleSubmit = async (data: any) => {
    try {
      const created = await apiClient.createMember(data);
      // 创建成功后，根据 v2.0.0 导航流返回首页
      router.push('/');
    } catch (err) {
      console.error('Failed to create member:', err);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md">
        <MemberForm
          title="添加新成员"
          submitLabel="保存并开始记录"
          onSubmit={handleSubmit}
          onCancel={() => router.back()}
        />
      </div>
    </main>
  );
}
