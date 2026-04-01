import { test, expect } from '@playwright/test';

/**
 * P5 用户体验测试
 * 验证空状态引导、错误提示、图表可读性等用户体验指标
 */

test('P5-01: 空状态引导文案清晰可读', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  
  // 验证欢迎文案存在且可读
  await expect(page.getByText('欢迎使用家庭检查单管理')).toBeVisible();
  
  // 验证引导说明存在
  await expect(page.getByText('记录家人健康足迹')).toBeVisible();
  
  // 验证操作按钮文案明确
  const actionButton = page.getByRole('button', { name: '添加第一位成员' });
  await expect(actionButton).toBeVisible();
  await expect(actionButton).toBeEnabled();
});

test('P5-02: 成员创建表单字段标签清晰', async ({ page }) => {
  await page.goto('/members/new');
  await page.waitForLoadState('networkidle');
  
  // 等待表单出现
  await expect(page.getByText('添加新成员')).toBeVisible();
  
  // 验证所有字段标签存在
  await expect(page.getByText('姓名')).toBeVisible();
  await expect(page.getByText('性别')).toBeVisible();
  await expect(page.getByText('出生年月')).toBeVisible();
  await expect(page.getByText('成员类型')).toBeVisible();
  
  // 验证 placeholder 提示存在
  await expect(page.getByPlaceholder('请输入姓名')).toBeVisible();
  
  // 验证提交按钮文案明确
  await expect(page.getByRole('button', { name: '保存并开始记录' })).toBeVisible();
});

test('P5-03: 错误提示友好可读', async ({ page }) => {
  await page.goto('/');
  
  // 模拟网络错误
  await page.route('**/api/v1/members', route => route.abort('failed'));
  await page.reload();
  
  // 验证有某种形式的反馈（不白屏）
  await expect(page.locator('main')).toBeVisible({ timeout: 5000 });
});

test('P5-04: 审核页布局清晰', async ({ page }) => {
  await page.goto('/review');
  await page.waitForLoadState('networkidle');
  
  // 验证页面标题
  await expect(page.getByText('OCR 识别结果审核')).toBeVisible();
});

test('P5-05: 成员卡片信息完整', async ({ page, request }) => {
  // 创建成员
  await request.post('http://127.0.0.1:8000/api/v1/members', {
    data: { name: '卡片测试成员', gender: 'male', date_of_birth: '2018-01-01', member_type: 'child' },
  });
  
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
  
  // 验证成员卡片包含必要信息
  await expect(page.getByText('卡片测试成员')).toBeVisible();
  
  // 验证成员类型标签
  await expect(page.getByText('儿童')).toBeVisible();
  
  // 验证无记录提示
  await expect(page.getByText('尚无记录')).toBeVisible();
});
