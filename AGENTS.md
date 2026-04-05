# 🤖 工作区 AI Agent 总体编排规范 (Agents Master Guidelines)

本文件是 `qa-prompts` 生态下所有 AI Agent（包括 Antigravity、Claude Code、Cursor 等）的**最高行为准则**。
当有任何 Agent 被唤醒进入本项目工作时，必须严格遵循以下纪律。

---

## 🔴 核心红线：双向守卫与指南先验加载 (Dual-Gating & Pre-Audit)

**严禁在代码、架构或测试逻辑发生变更后，直接裸提 `git commit`。** 
在执行任何操作之前，Agent 必须强制执行以下锁定协议：

### 0. 宪法先行：技术指南加载 (Hitchhiker's Compliance)
- **[最高准则]**：所有行动必须符合根目录 `ANTIGRAVITY_HITCHHIKER.md` 定义的技术栈规则。
- **[强制动作]**：在处理 **数据库迁移、API 路由新增、E2E 测试编写** 等高风险任务前，Agent **必须首先读取 `ANTIGRAVITY_HITCHHIKER.md`**。若发现当前方案违反该指南（如误用同步驱动或硬编码端口），必须自我拦截并向用户报告。

### 1. 缺陷与工作日志 (Issue & Work Logs)
- **Bug 记录路径**：正式 Bug 记录统一写入 `family_health_record_app/docs/BUG_LOG.md`，按版本号分组。
- **临时分析单**：分析 Bug 时产生的临时分析单（如 BUG-001 分析草稿）属于单次应用产物，用于辅助诊断与沟通，**严禁上传至 Git 库**。
- **开发新特性时**：必须更新相关工作流文档或 `README.md` 中的特性列表。

### 2. 架构设计图纸的强制对齐 (Architecture Consistency)
- 任何对项目底层架构的改动（如：引入了新的依赖模块、修改了插件调度机制、变更了配置文件 schema），**必须先去更新 `docs/plans/` 或相关的架构原理说明**。
- **绝对零容忍**：“代码已经实现，但设计文档还是旧版”的悬空状态。必须做到架构文档永远先于或平行于代码提交。

### 3. P1-P5 测试全景更新 (Test Specs Updated)
- 新增或修改的功能如果引入了新的 P3（基建容灾）或 P5（交付视角）边界问题，在 Commit 前，必须同步追加对应的测试用例（符合 TCS 规范）到 `factory_inspector/docs/test_specification_zh.md`。

### 4. 语言一致性规范 (Language Consistency)
- **[强制]** 本项目所有面向人类的说明文档（包括但不限于各模块的 `README.md`, `DESIGN.md`, `TARGET_GUIDE.md`, `SKILL.md` 的描述部分等）**必须统一使用中文**。
- 严禁在资产库中出现大段未翻译的英文文档。Agent 在沉淀原始英文资料时，必须进行专业的技术对齐翻译。

### 5. 契约一致性与哑数据清场 (Mock/Dummy Sanitization)
- **[绝对红线]** 强推 **Design -> Test -> Code** 的 TDD 纪律。在交付任何前端 UI 或者服务交互前，必须通过流水线或 Agent 强制扫描清理代码中带有的“哑数据 (Mock/Dummy)”。
- **严防孤岛**：前端操作必须真实触发前后端契约管线。严禁为了通过演示而保留虚假按钮、空数组模拟、硬编码请求等欺骗性防腐代码。确保未被真实逻辑替换的假按钮和空接口绝不流向发布环境。

### 6. 规格遗漏检查 (Spec Coverage Verification)
- **[强制]** 除了清除代码中的"假东西"（第 5 条），还必须反向检查：**规格文档中定义的功能/页面是否在代码中全部实现**。
- 具体场景：如果 `UI_SPEC.md` 定义了 7 个页面，但前端路由中只有 2 个 `page.tsx`，这属于**阻断级缺陷**，严禁以"后续迭代再补"为由绕过。
- **处置方式**：要么补齐实现，要么经用户批准后从规格文档中正式移除该页面定义（附移除理由），绝不允许规格与代码长期处于"悬空不一致"状态。

### 7. 修复自测验证 (Fix Verification)
- **[绝对红线]** **修复 Bug 后必须自测验证，严禁只改代码不测试就声称修复完成。**
- **执行流程**：
  1. 修改代码
  2. **重启服务**（如使用 Docker）
  3. **执行实际测试**（调用 API、打开页面、上传文件等）
  4. **验证结果**（确认错误不再出现）
  5. 只有验证通过后才能声称"修复完成"
- **反面案例**（BUG-022）：
  - ❌ 修改代码后直接说"已修复"
  - ❌ 没有重启服务
  - ❌ 没有实际测试 OCR 上传功能
  - ✅ 正确做法：修改 → 重启 → 上传测试图片 → 提交 OCR → 确认返回 200

