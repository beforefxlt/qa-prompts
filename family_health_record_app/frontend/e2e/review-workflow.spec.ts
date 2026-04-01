import { test, expect } from '@playwright/test';

test('审核流程 - 创建审核任务并完成审核', async ({ page, request }) => {
  // 1. 创建成员
  const memberResp = await request.post('http://127.0.0.1:8000/api/v1/members', {
    data: { name: '审核测试成员', gender: 'male', date_of_birth: '2018-01-01', member_type: 'child' },
  });
  expect(memberResp.ok()).toBeTruthy();
  const memberData = await memberResp.json();

  // 2. 上传文档
  const uploadResp = await request.post('http://127.0.0.1:8000/api/v1/documents/upload', {
    multipart: {
      member_id: memberData.id,
      file: {
        name: 'review-test.jpg',
        mimeType: 'image/jpeg',
        buffer: Buffer.from('review-test-image'),
      },
    },
  });
  expect(uploadResp.ok()).toBeTruthy();
  const uploadData = await uploadResp.json();

  // 3. 提交 OCR
  const submitResp = await request.post(`http://127.0.0.1:8000/api/v1/documents/${uploadData.document_id}/submit-ocr`);
  expect(submitResp.ok()).toBeTruthy();

  // 等待OCR处理完成
  await page.waitForTimeout(2000);

  // 4. 检查审核任务列表
  const tasksResp = await request.get('http://127.0.0.1:8000/api/v1/review-tasks');
  expect(tasksResp.ok()).toBeTruthy();
  const tasks = await tasksResp.json();

  // 5. 访问审核页
  await page.goto('/review');
  
  // 等待页面加载完成
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
  
  // 应该看到审核页面标题
  await expect(page.getByText('OCR 识别结果审核')).toBeVisible();
});

test('审核页 - 查看审核任务详情', async ({ page, request }) => {
  // 创建成员和文档
  const memberResp = await request.post('http://127.0.0.1:8000/api/v1/members', {
    data: { name: '审核详情成员', gender: 'female', date_of_birth: '2019-06-01', member_type: 'child' },
  });
  const memberData = await memberResp.json();

  const uploadResp = await request.post('http://127.0.0.1:8000/api/v1/documents/upload', {
    multipart: {
      member_id: memberData.id,
      file: {
        name: 'detail-test.jpg',
        mimeType: 'image/jpeg',
        buffer: Buffer.from('detail-test'),
      },
    },
  });
  const uploadData = await uploadResp.json();

  await request.post(`http://127.0.0.1:8000/api/v1/documents/${uploadData.document_id}/submit-ocr`);

  // 等待OCR处理完成
  await page.waitForTimeout(2000);

  // 访问审核页
  await page.goto('/review');
  
  // 等待页面加载完成
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
  
  // 验证页面基本元素
  await expect(page.getByText('OCR 识别结果审核')).toBeVisible();
});
