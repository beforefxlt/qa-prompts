import { test, expect, createTestMember, cleanDatabase, UI_TEXT } from './fixtures';

/**
 * P5 用户体验测试 @regression
 * 验证空状态引导、错误提示、图表可读性等用户体验指标
 */

test.describe.serial('P5 空状态测试 @regression', () => {
  test.beforeAll(async () => {
    await cleanDatabase();
  });

  test('TC-P5-001: 空状态引导文案清晰可读 @regression', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    await expect(page.getByText(UI_TEXT.WELCOME_TITLE)).toBeVisible();
    await expect(page.getByText('记录家人健康足迹')).toBeVisible();
    
    const actionButton = page.getByRole('button', { name: UI_TEXT.ADD_FIRST_MEMBER });
    await expect(actionButton).toBeVisible();
    await expect(actionButton).toBeEnabled();
  });

  test('TC-P5-002: 成员创建表单字段标签清晰 @regression', async ({ page }) => {
    await page.goto('/members/new');
    await page.waitForTimeout(1500);
    
    await expect(page.getByText(UI_TEXT.FORM_TITLE_CREATE)).toBeVisible();
    
    await expect(page.getByText(UI_TEXT.LABEL_NAME, { exact: true })).toBeVisible();
    await expect(page.getByText(UI_TEXT.LABEL_GENDER, { exact: true })).toBeVisible();
    await expect(page.getByText(UI_TEXT.LABEL_DOB, { exact: true })).toBeVisible();
    await expect(page.getByText(UI_TEXT.LABEL_TYPE, { exact: true })).toBeVisible();
    
    await expect(page.getByPlaceholder(UI_TEXT.PLACEHOLDER_NAME)).toBeVisible();
    await expect(page.getByRole('button', { name: UI_TEXT.FORM_SUBMIT_CREATE })).toBeVisible();
  });

  test.afterAll(async () => {
    await cleanDatabase();
  });
});

test('TC-P5-011: 错误提示友好可读 @regression', async ({ page }) => {
  await page.route('**/api/v1/members', route => route.fulfill({
    status: 500,
    contentType: 'application/json',
    body: JSON.stringify({ detail: 'Internal Server Error' })
  }));
  
  await page.goto('/');
  await page.waitForTimeout(1000);
  
  await expect(page.getByText(UI_TEXT.ERROR_TITLE)).toBeVisible();
  await expect(page.getByRole('button', { name: UI_TEXT.ERROR_RETRY })).toBeVisible();
});

test('TC-P5-020: 审核页布局清晰 @regression', async ({ page }) => {
  await page.goto('/review');
  await page.waitForTimeout(1000);
  
  await expect(page.getByText(UI_TEXT.REVIEW_TITLE)).toBeVisible();
});

test('TC-P5-024: 成员卡片信息完整 @regression', async ({ page }) => {
  await createTestMember({ name: '卡片测试成员' });
  
  await page.goto('/');
  await page.waitForTimeout(2000);
  
  await expect(page.getByText('卡片测试成员')).toBeVisible();
  await expect(page.getByText(UI_TEXT.MEMBER_TYPE_CHILD).first()).toBeVisible();
  await expect(page.getByText(UI_TEXT.NO_RECORDS)).toBeVisible();
});
