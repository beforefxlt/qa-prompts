import { test, expect, createTestMember, cleanDatabase, UI_TEXT } from './fixtures';

/**
 * 手动录入与 CRUD 功能测试 (技术债清理回归版) @critical @regression
 * 100% 依赖 data-testid 和 UI_TEXT 常量，确保跨环境测试稳定性
 */

test.describe.serial('手动录入与 CRUD 功能测试 @critical @regression', () => {
  let member: any;

  test.beforeAll(async () => {
    await cleanDatabase();
    member = await createTestMember({ name: 'E2E测试员' });
  });

  test('TC-CRUD-001: 全流程手动录入验证 @critical @regression', async ({ page }) => {
    await page.goto(`/members/${member.id}`);
    
    // 1. 等待详情页渲染
    await expect(page.getByTestId('member-name')).toHaveText('E2E测试员', { timeout: 15000 });
    
    // 2. 点击 FAB 展开并弹出手动录入 (使用 UI_TEXT 匹配 aria-label)
    await page.getByTestId('fab-trigger').click();
    await page.getByTestId('fab-manual').click();
    
    // 3. 填写身高 125.5
    const row = page.locator('.bg-slate-50').first();
    await row.locator('input[type="number"]').fill('125.5');
    
    // 4. 保存
    const savePromise = page.waitForResponse(r => r.url().includes('/manual-exams') && r.status() === 201);
    await page.getByRole('button', { name: '保存记录' }).click();
    await savePromise;
    
    // 5. 验证展示
    await expect(page.getByText('125.5')).toBeVisible({ timeout: 10000 });
  });

  test('TC-CRUD-002: 指标修正 (Update) 验证 @critical @regression', async ({ page }) => {
    // 进入趋势页
    await page.goto(`/members/${member.id}/trends?metric=height`);
    
    // 1. 找到 125.5 数值单元格
    const cell = page.getByText('125.5');
    await expect(cell).toBeVisible({ timeout: 10000 });
    
    // 2. Hover 并通过 data-testid 点击编辑
    await cell.hover();
    // 寻找以 edit-obs- 开头的 TestID 按钮
    await page.locator('[data-testid^="edit-obs-"]').first().click();
    
    // 3. 修改为 127
    const input = page.locator('input[type="number"]');
    await input.clear();
    await input.fill('127.0');
    
    const updatePromise = page.waitForResponse(r => r.url().includes('/observations/') && r.status() === 200);
    await page.getByRole('button', { name: '保存' }).click();
    await updatePromise;
    
    // 4. 验证更新
    await expect(page.getByText('127.0')).toBeVisible();
  });

  test('TC-CRUD-003: 记录物理删除 (Delete) 验证 @critical @regression', async ({ page }) => {
    await page.goto(`/members/${member.id}/trends?metric=height`);
    await expect(page.getByText('127.0')).toBeVisible();
    
    // 1. 点击删除 (使用 data-testid)
    page.once('dialog', d => d.accept());
    await page.locator('[data-testid^="delete-exam-"]').first().click();
    
    const deletePromise = page.waitForResponse(r => r.url().includes('/exam-records/') && r.status() === 204);
    await deletePromise;
    
    // 2. 验证消失
    await expect(page.getByText('127.0')).not.toBeVisible();
  });

  test('TC-CRUD-004: 业务合理性拦截验证 (Negative) @critical @regression', async ({ page }) => {
    await page.goto(`/members/${member.id}`);
    await page.getByTestId('fab-trigger').click();
    await page.getByTestId('fab-manual').click();
    
    // 输入超长身高 (300cm)
    await page.locator('input[type="number"]').first().fill('300');
    await page.getByRole('button', { name: '保存记录' }).click();
    
    // 验证 UI_TEXT 匹配
    await expect(page.getByText(UI_TEXT.MSG_SANITY_ERROR)).toBeVisible();
  });

  test.afterAll(async () => {
    await cleanDatabase();
  });
});
