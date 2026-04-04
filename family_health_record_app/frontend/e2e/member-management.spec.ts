import { test, expect, createTestMember, cleanDatabase, UI_TEXT } from './fixtures';

/**
 * P1 成员管理核心流程测试 @critical @smoke @regression
 * 使用 fixtures 自动清理数据库
 */

test.describe.serial('P1 空状态测试 @critical @smoke @regression', () => {
  test.beforeAll(async () => {
    await cleanDatabase();
  });

  test('TC-P1-001: 空状态引导 - 首次使用创建成员 @critical @smoke @regression', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    // 验证空状态
    await expect(page.getByRole('button', { name: UI_TEXT.ADD_FIRST_MEMBER })).toBeVisible();
    
    // 点击按钮
    await page.getByRole('button', { name: UI_TEXT.ADD_FIRST_MEMBER }).click();
    await expect(page).toHaveURL(/\/members\/new/);
  });

  test.afterAll(async () => {
    await cleanDatabase();
  });
});

test('TC-P1-016: 成员列表 - 展示多个成员 @smoke @regression', async ({ page }) => {
  await cleanDatabase();
  
  // 创建多个成员
  await createTestMember({ name: '成员A', gender: 'male', member_type: 'child' });
  await createTestMember({ name: '成员B', gender: 'female', member_type: 'spouse' });
  
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // 验证两个成员都显示
  await expect(page.getByText('成员A')).toBeVisible({ timeout: 10000 });
  await expect(page.getByText('成员B')).toBeVisible();
});
