# 测试团队 AI 辅助入门指南

> 从零开始，用 AI 专属 Skills 高效生成高质量测试用例与分析报告

**版本**: v2.6 (已纳入回归测试工作流、Bug 模式库与测试 Skills 治理基线)
**适用对象**: 首次接触探索性测试、自动化边界值与需求评审的测试工程师及 Test Lead

---

## 一、核心提效理念：从"背 Prompt 表格"到"召唤外挂大脑"

在 v1.0 时代，测试人员需要像填表一样复制 Markdown 模板代码并手动替换变量。  
现在（v2.0），我们已经将最硬核的测试模板原生内嵌为了 AI 的 **Skills（专属技能）**！
系统不仅大幅降低了使用门槛，同时已经主动移除了大量干扰测试视角的前端/开发类专属代码 Skills（如发版审查、UI 生成等），确保 AI 专注为你提供"防不胜防"的测试级视角解答。

### 📚 特别增刊：QA 核心资产库
除了日常开箱即用的 Skills，本机仓库还特别集成了 `studyInspire` 项目的精华沉淀！
请在日常阅读 **`docs/studyInspire-insights/`** 目录，获取包含测试架构设计 (`TESTING_ARCHITECTURE.md`)、测试分析心法 (`TEST_LESSONS_LEARNED.md`)、TDD 测试驱动开发实践等高级方法论。 

---

## 二、可用 Skills 列表与使用场景

目前的系统已为你装备了一组覆盖需求评审、策略设计、用例产出与最终复核的 QA Skills，遇到对应阶段直接召唤即可：

| Skill 技能名 | 会话触发场景 | 核心能力说明 |
| :--- | :--- | :--- |
| **`requirement-reviewer`** | 需求评审阶段（评审 PRD / 敏捷用户故事） | 找出需求中的歧义词（如"快速"且无指标）、逻辑真空、缺失的边界和异常应对路径，并按高中低风险输出整改建议表。 |
| **`test-strategy-planner`** | 通用测试策略设计阶段 | 按 P1-P5 全景模型梳理基础路径、业务异常、基建异常、边界条件与交付视角，生成结构化测试矩阵。 |
| **`bva-boundary-value-analysis`** | 用例设计阶段（输入框、表单、API 参数强校验） | 严格基于"边界值分析法"为你秒速输出包含 min, max, min-1, max+1, 空值, 类型错误等硬核边界的测试矩阵表。 |
| **`exploratory-testing-persona`** | 发散测试阶段（探索性测试 / Monkey Test） | 模拟 5 种极端人格（小白、极客、弱网、完美主义、急躁），在不看代码的前提下为你提供极具破坏性的手工测试漏洞排查指导。 |
| **`test-plan-copilot`** | 项目发版前计划阶段（储能/电力垂直场景） | 丢入模糊需求，自动脑补工控上下游链路关联与环境矩阵，按 `TP-001` 产出正规结构化系统测试大纲。 |
| **`test-case-factory`** | 编写测试执行资产阶段 | 强力重构零散步骤，严格按照物理前置条件、控制测试动作、录波证据隔离等环节量产正规化实例。 |
| **`test-report-reviewer`** | 执行阶段收尾放行 | 传入跑偏的碎碎念战报，AI秒速剥离出"首次挂测率"和"遗留致命危险域"撰写具有说服力的研判。 |
| **`issue-reporter`** | 缺陷登记与复现固化阶段 | 将零散现象、日志和复现步骤整理成符合模板的缺陷单草稿。 |
| **`protocol-fuzzing-test`** | 工业协议专项鲁棒性测试阶段 | 基于 Modbus 测试经验提炼分层故障注入方法论，覆盖靶机设计、异常设计、观测指标和失败判定。 |
| **`8d-qm-analysis`** | 事故复盘与体系追责阶段 | 以 QM 视角重构 8D 分析，聚焦 D3 / D4 / D5 / D7，强制把"人的失误"上升为流程、门禁和系统失效问题。 |
| **`test-code-simplifier`** | 测试代码开发收口阶段 | 仅对测试代码做低扰动整理，优先收紧重复断言、fixture 职责和命名噪音；不是默认每轮都要启用。 |
| **`reviewer-agent`** | Workflow 最终收口与提交前复核 | 对当前仓库或本轮变更执行最小扰动复核，优先结合 `vibe-tools repo` 进行整仓上下文审查，并明确要求 "Minimalist Refactor" 风格输出。 |

### 新增：回归测试与代码审查（v2.6）

| 资源 | 类型 | 说明 |
| :--- | :--- | :--- |
| **`regression-test`** | Workflow | 已有代码的回归测试流水线：代码审查 → Bug 修复(TDD) → 全链路 → 失败路径 → 文档对齐 |
| **Bug 模式库** | 外挂资产 | `.agents/assets/bug-patterns.md`，收录 18 个真实 Bug 模式（BP-001~BP-018），供审查清单、ESLint、pre-commit 消费 |
| **ESLint 自定义规则** | 自动化门禁 | `custom/no-identical-ternary` 拦截 `x ? a : a` 模式 |
| **pre-commit hook** | 提交门禁 | 全量 351 个 UT 自动运行，~4.5s |

补充说明：
- `bva-boundary-value-analysis` 适合字段级快刀式出表，不替代 `test-case-factory` 的正式 TCS 用例集。
- `test-plan-copilot` 是行业专版计划技能；若只是梳理通用测试点，优先调用 `test-strategy-planner`。
- `verify-requirements`、`webapp-testing`、`test-driven-development` 属于工程验证辅助能力，不属于测试设计主链；其中后两者当前仅建议在用户明确要求时按需启用。

