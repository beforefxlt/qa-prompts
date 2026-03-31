# 前端 UI 组件测试驱动开发指南 (UI TDD Guideline)

秉承本项目 `AGENTS.md` 中的最高指令及引申的 `ui-test-driven-dev` 技能要求，下一阶段所有的前端（Web）组件开发，无论是由人类工程师手动编写还是由 AI Agent 自动生成，**必须强制执行“测试先行 (Test-First)”的开发纪律。**

## 1. 核心流程：逻辑开发前的“验证动作”前置
在编写任何一个新的组件（如新的交互按钮、表格、或表单）的业务逻辑之前，必须先出具验证动作的代码。
- **Red (报错)**：先书写测试文件（如 `Dashboard.test.tsx` 或 Playwright 的 `upload.spec.ts`），断言应该发生的行为。此时测试必定失败（或编译不通过）。
- **Green (通过)**：随后在组件内补充真实的 UI 交互代码、API 挂载，使得刚才的测试变绿。
- **Refactor (重构)**：在有测试兜底的情况下，清理组件骨架和冗余代码。


## 2. 行为验证，而非像素验证
组件的测试重心必须放在**交互流转**和**数据连通性**上：
- ❌ **禁止单纯测表现**：不要仅仅测试“按钮是否是蓝色的”或者“样式是否为 rounded-full”。
- ✅ **强制测行为闭环**：必须测试“当点击录入时，是否唤起了文件选择器”、“当服务异常时，是否回退到了手工录入表单并展现了红色故障提示”。


## 3. 针对“原生弹窗/文件选取”的拦截规范
像图片上传、扫码、授权获取等交互，极易因为调用操作系统的原生 UI（如 `fileInput.click()` 或者 `window.alert`）导致自动化测试阻断或脱节。为杜绝此类“为了视觉糊弄”的代码合入，强制要求：

### 3.1 拦截与 Mock 准则
在进入 UI 开发前，测试侧必须**出具对底层 API 的 Mock 拦截证明**。这标志着开发者思考了后续的运行链路。

**1. 浏览器原生文件选取器的拦截**
对于 `<input type="file" />` 的触发，由于我们无法在测试中物理点击操作系统的真实相册，必须在测试用例级别对此事件实施 Mock 拦截：
```typescript
// Jest / React Testing Library 示例标准：
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('录入按钮应触发文件选择器并成功拦截文件传入', async () => {
  render(<Dashboard />);
  
  // 1. 获取隐藏的文件选择器节点 (需在代码里绑定 data-testid="file-upload")
  const fileInput = screen.getByTestId('file-upload');
  
  // 2. 模拟真实用户的上传行为（拦截原生弹窗，将内存中的 Fake File 直接注入）
  const fakeFile = new File(['dummy content'], 'check_record.png', { type: 'image/png' });
  await userEvent.upload(fileInput, fakeFile);

  // 3. 断言后续的 API 调用是否按契约执行
  expect(apiClient.uploadDocument).toHaveBeenCalledWith(fakeFile, expect.any(String));
  expect(apiClient.submitOcr).toHaveBeenCalled(); // 核心：确保二段调用被执行
});
```

**2. Playwright 端到端拦截标准**
如果你使用的是 Playwright 进行端到端（E2E）验收，测试不仅要验证前端，还可以 Mock 后端返回：
```typescript
test('当选择上传检查单时，页面应展示提取中的状态，并随后更新折线图', async ({ page }) => {
  // 1. 拦截上传接口并塞入 Mock 返回句柄
  await page.route('**/api/v1/documents/upload', route => {
    route.fulfill({ json: { document_id: "mock-doc-123", status: "uploaded" } });
  });

  // 2. 将模拟图片挂载到上传输入框上（避开系统本身的弹窗阻塞）
  await page.setInputFiles('input[type="file"]', 'test-fixtures/sample_record.png');

  // 3. 断言界面应当呈现了对应的状态转换
  await expect(page.locator('button')).toContainText('智能提取中...');
});
```

## 4. 交付卡点 (Quality Gate)
- 今后在合并 Request 或执行 Commit 前的检查环节（`Reviewer Agent`）中，不仅会扫描是否有“空数组假数据”，还会**检查这些核心按键是否配套了如上的拦截测试用例。如果没有，拒绝通过！**
