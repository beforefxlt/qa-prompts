import { test, expect } from '@playwright/test';

test('前后端链路可用并可在页面展示成员', async ({ page, request }) => {
  const memberResp = await request.post('http://127.0.0.1:8000/api/v1/members', {
    data: {
      phone_or_email: `e2e-${Date.now()}@test.com`,
      name: 'E2E成员',
      gender: 'female',
      date_of_birth: '2018-01-01',
      member_type: 'child',
    },
  });
  expect(memberResp.ok()).toBeTruthy();
  const memberData = await memberResp.json();

  const uploadResp = await request.post('http://127.0.0.1:8000/api/v1/documents/upload', {
    multipart: {
      member_id: memberData.id,
      file: {
        name: 'e2e.jpg',
        mimeType: 'image/jpeg',
        buffer: Buffer.from('e2e-test-image'),
      },
    },
  });
  expect(uploadResp.ok()).toBeTruthy();
  const uploadData = await uploadResp.json();

  const submitResp = await request.post(`http://127.0.0.1:8000/api/v1/documents/${uploadData.document_id}/submit-ocr`);
  expect(submitResp.ok()).toBeTruthy();

  await page.goto(`/?memberId=${memberData.id}&memberName=E2E成员`);
  await expect(page.getByText('E2E成员')).toBeVisible();
  await expect(page.getByText('儿童眼轴 (Axial Length)')).toBeVisible();
  await expect(page.getByRole('button', { name: '录入新检查单' })).toBeVisible();
});
