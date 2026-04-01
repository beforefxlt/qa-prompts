'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { MemberForm } from '@/components/forms/MemberForm';
import { apiClient } from '@/app/api/client';

export default function CreateMemberPage() {
  const router = useRouter();
  const [isMounted, setIsMounted] = React.useState(false);

  React.useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleSubmit = async (data: any) => {
    try {
      console.log('Sending data to backend:', data);
      const created = await apiClient.createMember(data);
      console.log('Member created successfully:', created);
      // 创建成功后返回首页，触发刷新
      router.push('/');
      router.refresh();
    } catch (err: any) {
      console.error('Failed to create member:', err);
      alert(`保存失败: ${err.message}`);
    }
  };

  if (!isMounted) return null;

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md animate-in fade-in zoom-in duration-300">
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
