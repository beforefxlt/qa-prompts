# MCP 测试执行状态

> **最后更新**: 2026-04-01 13:20
> **目标**: 完成基于 Chrome DevTools MCP 的前端测试 (Playwright 暂不处理)

---

## 环境状态

| 服务 | 状态 | 端口 | 进程 |
|------|------|------|------|
| 后端 (FastAPI) | ✅ 运行中 | 8000 | 23292 |
| 前端 (Next.js) | ✅ 运行中 | 3001 | 20436 |
| Chrome (调试模式) | ✅ 运行中 | 9222 | 5952 |
| MCP Server | ✅ 已安装 | - | - |
| 数据库 | ✅ 已重建 | - | 空状态 |

---

## 测试用例清单

| 用例 ID | 名称 | 状态 | 备注 |
|---------|------|------|------|
| TC-MCP-001 | 空状态引导验证 | ⏳ 待执行 | 验证首页欢迎文案和添加按钮 |
| TC-MCP-002 | 成员创建流程 | ⏳ 待执行 | 创建测试成员 |
| TC-MCP-003 | 成员编辑功能 | ⏳ 待执行 | 编辑成员名称 |
| TC-MCP-004 | 成员删除功能 | ⏳ 待执行 | 删除成员并验证 |
| TC-MCP-005 | 指标切换验证 | ⏳ 待执行 | 眼轴/身高/体重/血糖切换 |
| TC-MCP-006 | 空数据状态 | ⏳ 待执行 | 无数据时的提示 |
| TC-MCP-007 | 审核页面验证 | ⏳ 待执行 | /review 页面 |
| TC-MCP-008 | 页面加载性能 | ⏳ 待执行 | LCP/CLS/FCP 指标 |

---

## 执行方式

由于 opencode CLI 不支持直接调用 MCP 工具，需要通过以下方式执行：

### 方式一：在支持 MCP 的 Agent 中执行

在 Claude Desktop / Cursor / Copilot 中配置 MCP 后，按 `mcp-tests/TEST_GUIDE.md` 中的指令逐个执行。

### 方式二：使用 MCP SDK 自动化脚本

```bash
cd C:\Users\Administrator\qa-prompts\family_health_record_app\mcp-tests
node run-tests.js
```

---

## 已完成的准备工作

- [x] 启动后端服务 (FastAPI:8000)
- [x] 启动前端服务 (Next.js:3001)
- [x] 启动 Chrome 调试模式 (:9222)
- [x] 安装 chrome-devtools-mcp
- [x] 重建数据库 (清空测试数据)

---

## 下一步

1. 通过 MCP Agent 执行 TC-MCP-001 ~ TC-MCP-008
2. 收集截图和测试结果
3. 更新本文件中的测试状态