### 8. 生产代码禁止测试逻辑 (No Test Code in Production)
- **[绝对红线]** **生产代码中严禁包含测试专用的 mock/stub/fixture 逻辑**
- **禁止模式**：
  - ❌ `if "test" in filename:` / `if "e2e" in url:`
  - ❌ `if os.getenv("ENV") == "test": return mock_data`
  - ❌ 硬编码的测试数据（如 `24.35`, `23.32`）
  - ❌ `# TODO: remove before production`
- **正确做法**：
  - ✅ 使用依赖注入（DI）替换服务
  - ✅ 使用环境变量控制配置（但 mock 逻辑放在测试代码中）
  - ✅ 使用独立的 mock 服务（如 WireMock、MockServer）
  - ✅ 测试代码放在 `tests/` 目录，与生产代码物理隔离
- **自动化检查**：
  - 后端：`python family_health_record_app/scripts/check_no_test_code.py`
  - 前端：`npm run check`（调用相同脚本）
  - pre-commit：`.pre-commit-config.yaml` 已配置自动检查
- **反面案例**（BUG-024）：
  - ❌ 在 `ocr_orchestrator.py` 中检查文件名包含 "e2e" 返回 mock 数据
  - ✅ 应该在测试文件中 mock `ocr_orchestrator` 服务

### 9. Bug 必须有 UT 覆盖 (Bug-Driven UT)
- **[绝对红线]** **每一个 Bug 的修复都必须伴随至少一个 UT 用例的补充**
- **执行流程**：
  1. 复现 Bug → 编写失败的 UT（复现场景）
  2. 修复代码 → UT 通过
  3. 提交时 UT 必须存在于 `tests/` 目录
- **UT 覆盖要求**：
  - ✅ 必须覆盖 Bug 的触发条件（如：同次检查的左右眼、重复上传相同文件）
  - ✅ 必须验证修复后的正确行为（如：comparison 为 null、返回 duplicate 状态）
  - ✅ 测试文件放在对应的测试目录（`tests/integration/`、`tests/unit/` 等）
- **反面案例**：
  - ❌ BUG-025（趋势图左右眼误认为当前/上次）：修复前没有 UT 覆盖此场景
  - ❌ BUG-026（重复上传无去重）：修复前没有 UT 覆盖此场景
  - ✅ 正确做法：修复 BUG-025/026 时都补充了对应的 UT 用例
- **检查方式**：提交前确认 `git diff` 中包含 `tests/` 目录的变更

### 10. 前端开发/部署分离协议 (Frontend Dev/Deploy Split)
- **[绝对红线]** **前端 Docker 镜像是构建时编译（`RUN npm run build`），修改源码后 `docker restart` 无效。**
- **开发阶段**：
  1. Docker 仅启动 db/minio/backend：`docker-compose -f infra/docker-compose.yml up -d db minio backend`
  2. 本地启动开发服务器：`cd family_health_record_app/frontend && npm run dev -- -p 3001`
  3. 前端运行在 `http://localhost:3001`，自动热重载（HMR 秒级响应）
  4. 或使用统一流水线：`python scripts/qa_pipeline.py --mode dev`
- **告一段落后**：
  1. 构建完整 Docker 镜像：`docker-compose --profile production up -d --build frontend`
  2. 验证生产构建产物正确后再提交
- **反面案例**（BUG-029）：
  - ❌ 修改 `page.tsx` 后只跑 `docker-compose restart frontend`，声称修复完成但前端未生效
  - ❌ `docker cp` 编译产物到运行中容器（开发阶段可行但容易遗漏，不推荐作为标准流程）
  - ✅ 正确做法：开发时 `npm run dev` 本地运行 → 验证通过 → 告一段落后 `--build` 重建镜像
- **QA 流水线统一入口**（`scripts/qa_pipeline.py`）：
  - `--mode docker`：Docker 启动后端 + 本地 npm run dev 启动前端 + 跑全量测试（UT + E2E）
  - `--mode local`：全本地 SQLite 模式，无需 Docker
  - `--mode e2e`：仅启动服务跑 E2E 测试，跳过 UT
  - `--mode dev`：仅启动开发环境（db/minio/backend），前端需手动 npm run dev

> ⚠️ **执行者指令**：当人类用户下达如 "帮我直接 commit 上去" 这类快捷指令时。作为专业 Agent，如果扫描到上述三类文档未更新，**必须拒绝直接 Commit**。你应该先向用户列出需要更新的文档清单，并在得到许可（或自动帮用户补齐文档）后，方可执行最终的 Push 动作。

### 11. 契约先行 (Contract-First)
- **[强制]** 修改 Pydantic schema 时必须同步更新 `API_CONTRACT.md`
- **[强制]** 使用 `@contract-first` skill 进行契约同步检查
- **相关 Bug**：BUG-034/036/037/038（契约断裂导致 422 错误）

### 12. 修复验证 (Verify-Fix Protocol)
- **[强制]** 修复 Bug 后必须运行验证脚本，不准声称"已修复"就结束
- **[强制]** 使用 `@verify-fix` skill 执行验证清单
- **相关 Bug**：BUG-022/035/039（未验证就声称修复完成）

