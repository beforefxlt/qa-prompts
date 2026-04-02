import { test, expect, createTestMember } from './fixtures';

/**
 * 错误状态测试
 * 验证空状态、错误状态的用户引导
 */

test('首页 - 空状态引导', async ({ page }) => {
  // 确保数据库为空（cleanDb fixture 自动清理）
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // 验证欢迎文案
  await expect(page.getByText('欢迎使用家庭检查单管理')).toBeVisible({ timeout: 10000 });
  
  // 验证添加成员按钮
  await expect(page.getByRole('button', { name: '添加第一位成员' })).toBeVisible();
});

test('首页 - 有成员时显示卡片列表', async ({ page }) => {
  // 注入测试数据
  await createTestMember({ name: 'E2E测试成员' });
  
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // 验证成员卡片可见
  await expect(page.getByText('E2E测试成员')).toBeVisible({ timeout: 10000 });
  
  // 验证成员类型标签（使用更精确的选择器）
  await expect(page.getByText('儿童').first()).toBeVisible();
});

test('成员创建 - 跳转到新建页面', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // 点击添加成员按钮
  await page.getByRole('button', { name: '添加第一位成员' }).click();
  
  // 验证跳转到新建页面
  await expect(page).toHaveURL(/\/members\/new/);
  await expect(page.getByText('添加成员')).toBeVisible({ timeout: 10000 });
});

test('审核页 - 页面标题正确', async ({ page }) => {
  await page.goto('/review');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
  
  await expect(page.getByText('OCR 识别结果审核')).toBeVisible({ timeout: 10000 });
});
