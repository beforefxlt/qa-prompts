import { test as base, expect } from '@playwright/test';
import { UI_TEXT } from '../src/constants/ui-text';

const API_BASE = 'http://localhost:8000/api/v1';

/**
 * E2E 测试 fixtures
 * 提供数据清理和 UI 文案引用
 *
 * 清理策略：
 * - cleanDb fixture 使用 auto: true，每个 test 执行前后自动清理
 * - cleanDatabase() 清理所有业务表（含关联表），防止外键残留
 * - 使用后端 /api/v1/admin/reset 端点（如可用），否则逐个 DELETE
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
 * 清理顺序：先子表后父表，避免外键约束冲突
 */
export async function cleanDatabase() {
  try {
    // 尝试使用 admin reset 端点（最快）
    const resetResp = await fetch(`${API_BASE}/admin/reset`, { method: 'POST' });
    if (resetResp.ok) return;

    // 回退方案：逐个 DELETE（从叶子表到根表）
    const deleteOrder = [
      'derived-metrics/clear',
      'observations/clear',
      'exam-records/clear',
      'review-tasks/clear',
      'documents/clear',
      'members/clear',
    ];

    for (const endpoint of deleteOrder) {
      await fetch(`${API_BASE}/${endpoint}`, { method: 'DELETE' }).catch(() => {});
    }
  } catch (e) {
    // 最后的兜底：逐个删除 members
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

// 导出文案供测试使用
export { expect, UI_TEXT };
