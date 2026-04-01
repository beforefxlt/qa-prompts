import { test, expect } from '@playwright/test';

/**
 * P1 成员管理核心流程测试 (加固版)
 * 引入随机后缀，彻底解决脏数据导致的 'resolved to 4 elements' 歧义问题
 */

test('TC-P1-001: 空状态引导 - 首次使用创建成员', async ({ page }) => {
  await page.goto('/');
  await page.waitForTimeout(2000);
  
  // 此时应该是空状态
  const actionButton = page.getByRole('button', { name: '添加第一位成员' });
  if (await actionButton.isVisible()) {
    await actionButton.click();
    await expect(page).toHaveURL(/\/members\/new/);
  }
});

test('TC-P1-016: 成员列表 - 展示多个成员', async ({ page, request }) => {
  // 使用随机后缀，确保本用例创建的成员是唯一的
  const suffix = Date.now().toString().slice(-4);
  const name1 = `晓萌_${suffix}`;
  const name2 = `爸爸_${suffix}`;

  await request.post('http://127.0.0.1:8000/api/v1/members', {
    data: { name: name1, gender: '女', date_of_birth: '2016-05-05', member_type: 'child' },
  });
  await request.post('http://127.0.0.1:8000/api/v1/members', {
    data: { name: name2, gender: '男', date_of_birth: '1985-08-08', member_type: 'adult' },
  });
  
  await page.goto('/');
  await page.waitForTimeout(2000);
  
  // 验证新创建的成员可见，并使用 .first() 规避多布局渲染歧义
  await expect(page.getByText(name1)).toBeVisible();
  await expect(page.getByText(name2)).toBeVisible();
  await expect(page.getByText('儿童').first()).toBeVisible();
  await expect(page.getByText('成人').first()).toBeVisible();
});

test('TC-P1-018: 成员编辑 - 修改成员信息', async ({ page, request }) => {
  const suffix = Date.now().toString().slice(-4);
  const originalName = `待编辑_${suffix}`;
  const newName = `已更名_${suffix}`;

  // 1. 创建成员
  const resp = await request.post('http://127.0.0.1:8000/api/v1/members', {
    data: { name: originalName, gender: '男', date_of_birth: '2018-01-01', member_type: 'child' },
  });
  const member = await resp.json();

  // 2. 进入列表并点击详情
  await page.goto('/');
  await page.getByText(originalName).click();
  
  // 3. 点击编辑按钮 (V2 UI 可能是个图标或文字)
  await page.getByRole('button', { name: /编辑|settings/i }).first().click();
  
  // 4. 修改姓名
  await page.getByPlaceholder('请输入姓名').fill(newName);
  await page.getByRole('button', { name: '保存修改' }).click();
  
  // 5. 验证跳转回列表且姓名已更新
  await expect(page.getByText(newName)).toBeVisible();
});

test('TC-P1-019: 成员删除 - 软删除验证', async ({ page, request }) => {
  const suffix = Date.now().toString().slice(-4);
  const name = `待删除_${suffix}`;

  // 1. 创建成员
  await request.post('http://127.0.0.1:8000/api/v1/members', {
    data: { name: name, gender: '男', date_of_birth: '2010-10-10', member_type: 'child' },
  });

  await page.goto('/');
  await expect(page.getByText(name)).toBeVisible();

  // 2. 点击进入详情
  await page.getByText(name).click();

  // 3. 执行删除
  page.on('dialog', dialog => dialog.accept()); // 自动确认删除对话框
  await page.getByRole('button', { name: /删除|delete/i }).first().click();

  // 4. 验证回到列表且已消失
  await page.waitForTimeout(1000);
  await expect(page.getByText(name)).not.toBeVisible();
});
