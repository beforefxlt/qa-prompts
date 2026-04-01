# 项目状态文档 (STATUS.md)

> **单一真相源**：每个 Agent 开始工作前必须读取，结束时必须更新。
> **最后更新**: 2026-04-01 by opencode

---

## 当前状态

**整体进度**: 🔄 P0 后端已修复，前端 E2E 测试进行中

| 模块 | 状态 | 说明 |
|------|------|------|
| 后端 API | ✅ 正常 | 所有端点返回 200 |
| 后端测试 | ✅ 通过 | 72 个 pytest 测试全部通过 |
| 前端页面 | ✅ 正常 | 端口已改为 3001 |
| 前端 E2E 测试 | 🔄 修复中 | 3/5 测试文件已修复 |

---

## 已完成的修复

### BUG-018: /api/v1/members 500 错误 ✅
- 修复 `debug_api.py` 导入错误
- 创建 `verify_fix.py` 验证脚本

### BUG-019: /api/v1/health 和 /api/v1/trends 404 ✅
- `/health` 移至 `/api/v1/health`
- 新增 `/api/v1/trends` 端点

### 端口统一 (3000 → 3001) ✅
- 修改 CORS、Dockerfile、docker-compose、playwright.config

---

## 待完成任务

| 优先级 | 任务 | 文件 |
|--------|------|------|
| P0 | 修复 member-management.spec.ts | `frontend/e2e/member-management.spec.ts` |
| P0 | 修复 ux-experience.spec.ts | `frontend/e2e/ux-experience.spec.ts` |
| P1 | 实现 Chrome DevTools MCP 测试 | 待定 |

### E2E 测试修复要点
1. 增加 `waitForTimeout(2000)` 等待 React hydration
2. 表单字段：`出生年月` (年月选择器) 而非 `出生日期` (date输入)
3. 提交按钮：`保存并开始记录` 而非 `保存`
4. 移除依赖不存在功能的测试（如"模拟接口状态"按钮）

---

## 关键文件

| 文件 | 说明 |
|------|------|
| `backend/app/main.py` | 后端入口 |
| `backend/verify_fix.py` | API 验证脚本 |
| `frontend/e2e/*.spec.ts` | E2E 测试用例 |
| `docs/specs/UI_SPEC.md` | UI 规格文档 |
| `docs/BUG_LOG.md` | 缺陷记录 |

---

## 测试命令

```bash
# 后端测试
cd family_health_record_app/backend && python -m pytest tests/ -v

# 前端 E2E 测试
cd family_health_record_app/frontend && npx playwright test --reporter=list

# API 验证
cd family_health_record_app/backend && python verify_fix.py
```

---

## 环境状态

- **后端**: http://localhost:8000 (运行中)
- **前端**: http://localhost:3001 (需手动启动)
- **数据库**: SQLite (`backend/health_record.db`)

---

## 更新日志

| 日期 | Agent | 变更 |
|------|-------|------|
| 2026-04-01 | opencode | 创建 STATUS.md，完成 P0 后端修复 |
