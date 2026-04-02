import { test, expect, createTestMember, UI_TEXT } from './fixtures';

test('首页 - 空状态引导', async ({ page }) => {
  await page.goto('/');
  await page.waitForTimeout(2000);
  
  // 引用常量，不再硬编码
  await expect(page.getByText(UI_TEXT.WELCOME_TITLE)).toBeVisible({ timeout: 10000 });
  await expect(page.getByRole('button', { name: UI_TEXT.ADD_FIRST_MEMBER })).toBeVisible();
});

test('首页 - 有成员时显示卡片列表', async ({ page }) => {
  await createTestMember({ name: 'E2E测试成员' });
  
  await page.goto('/');
  await page.waitForTimeout(2000);
  
  await expect(page.getByText('E2E测试成员')).toBeVisible({ timeout: 10000 });
  await expect(page.getByText(UI_TEXT.MEMBER_TYPE_CHILD).first()).toBeVisible();
});

test('成员创建 - 跳转到新建页面', async ({ page }) => {
  await page.goto('/');
  await page.waitForTimeout(2000);
  
  await page.getByRole('button', { name: UI_TEXT.ADD_FIRST_MEMBER }).click();
  
  await expect(page).toHaveURL(/\/members\/new/);
  await expect(page.getByText(UI_TEXT.FORM_TITLE_CREATE)).toBeVisible({ timeout: 10000 });
});

test('审核页 - 页面标题正确', async ({ page }) => {
  await page.goto('/review');
  await page.waitForTimeout(1000);
  
  await expect(page.getByText(UI_TEXT.REVIEW_TITLE)).toBeVisible({ timeout: 10000 });
});
