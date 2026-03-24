# 🤖 工作区 AI Agent 总体编排规范 (Agents Master Guidelines)

本文件是 `qa-prompts` 生态下所有 AI Agent（包括 Antigravity、Claude Code、Cursor 等）的**最高行为准则**。
当有任何 Agent 被唤醒进入本项目工作时，必须严格遵循以下纪律。

---

## 🔴 核心红线：Commit 前的文档一致性强校验 (Pre-Commit Sync)

**严禁在代码、架构或测试逻辑发生变更后，直接裸提 `git commit`。** 
在执行任何 `git commit` 操作之前，Agent 必须强制执行以下“文档一致性拦截检查”：

### 1. 缺陷与工作日志 (Issue & Work Logs)
- **分析 Bug 时**：产生的 Bug 分析单（如 BUG-001）属于单次应用产物，用于辅助诊断与沟通，**严禁上传至 Git 库**。
- **开发新特性时**：必须更新相关工作流文档或 `README.md` 中的特性列表。

### 2. 架构设计图纸的强制对齐 (Architecture Consistency)
- 任何对项目底层架构的改动（如：引入了新的依赖模块、修改了插件调度机制、变更了配置文件 schema），**必须先去更新 `docs/plans/` 或相关的架构原理说明**。
- **绝对零容忍**：“代码已经实现，但设计文档还是旧版”的悬空状态。必须做到架构文档永远先于或平行于代码提交。

### 3. P1-P5 测试全景更新 (Test Specs Updated)
- 新增或修改的功能如果引入了新的 P3（基建容灾）或 P5（交付视角）边界问题，在 Commit 前，必须同步追加对应的 TC-001 用例到 `factory_inspector/docs/test_specification_zh.md`。

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
