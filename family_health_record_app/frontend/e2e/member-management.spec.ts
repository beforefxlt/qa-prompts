import { test, expect } from '@playwright/test';

test('空状态引导 - 首次使用创建成员', async ({ page }) => {
  // 确保后端无成员数据（使用干净数据库）
  await page.goto('/');
  
  // 应该看到空状态引导页
  await expect(page.getByText('欢迎使用家庭检查单管理')).toBeVisible();
  await expect(page.getByText('请先添加家庭成员')).toBeVisible();
  await expect(page.getByRole('button', { name: '添加第一位成员' })).toBeVisible();
  
  // 点击添加成员
  await page.getByRole('button', { name: '添加第一位成员' }).click();
  
  // 等待表单出现
  await expect(page.getByText('添加成员')).toBeVisible();
  
  // 填写表单 - 使用placeholder定位输入框
  await page.getByPlaceholder('请输入姓名').fill('小明');
  
  // 性别选择 - 使用select定位
  await page.locator('select').first().selectOption('男');
  
  // 出生日期 - 使用type=date定位
  await page.locator('input[type="date"]').first().fill('2018-06-15');
  
  // 成员类型 - 使用第二个select
  await page.locator('select').nth(1).selectOption('child');
  
  // 提交
  await page.getByRole('button', { name: '保存' }).click();
  
  // 等待页面跳转和加载
  await page.waitForTimeout(1000);
  
  // 应该看到成员卡片或进入成员详情页
  await expect(page.getByText('小明')).toBeVisible();
});

test('成员列表 - 展示多个成员', async ({ page, request }) => {
  // 先创建几个成员
  const members = [
    { name: '晓萌', gender: 'female', date_of_birth: '2018-01-01', member_type: 'child' },
    { name: '爸爸', gender: 'male', date_of_birth: '1990-01-01', member_type: 'adult' },
  ];
  
  for (const m of members) {
    await request.post('http://127.0.0.1:8000/api/v1/members', { data: m });
  }
  
  await page.goto('/');
  
  // 等待页面加载完成
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
  
  // 应该看到所有成员
  await expect(page.getByText('晓萌')).toBeVisible();
  await expect(page.getByText('爸爸')).toBeVisible();
  await expect(page.getByText('儿童')).toBeVisible();
  await expect(page.getByText('成人')).toBeVisible();
});

test('成员编辑 - 修改成员信息', async ({ page, request }) => {
  // 创建成员
  const resp = await request.post('http://127.0.0.1:8000/api/v1/members', {
    data: { name: '待编辑', gender: 'male', date_of_birth: '2018-01-01', member_type: 'child' },
  });
  expect(resp.ok()).toBeTruthy();
  
  await page.goto('/');
  
  // 等待页面加载完成
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
  
  // hover 显示编辑按钮
  const memberCard = page.locator('button.group').filter({ hasText: '待编辑' });
  await memberCard.hover();
  
  // 等待编辑按钮出现
  await page.waitForTimeout(300);
  
  // 点击编辑按钮
  await page.getByRole('button', { name: '编辑' }).click();
  
  // 等待编辑表单出现
  await expect(page.getByText('编辑成员')).toBeVisible();
  
  // 修改名称 - 使用placeholder定位
  await page.getByPlaceholder('请输入姓名').fill('已编辑');
  await page.getByRole('button', { name: '保存修改' }).click();
  
  // 等待更新完成
  await page.waitForTimeout(1000);
  
  // 验证更新
  await expect(page.getByText('已编辑')).toBeVisible();
});

test('成员删除 - 软删除后不在列表显示', async ({ page, request }) => {
  // 创建成员
  const resp = await request.post('http://127.0.0.1:8000/api/v1/members', {
    data: { name: '待删除', gender: 'male', date_of_birth: '2018-01-01', member_type: 'child' },
  });
  expect(resp.ok()).toBeTruthy();
  
  await page.goto('/');
  
  // 等待页面加载完成
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
  
  await expect(page.getByText('待删除')).toBeVisible();
  
  // hover 显示删除按钮
  const memberCard = page.locator('button.group').filter({ hasText: '待删除' });
  await memberCard.hover();
  
  // 等待删除按钮出现
  await page.waitForTimeout(300);
  
  // 处理确认对话框
  page.on('dialog', dialog => dialog.accept());
  
  // 点击删除
  await page.getByRole('button', { name: '删除' }).click();
  
  // 等待删除完成
  await page.waitForTimeout(1000);
  
  // 验证不在列表
  await expect(page.getByText('待删除')).not.toBeVisible();
});