---

## 三、全新工作流（一句话自动化调用）

### 1. 直接贴出原始素材
不需要你自己再费心梳理 Markdown 变量格式，直接把下面这些平日里的"原材料"扔给 AI 对话框：
- 群里发来的 PRD 截图翻译的文字 / 需求文档中的某段话。
- 接口文档（Swagger) 里的某些字段长度或鉴权描述。
- 南网/国标的某段控制逻辑流转说明。

### 2. 一句话召唤 Skill
在贴出素材的同行，像使唤测试小弟一样，附带一句唤醒对应 Skill 的指令。

**👉 示例 1：想做需求评审**
> **Prompt**: "使用 `requirement-reviewer` 这个 skill 帮我看看这段需求逻辑有没有漏洞：如果 AGC 的偏差过大，需要上报故障。"

**👉 示例 2：想做边界值分析**
> **Prompt**: "调用 `bva-boundary-value-analysis` 这个 skill，帮我按表格出这几项的用例：AGC 功率上限为 100MW，下限 50MW。"

**👉 示例 3：想做自由探索性测试**
> **Prompt**: "我要测'无感后台定时对时'功能，用 `exploratory-testing-persona` skill 帮我从小白用户和弱网视角出几个破坏性测试点。"

**👉 示例 4：想做代码回归测试**
> **Prompt**: "使用 `regression-test` 工作流，帮我审查当前代码变更并跑全链路测试。"

### 3. 一秒收割，直接贴入测试管理系统
按下回车后，系统会自动套用内置模板，硬核输出标准化的表格（绝不输出啰嗦的废话）。  
经你运用测试经验微调核对后，可直接批量复制导入 禅道、TestRail 或飞书多维表格 中。

### 4. 收口前再过一遍 Reviewer Agent
当你已经拿到测试策略、用例或说明文档，准备提交或进入下一环节前，建议再补一次轻量复核：

> **Prompt**: "调用 `reviewer-agent`，对当前仓库做一次最小扰动复核；如果环境支持，请优先使用 `vibe-tools repo` 并按 'Minimalist Refactor' 原则输出。"

### 5. 只在需要时整理测试代码
如果你刚完成一轮 pytest、协议测试脚本或 fixture 开发，觉得代码已经可用但表达还不够紧凑，可以额外调用：

> **Prompt**: "使用 `test-code-simplifier` 只整理当前测试代码，保持行为不变，不扩大改动范围。"

若你想先理解 `reviewer-agent` 与 `test-code-simplifier` 的共性边界，可先阅读：
`docs/user_guides/qa_cleanup_principles_zh.md`

---

## 四、常见问题

### Q1：AI 生成的用例漏掉了我们现场某个特定的硬件工况怎么办？
这很正常，常见原因是原始素材没有交代环境背景。你可以不必重新出题，直接在对话框追问："如果此时刚好把通信网线拔掉，你在上面的表里再加几条怎么加？"
### Q2：我想把其他的测试心法也转化为 AI 技能（比如多维复合路径、复杂状态机）？
除了现有的核心引擎外，如果你有自己得心应手的方法论，你可以呼叫 AI 并丢给它这个要求，AI 会根据内置的 `skill-creator` 自动为你生成新的专属测试插件存放于 `skills/` 目录下！

---

## 变更记录

| 版本 | 日期 | 作者 | 变更说明 |
| :--- | :--- | :--- | :--- |
| **v2.6** | 2026-04-04 | QA Team | 新增 `regression-test` 工作流、Bug 模式库（`.agents/assets/bug-patterns.md`）、ESLint 自定义规则、pre-commit hook；拆分"从 0 到 1"与"回归测试"两条工作流 |
| **v2.5** | 2026-03-25 | QA Team | 将 `webapp-testing` 与 `test-driven-development` 收敛为按需辅助 Skill，去除外来模板痕迹，明确其暂不纳入推荐主线。 |
| **v2.4** | 2026-03-25 | QA Team | 新增测试 Skills 治理与版本基线说明，补齐 `test-strategy-planner`、`issue-reporter`、`protocol-fuzzing-test` 等技能入口，并明确 `test-plan-copilot` / `bva-boundary-value-analysis` 的边界；同时将 `protocol-fuzzing-test` 定位收敛为包含靶机设计的方法论型 Skill。 |
| **v2.3** | 2026-03-25 | QA Team | 新增 `test-code-simplifier`，用于测试代码开发过程中的低扰动简化收口，明确其为按需调用而非默认步骤。 |
| **v2.2** | 2026-03-25 | QA Team | 新增 `reviewer-agent` 收口复核能力，并引入基于 `vibe-tools repo` 的整仓上下文审查建议，工作流升级为四段式。 |
| **v2.1** | 2026-03-24 | QA Team | **文档自动化套件收拢**：全量加入 TP-001/TCS-001/TR-001/BUG-001 标准体系工控基石模板，重构对应的 3 项一键自动化 Skills。剔除全系列 Emoji 与非中文翻译干扰冗余，严肃工程标准。 |
| **v2.0** | 2026-03-22 | QA Team | **大版本升级**：废弃手动复制变量填表制，全面升级为通过唤醒 AI Skills 的自动化无感工作流；剔除冗余开发套件；集成了 `studyInspire` 项目的顶尖方法论沉淀。 |
| **v1.0** | 2026-03-22 | QA Team | 初始版本（基于手动创建并复制 Markdown 文本模板执行） |
