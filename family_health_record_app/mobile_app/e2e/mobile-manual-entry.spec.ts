import { test, expect } from './fixtures';

test.describe('移动端手工录入功能', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('TC-MOBILE-001: 添加成员后返回首页，列表自动刷新', async ({ page }) => {
    await test.step('1. 首页点击添加成员', async () => {
      if (await page.locator('text=添加第一位成员').isVisible()) {
        await page.locator('text=添加第一位成员').click();
      } else {
        await page.locator('text=+ 添加成员').click();
      }
    });

    await test.step('2. 填写成员信息', async () => {
      await page.locator('input[placeholder="请输入姓名"]').fill('测试儿童');
      await page.locator('text=保存并开始记录').click();
    });

    await test.step('3. 返回首页，验证成员出现在列表中', async () => {
      await expect(page.locator('text=测试儿童')).toBeVisible({ timeout: 5000 });
    });
  });

  test('TC-MOBILE-002: 手工录入身高后，Dashboard 生长发育卡片显示最新值', async ({ page }) => {
    await test.step('1. 进入成员 Dashboard', async () => {
      await page.locator('text=测试儿童').click();
    });

    await test.step('2. 点击手工录入按钮', async () => {
      const manualEntryBtn = page.locator('text=✏️ 手工录入指标');
      if (await manualEntryBtn.isVisible()) {
        await manualEntryBtn.click();
      } else {
        await page.locator('text=手工录入指标').click();
      }
    });

    await test.step('3. 填写身高数据', async () => {
      const heightOption = page.locator('text=身高').first();
      if (await heightOption.isVisible()) {
        await heightOption.click();
      }
      const valueInputs = page.locator('input[keyboardType="decimal-pad"]');
      if (await valueInputs.first().isVisible()) {
        await valueInputs.first().fill('125');
      } else {
        await page.locator('input[placeholder="请输入数值"]').fill('125');
      }
      await page.locator('text=保存记录').click();
    });

    await test.step('4. 返回 Dashboard，验证身高显示 125 而非 N/A', async () => {
      await expect(page.locator('text=125').first()).toBeVisible({ timeout: 5000 });
      await expect(page.locator('text=N/A')).not.toBeVisible();
    });
  });

  test('TC-MOBILE-003: 手工录入眼轴左右眼数据', async ({ page }) => {
    await test.step('1. 进入成员 Dashboard', async () => {
      await page.locator('text=测试儿童').click();
    });

    await test.step('2. 点击手工录入', async () => {
      const manualEntryBtn = page.locator('text=✏️ 手工录入指标');
      if (await manualEntryBtn.isVisible()) {
        await manualEntryBtn.click();
      } else {
        await page.locator('text=手工录入指标').click();
      }
    });

    await test.step('3. 选择眼轴，填写左右眼数值', async () => {
      const axialOption = page.locator('text=眼轴').first();
      if (await axialOption.isVisible()) {
        await axialOption.click();
      }
      const eyeInputs = page.locator('input[placeholder="—"]');
      if (await eyeInputs.first().isVisible()) {
        await eyeInputs.first().fill('23.5');
        await eyeInputs.last().fill('23.3');
      }
      await page.locator('text=保存记录').click();
    });

    await test.step('4. 返回 Dashboard，验证眼轴数据显示', async () => {
      await expect(page.locator('text=23.5').or(page.locator('text=23.3'))).toBeVisible({ timeout: 5000 });
    });
  });

  test('TC-MOBILE-004: 手工录入数值超出区间，前端拦截', async ({ page }) => {
    await test.step('1. 进入成员 Dashboard', async () => {
      await page.locator('text=测试儿童').click();
    });

    await test.step('2. 点击手工录入', async () => {
      const manualEntryBtn = page.locator('text=✏️ 手工录入指标');
      if (await manualEntryBtn.isVisible()) {
        await manualEntryBtn.click();
      } else {
        await page.locator('text=手工录入指标').click();
      }
    });

    await test.step('3. 填写超出区间的身高', async () => {
      const valueInputs = page.locator('input[keyboardType="decimal-pad"]');
      if (await valueInputs.first().isVisible()) {
        await valueInputs.first().fill('500');
      } else {
        await page.locator('input[placeholder="请输入数值"]').fill('500');
      }
      await page.locator('text=保存记录').click();
    });

    await test.step('4. 验证错误提示出现', async () => {
      await expect(page.locator('text=超出合理范围')).toBeVisible({ timeout: 3000 });
    });
  });

  test('TC-MOBILE-005: 趋势图页面验证手工录入数据', async ({ page }) => {
    await test.step('1. 进入成员 Dashboard', async () => {
      await page.locator('text=测试儿童').click();
    });

    await test.step('2. 点击身高卡片进入趋势页', async () => {
      await page.locator('text=身高').first().click();
    });

    await test.step('3. 验证趋势图显示数据点', async () => {
      await expect(page.locator('text=125')).toBeVisible({ timeout: 5000 });
    });
  });
});