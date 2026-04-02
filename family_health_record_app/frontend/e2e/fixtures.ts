import { test as base, expect } from '@playwright/test';

const API_BASE = 'http://127.0.0.1:8000/api/v1';

/**
 * E2E 测试 fixtures
 * 提供数据清理和注入功能
 */
export const test = base.extend<{ cleanDb: void }>({
  // 每个测试前清理数据库，测试后恢复空状态
  cleanDb: [async ({}, use) => {
    // 测试前：清理所有数据
    await cleanDatabase();
    
    await use();
    
    // 测试后：清理所有数据
    await cleanDatabase();
  }, { auto: true }],  // 自动应用于所有测试
});

/**
 * 清理数据库所有测试数据
 */
export async function cleanDatabase() {
  try {
    const res = await fetch(`${API_BASE}/members`);
    if (!res.ok) return;
    
    const members = await res.json();
    
    // 删除每个成员（软删除）
    for (const member of members) {
      await fetch(`${API_BASE}/members/${member.id}`, {
        method: 'DELETE',
      });
    }
    
    if (members.length > 0) {
      console.log(`已清理 ${members.length} 条成员数据`);
    }
  } catch (e) {
    console.warn('清理数据库失败（可能服务未启动）:', e);
  }
}

/**
 * 创建测试成员
 */
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
  
  if (!res.ok) {
    throw new Error(`创建测试成员失败: ${res.statusText}`);
  }
  
  return res.json();
}

export { expect };
