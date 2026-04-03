import { test as base, expect } from '@playwright/test';
import { UI_TEXT } from '../src/constants/ui-text';

const API_BASE = 'http://localhost:8000/api/v1';

/**
 * E2E 测试 fixtures
 * 提供数据清理和 UI 文案引用
 */
export const test = base.extend<{ cleanDb: void }>({
  cleanDb: [async ({}, use) => {
    await cleanDatabase();
    await use();
    await cleanDatabase();
  }, { auto: true }],
});

export async function cleanDatabase() {
  try {
    const res = await fetch(`${API_BASE}/members`);
    if (!res.ok) return;
    const members = await res.json();
    for (const member of members) {
      await fetch(`${API_BASE}/members/${member.id}`, { method: 'DELETE' });
    }
  } catch (e) {
    console.warn('清理数据库失败:', e);
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

// 导出文案供测试使用
export { expect, UI_TEXT };