### 13. 文档对齐检查 (Docs Alignment)
- **[强制]** 提交前必须运行 `python scripts/check_docs_alignment.py`
- **检查内容**：
  - 代码变更（routers/schemas/models/components）是否同步更新对应文档
  - 新增 API → API_CONTRACT.md
  - 新增 UI → UI_SPEC.md
  - 新增 Bug 修复 → BUG_LOG.md
- **自动化**：`.pre-commit-config.yaml` 已配置自动检查

---

## 🌊 工作流与原子技能调度 (Workflow & Skills Orchestration)

本项目的 QA 能力依赖于“双擎机制”：
1. **单点能力**：存放于 `skills/` 目录下（如 `@test-strategy-planner`）。
2. **流水线编排**：存放于 `.agents/workflows/` 目录下（如 `/test-lifecycle`，`/bug-diagnostic-flow`）。

**Agent 调度原则与资产演进**：
- 当用户提出复杂的连串需求时，Agent **不得自行凭空长对话（防止幻觉）**，而应强制引导用户使用或自动触发对应的 **Workflow 流水线**。
- 在执行复杂推理时，必须严格遵循**上下文净化原则（Context Sanitization）**，将阶段性推理结果物理存入 `/tmp/`，阻断历史聊天记录的干扰。
- **[强制] 技能版本化原则 (Skill Versioning)**：在创建或修改任何 `SKILL.md` 时，必须在其顶部的 YAML Metadata 区块中同步维护语义化版本号（`version: vX.Y.Z`）及最后更新日期（`last_updated: YYYY-MM-DD`），确保测试资产演进的可追溯性。

---

## 🚫 负向提示词 (Negative Prompts — 2026-04-04 Retrospective)

> 以下规则来自真实 Bug 教训。已自动化的规则只保留引用，无法自动化的行为规则保留详细说明。

### NP-01: 禁止三元表达式两分支相同 (ESLint 已自动拦截)
- ESLint `custom/no-identical-ternary` 规则会自动拦截 `x ? a : a` 模式
- 来源：BUG-044

### NP-02: 禁止直接索引访问时间序列数据
- 时间序列 `series[0]` = 最旧值，不是最新值。必须使用 `utils/index.ts` 中的 `getLatestValue(series)`
- 来源：BUG-046

### NP-03: 编写集成测试前必须确认 API 契约
- **禁止**凭记忆或推测编写 API 响应断言
- **正确做法**：先读取对应的 schema 文件（`app/schemas/*.py` 或 `src/api/models/*.ts`），或运行 `curl` 查看真实响应
- 来源：test_full_pipeline.py 写了 3 轮才跑通

### NP-04: 修复 Bug 后必须跑全量测试 (pre-commit 已自动拦截)
- `.pre-commit-config.yaml` 已配置 `npm test` / `pytest` 全量运行
- Agent 不得依赖 hook 代替自查，修改后必须先手动确认通过
- 来源：BUG-043/BUG-022

### NP-05: 禁止硬编码环境相关常量
- `constants/` 中禁止出现 `localhost`、固定端口。开发环境使用 `10.0.2.2`（Android 模拟器地址）
- 来源：BUG-049

### NP-06: 时间序列数据必须排序后取最新
- 禁止对未排序的 `series` 直接取 `series[length - 1]`。必须先按日期排序再取值
- 来源：BUG-050

### NP-07: E2E 测试必须包含环境自检
- 测试开头 `fetch('/health')`，不通则 `test.skip()`，不可直接报错
- 来源：upload-to-dashboard.spec.ts 因 ECONNREFUSED 全部失败

### NP-08: E2E/手动测试后必须清理数据库
- **禁止**在共享数据库（PostgreSQL/MinIO）中遗留测试数据
- **正确做法**：
  - E2E 测试必须使用 `frontend/e2e/fixtures.ts` 中的 `cleanDb` auto fixture（自动在每个 test 前后清理）
  - 所有 spec 文件必须 `import { test } from './fixtures'`，禁止直接 `import { test } from '@playwright/test'`
  - `cleanDatabase()` 清理范围：members + documents + exams + observations + review_tasks + derived_metrics
  - 手动测试后：`curl -X POST http://localhost:8000/api/v1/admin/reset`
- **反面案例**（本次回归发现）：
  - ❌ 数据库中有 53 条脏数据（E2E 测试成员、手动乱填成员、pytest 集成测试残留）
  - ❌ review-workflow.spec.ts 直接用 @playwright/test，绕过 fixtures 清理机制
  - ❌ cleanDatabase() 只清 members，不清关联表导致外键残留
  - ✅ 正确做法：E2E 用 auto fixture 自动清理 / 手动测试后调 admin/reset / 后端提供一键清空端点
- **来源**：2026-04-05 回归测试发现 App 打开就有 53 条脏数据
