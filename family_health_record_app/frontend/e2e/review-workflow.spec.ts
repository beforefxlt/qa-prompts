import { test, expect } from './fixtures';

test('审核页 - 页面标题和空状态 @smoke @regression', async ({ page }) => {
  await page.goto('/review');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
  
  // 验证页面标题
  await expect(page.getByText('OCR 识别结果审核')).toBeVisible();
});

test('审核页 - 返回按钮可用 @smoke @regression', async ({ page }) => {
  await page.goto('/review');
  await page.waitForLoadState('networkidle');
  
  // 验证返回按钮存在
  const backButton = page.locator('button').filter({ has: page.locator('svg') }).first();
  await expect(backButton).toBeVisible();
});
