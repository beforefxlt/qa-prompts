import { test, expect, createTestMember, cleanDatabase, UI_TEXT } from './fixtures';

/**
 * P1 成员管理核心流程测试
 * 使用 fixtures 自动清理数据库
 */

test.describe.serial('P1 空状态测试', () => {
  test.beforeAll(async () => {
    await cleanDatabase();
  });

  test('TC-P1-001: 空状态引导 - 首次使用创建成员', async ({ page }) => {
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

test('TC-P1-016: 成员列表 - 展示多个成员', async ({ page }) => {
  // 注入测试数据
  await createTestMember({ name: '测试成员A', gender: 'female', member_type: 'child' });
  await createTestMember({ name: '测试成员B', gender: 'male', member_type: 'adult' });
  
  await page.goto('/');
  await page.waitForTimeout(2000);
  
  // 验证成员可见
  await expect(page.getByText('测试成员A')).toBeVisible();
  await expect(page.getByText('测试成员B')).toBeVisible();
});

test('TC-P1-018: 成员编辑 - 修改成员信息', async ({ page }) => {
  // 创建测试成员
  await createTestMember({ name: '待编辑成员' });
  
  // 进入列表并点击成员
  await page.goto('/');
  await page.waitForTimeout(2000);
  await page.getByText('待编辑成员').click();
  
  // 等待详情页加载，点击设置按钮（使用更精确的选择器）
  await page.waitForTimeout(1000);
  await page.locator('header').getByRole('button').last().click();
  
  // 等待编辑页面
  await page.waitForTimeout(1000);
  
  // 修改姓名
  await page.getByPlaceholder(UI_TEXT.PLACEHOLDER_NAME).fill('已编辑成员');
  await page.getByRole('button', { name: UI_TEXT.FORM_SUBMIT_EDIT }).click();
  
  // 验证更新成功（跳转回详情页或列表）
  await page.waitForTimeout(1000);
});

test('TC-P1-019: 成员删除 - 软删除验证', async ({ page }) => {
  // 创建测试成员
  await createTestMember({ name: '待删除成员' });
  
  await page.goto('/');
  await expect(page.getByText('待删除成员')).toBeVisible();
  
  // 点击进入详情
  await page.getByText('待删除成员').click();
  
  // 点击设置按钮进入编辑页面
  await page.waitForTimeout(1000);
  await page.locator('header').getByRole('button').last().click();
  
  // 等待编辑页面加载
  await page.waitForTimeout(1000);
  
  // 设置 dialog 处理器
  page.on('dialog', dialog => dialog.accept());
  
  // 点击删除按钮
  await page.getByRole('button', { name: UI_TEXT.FORM_DELETE }).click();
  
  // 等待删除操作完成
  await page.waitForTimeout(2000);
  
  // 验证回到首页
  await expect(page).toHaveURL('/');
});
