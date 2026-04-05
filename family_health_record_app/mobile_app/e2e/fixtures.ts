import { test as base, expect } from '@playwright/test';

const API_BASE = 'http://localhost:8000/api/v1';

/**
 * 移动端 E2E 测试 fixtures
 * 提供数据清理功能
 */
export const test = base.extend<{ cleanDb: void }>({
  cleanDb: [async ({}, use) => {
    await cleanDatabase();
    await use();
    await cleanDatabase();
  }, { auto: true }],
});

/**
 * 清理数据库所有业务数据
 */
export async function cleanDatabase() {
  try {
    const resetResp = await fetch(`${API_BASE}/admin/reset`, { method: 'POST' });
    if (resetResp.ok) return;

    const deleteOrder = [
      'admin/derived-metrics/clear',
      'admin/observations/clear',
      'admin/exam-records/clear',
      'admin/review-tasks/clear',
      'admin/documents/clear',
      'admin/members/clear',
    ];

    for (const endpoint of deleteOrder) {
      await fetch(`${API_BASE}/${endpoint}`, { method: 'DELETE' }).catch(() => {});
    }
  } catch (e) {
    try {
      const res = await fetch(`${API_BASE}/members`);
      if (!res.ok) return;
      const members = await res.json();
      for (const member of members) {
        await fetch(`${API_BASE}/members/${member.id}`, { method: 'DELETE' }).catch(() => {});
      }
    } catch {
      console.warn('清理数据库失败:', e);
    }
  }
}

export async function createTestMember(data: {
  name: string;
  gender?: string;
  date_of_birth?: string;
  member_type?: string;
}) {
  const res = await fetch(`${API_BASE}/members`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: data.name,
      gender: data.gender || 'male',
      date_of_birth: data.date_of_birth || '2018-01-01',
      member_type: data.member_type || 'child',
    }),
  });
  if (!res.ok) throw new Error(`创建测试成员失败: ${res.statusText}`);
  return res.json();
}

export { expect };