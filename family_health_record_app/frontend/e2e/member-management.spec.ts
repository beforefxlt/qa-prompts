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
  
  // 填写表单
  await page.getByLabel('姓名').fill('小明');
  await page.getByLabel('性别').selectOption('男');
  await page.getByLabel('出生日期').fill('2018-06-15');
  await page.getByLabel('成员类型').selectOption('child');
  
  // 提交
  await page.getByRole('button', { name: '保存' }).click();
  
  // 应该看到成员卡片
  await expect(page.getByText('小明')).toBeVisible();
  await expect(page.getByText('儿童')).toBeVisible();
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
  
  // hover 显示编辑按钮
  const memberCard = page.locator('button', { hasText: '待编辑' });
  await memberCard.hover();
  
  // 点击编辑按钮
  await page.getByRole('button', { name: '编辑' }).click();
  
  // 修改名称
  await page.getByLabel('姓名').fill('已编辑');
  await page.getByRole('button', { name: '保存修改' }).click();
  
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
  await expect(page.getByText('待删除')).toBeVisible();
  
  // hover 显示删除按钮
  const memberCard = page.locator('button', { hasText: '待删除' });
  await memberCard.hover();
  
  // 点击删除
  page.on('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: '删除' }).click();
  
  // 验证不在列表
  await expect(page.getByText('待删除')).not.toBeVisible();
});
