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
- **自动化检查**：提交前运行 `python scripts/check_no_test_code.py`
- **反面案例**（BUG-024）：
  - ❌ 在 `ocr_orchestrator.py` 中检查文件名包含 "e2e" 返回 mock 数据
  - ✅ 应该在测试文件中 mock `ocr_orchestrator` 服务

> ⚠️ **执行者指令**：当人类用户下达如 "帮我直接 commit 上去" 这类快捷指令时。作为专业 Agent，如果扫描到上述三类文档未更新，**必须拒绝直接 Commit**。你应该先向用户列出需要更新的文档清单，并在得到许可（或自动帮用户补齐文档）后，方可执行最终的 Push 动作。

---

## 🌊 工作流与原子技能调度 (Workflow & Skills Orchestration)

本项目的 QA 能力依赖于“双擎机制”：
1. **单点能力**：存放于 `skills/` 目录下（如 `@test-strategy-planner`）。
2. **流水线编排**：存放于 `.agents/workflows/` 目录下（如 `/test-lifecycle`，`/bug-diagnostic-flow`）。

**Agent 调度原则与资产演进**：
- 当用户提出复杂的连串需求时，Agent **不得自行凭空长对话（防止幻觉）**，而应强制引导用户使用或自动触发对应的 **Workflow 流水线**。
- 在执行复杂推理时，必须严格遵循**上下文净化原则（Context Sanitization）**，将阶段性推理结果物理存入 `/tmp/`，阻断历史聊天记录的干扰。
- **[强制] 技能版本化原则 (Skill Versioning)**：在创建或修改任何 `SKILL.md` 时，必须在其顶部的 YAML Metadata 区块中同步维护语义化版本号（`version: vX.Y.Z`）及最后更新日期（`last_updated: YYYY-MM-DD`），确保测试资产演进的可追溯性。
