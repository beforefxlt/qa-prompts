import { test, expect } from '@playwright/test';

test('首页 - 显示成员列表', async ({ page, request }) => {
  // 创建成员
  const memberResp = await request.post('http://127.0.0.1:8000/api/v1/members', {
    data: {
      name: 'E2E成员',
      gender: 'female',
      date_of_birth: '2018-01-01',
      member_type: 'child',
    },
  });
  expect(memberResp.ok()).toBeTruthy();
  const memberData = await memberResp.json();

  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // 验证成员显示在列表中
  await expect(page.getByText('E2E成员')).toBeVisible({ timeout: 10000 });
  await expect(page.getByText('儿童')).toBeVisible();
  
  // 验证有添加成员按钮
  await expect(page.getByRole('button', { name: /添加.*成员/ })).toBeVisible();
});

test('成员卡片 - 点击可进入详情', async ({ page, request }) => {
  // 创建成员
  const memberResp = await request.post('http://127.0.0.1:8000/api/v1/members', {
    data: {
      name: '点击测试成员',
      gender: 'male',
      date_of_birth: '2019-01-01',
      member_type: 'child',
    },
  });
  const memberData = await memberResp.json();

  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // 点击成员卡片
  await page.getByText('点击测试成员').click();
  
  // 验证跳转到成员详情页
  await expect(page).toHaveURL(new RegExp(`/members/${memberData.id}`), { timeout: 10000 });
});
