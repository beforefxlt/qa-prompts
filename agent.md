# 🤖 AI Agent Harness 工程指南

> 基于 OpenAI Harness Engineering + Claude Code 源码分析 + 项目 Bug Log
> 版本：v2.0 | 更新：2026-04-04

---

## 1. 核心原则

| # | 原则 | 说明 |
|:-:|:-----|:-----|
| 1 | 零起点策略 | Agent 完全负责代码生成，人类设计环境 |
| 2 | 角色重定义 | 人=设计环境+意图+反馈，Agent=执行+验证 |
| 3 | 验证即对抗 | Verification Agent 想方设法把代码搞崩 |
| 4 | 内外有别 | 内部用户约束比外部更严格 |
| 5 | 知识即系统 | 仓库知识是唯一真相源 |

---

## 2. 架构映射

| Claude Code 层 | 本项目实践 |
|:--------------|:-----------|
| 第6层 安全治理 | AGENTS.md 核心红线 (13条) |
| 第5层 生态扩展 | 60+ skills |
| 第4层 工具管线 | 验证清单 (5步) |
| 第3层 Agent调度 | skills 单点能力 |
| 第2层 提示词引擎 | docs/ 目录结构 |
| 第1层 入口层 | qa_pipeline.py |

---

## 3. 核心红线（禁止 ❌）

```
❌ 契约断裂     → Pydantic 校验必须同步到 API_CONTRACT.md
❌ 测试代码入生产 → 不准有 mock/stub 在 app/ 目录
❌ 修复未验证   → 不准声称"已修复"就结束
❌ 文档未对齐   → 代码变更必须同步更新 docs/
❌ 规格遗漏     → UI_SPEC 定义7页必须实现7页
❌ 盲改        → 不准先读再改
```

---

## 4. 强制工具

| 工具 | 用途 | 触发时机 |
|:-----|:-----|:--------|
| `check_no_test_code.py` | 检查生产代码无测试逻辑 | pre-commit |
| `check_docs_alignment.py` | 检查文档对齐 | pre-commit |
| `pytest` | 后端验证 | 代码修改后 |
| `npm run build` | 前端验证 | 前端修改后 |

---

## 5. 检查清单

| Category | Status |
|:---------|:------:|
| docs/ 结构化 | ✅ |
| API_CONTRACT.md 数值约束 | ✅ |
| pre-commit hooks | ✅ |
| 契约验证 UT | ✅ |
| 层级架构 Linter | ❌ |
| 自主循环增强 | ❌ |

**成熟度**: ⭐⭐⭐☆☆ (3/5)

---

## 6. 相关文档

| 文档 | 说明 |
|:-----|:-----|
| `AGENTS.md` | AI Agent 总体编排规范（红线） |
| `skills/contract-first/` | 契约先行规则 |
| `skills/verify-fix/` | 修复验证规则 |
| `docs/specs/API_CONTRACT.md` | API 契约详细 |
| `docs/BUG_LOG.md` | Bug 根因分析 |
| `ANTIGRAVITY_HITCHHIKER.md` | 技术栈规则 |

---

*详细实现指南见各 SKILL 和 docs/ 目录*
