import { test, expect, createTestMember } from './fixtures';

test('首页 - 显示成员列表 @smoke @regression', async ({ page }) => {
  // 创建成员
  await createTestMember({ name: 'E2E成员', gender: 'female', member_type: 'child' });

  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // 验证成员显示在列表中
  await expect(page.getByText('E2E成员')).toBeVisible({ timeout: 10000 });
  await expect(page.getByText('儿童').first()).toBeVisible();
  
  // 验证有添加成员按钮
  await expect(page.getByRole('button', { name: /添加.*成员/ })).toBeVisible();
});

test('成员卡片 - 点击可进入详情 @smoke @regression', async ({ page }) => {
  // 创建成员
  const memberData = await createTestMember({ name: '点击测试成员', gender: 'male', member_type: 'child' });

  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // 点击成员卡片
  await page.getByText('点击测试成员').click();
  
  // 验证跳转到成员详情页
  await expect(page).toHaveURL(new RegExp(`/members/${memberData.id}`), { timeout: 10000 });
});
