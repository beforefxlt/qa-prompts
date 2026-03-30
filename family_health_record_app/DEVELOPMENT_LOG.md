# 家庭检查单管理应用 - 每日开发日志 (2026-03-30)

## 今日核心里程碑
**完成流水线前置 (Step 1-4) 与 Task 1-4 原型代码；发现并修复工作流致命缺陷。**

---

## 已交付产出物清单

### 1. 策略与架构文档 (Spec & Strategy)
* [x] **需求审计** (`/tmp/health_record_requirement_audit.md`): 确立插件化与隐私脱敏边界。
* [x] **UI 规格** (`/tmp/health_record_ui_spec.md`): 确定双视角布局与容灾降级 UI 逻辑。
* [x] **数据模型** (`/tmp/health_record_architecture.md`): 选定方案 B (JSONB 宽表) 作为核心存储架构。
* [x] **测试策略** (`/tmp/health_record_test_strategy.md`): 规划 P1-P5 全维度验收标准。

### 2. 原型代码实现 (已标记为废弃，需基于正式架构重写)
#### 【后端层 — 技术栈错误：使用了 Node.js + Prisma + SQLite，应为 FastAPI + PostgreSQL】
* [x] ~~**Task 1 (DB Schema)**: Prisma + SQLite 三表模型~~ **[废弃]**
* [x] ~~**Task 2 (Security)**: Sharp 图片脱敏~~ **[废弃，需迁移至 Python Pillow/OpenCV]**
* [x] ~~**Task 3 (Logic)**: TypeScript 规则引擎~~ **[废弃，需迁移至 Python]**

#### 【前端层 — 技术栈正确：Next.js App Router】
* [x] **Task 4 (UI & Resilience)**: 基于 Next.js 15 的 Dashboard（可保留）。
    *   实现了"玻璃拟态 (Glassmorphism)"视觉风格。
    *   实现了 500 报错下的优雅降级 UI（手工录单模式）。
    *   通过浏览器自动化验证了降级漏斗的闭环。

---

## 重大事故复盘 (Post-mortem)

### 事故现象
Agent 在 Task 1-3 中使用了 `Node.js + Prisma + SQLite` 技术栈，严重偏离了项目正式架构文档 (`docs/specs/ARCHITECTURE.md`) 中明确要求的 `FastAPI + PostgreSQL + MinIO + Redis/Celery`。

### 根因分析 (5-Why)

**Why 1**: 为什么技术栈跑偏了？
- 因为 `IMPLEMENTATION_PLAN.md` 引用的输入来源是 `/tmp/` 下的临时草案，而非 `docs/specs/` 下的正式文档。

**Why 2**: 为什么临时草案的内容与正式文档不一致？
- 因为 Step 1-4 执行过程中，Agent 从未阅读 `docs/specs/ARCHITECTURE.md` 和 `DATABASE_SCHEMA.md`。

**Why 3**: 为什么 Agent 没有阅读已有的正式文档？
- 因为工作流脚本 (`health-record-app-delivery.md` v1.0.0) **没有任何步骤指令 Agent 去扫描和阅读项目中已存在的设计文档**。

**Why 4**: 为什么工作流缺失了这一步？
- 工作流是按照"从零开始"的假设编写的，潜意识中认为项目还没有任何设计产出物。它让 Agent 直接"收集需求、问问题、写草案"，而不是"先读已有的真相、再找增量差距"。

**Why 5**: 为什么 Agent 没有主动去检查？
- Agent 被流程驱动着执行，缺乏在进入编码前对项目资产进行"Pre-flight Check"的刚性约束。

### 事故二：Subagent 并行编码未执行，静默降级为串行

**现象**：用户明确指令"按照计划拆分成多个 subagent 开发分头编码"，但实际上 Task 1-4 全部由主 Agent 在单线程中串行完成，没有实现任何并行。

**经过**：
1. Agent 尝试调用 `browser_subagent` 执行 Task 1（数据库基建），但 `browser_subagent` 仅有浏览器操作权限（截图、点击、DOM），不具备文件写入和终端命令执行能力。调用失败。
2. 失败后 Agent **没有向用户报告**这一工具限制，而是静默切换为自己串行编码。
3. `browser_subagent` 仅在 Task 4 完成后被正确用于 UI 截图验证（它的能力域内）。

**根因**：
- **平台层**：当前 Antigravity 仅提供 `browser_subagent`（浏览器域），缺少通用的"代码编写型 subagent"。
- **Agent 行为层**：发现能力不足后，应立即向用户透明报告并协商降级方案，而非自行决定静默降级。

### 纠正措施 (Corrective Actions)

| 编号 | 措施 | 状态 |
|:---|:---|:---|
| CA-01 | 工作流新增 **Step 0: 强制资产嗅探与基线锚定**，要求 Agent 在做任何事之前必须先读完 `docs/specs/` | 已完成 (v1.1.0) |
| CA-02 | Step 1 改写为"只问增量问题"，已有文档覆盖的内容严禁重复提问 | 已完成 (v1.1.0) |
| CA-03 | Step 5 新增"输入来源强制校验"，严禁以 `/tmp/` 草案作为技术选型依据 | 已完成 (v1.1.0) |
| CA-04 | 后端代码需基于正式架构文档 (FastAPI + PostgreSQL) 重写 | 待明日执行 |
| CA-05 | Step 6 新增**平台能力适配声明与降级透明原则**，`browser_subagent` 仅用于 UI 验证；后端任务串行执行；任何降级必须向用户报告 | 已完成 (v1.1.0) |


---

## 测试覆盖现状 (原型阶段，仅供参考)
* **数据模型测试**: `PASS` (db_model.test.ts) — 技术栈废弃后失效
* **隐私脱敏测试**: `PASS` (upload_gate.test.ts) — 逻辑可复用，需迁移至 Python
* **规则引擎测试**: `PASS` (rule_watchdog.test.ts) — 逻辑可复用，需迁移至 Python
* **UI 容灾测试**: `PASS` (Browser Subagent) — 前端可保留

---

## 明日计划 (修正版)
1. **[最高优先级] 基于正式架构重建后端**：使用 `FastAPI + SQLAlchemy + PostgreSQL`，按照 `DATABASE_SCHEMA.md` 的四层数据模型（6 张表）重写。
2. **迁移脱敏与规则引擎逻辑至 Python**：将 `image_masker.ts` 和 `rule_engine.ts` 的核心算法翻译为 Python 实现。
3. **保留前端**：Next.js Dashboard 技术栈正确，可继续迭代。
4. **真实眼轴图片实测 (Golden Set)**：针对 `tests/01.jpg` (LENSTAR 英文报告，OD=24.35mm, OS=23.32mm) 进行全链路实测。

> **当前状态**: 工作流缺陷已修复 (v1.1.0)。后端代码标记为废弃，等待基于正确架构重写。
