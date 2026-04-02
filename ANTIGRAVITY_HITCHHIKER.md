# 💠 ANTIGRAVITY HITCHHIKER GUIDE (v1.0.0)

## 🛠️ 技术栈与环境约束 (Stack & Env)
1. **Backend**: FastAPI(Async) + SQLAlchemy + aiosqlite.
   - [规则] **必须** 使用 `sqlite+aiosqlite:///` 驱动 (禁止同步注入)。
   - [规则] 端口 **8000** 专属于后端。
2. **Frontend**: Next.js (Vite) + TypeScript (Strict Mode).
   - [规则] 端口 **3001** 专属于前端。
   - [规则] **禁止** 提交带有残留 `console.log` 或 `any` 类型的代码。
3. **QA Pipeline**: 核心集成入口 `scripts/qa_pipeline.py`.
   - [规则] 运行前 **必须** 执行 `sync_traceability.py`。
   - [规则] 测试前 **必须** 物理清理 `.db` 和 `uploads/`。

## 🛡️ 硬性工程红线 (Hard Rules)
- **R1: 永远不要删除** 任何已存在的数据库迁移文件（Alembic/Migration 基石）。
- **R2: 禁止硬编码** 测试数据到 API 路由。测试必须通过 `request.post` 动态注入。
- **R3: 门禁拦截**:
  - `git commit` 前 **必须** 运行 `ruff` (BE) 和 `tsc` (FE)。
  - `git push` 前 **建议** 手动运行一次全量 `qa_pipeline.py`回归。
- **R4: UI 选择器**: E2E 测试 **必须** 优先使用 `getByRole` 或 `getByText` 配合 `.first()`。

## 🧠 AI 执行协议 (AI Compliance)
- 在每次复杂任务开始前，**必须读一次本指南**。
- 如果代码违反上述规则，AI 有义务自我拦截并修正，而非等待用户指出。
