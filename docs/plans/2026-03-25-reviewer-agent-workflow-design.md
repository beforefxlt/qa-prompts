# Reviewer Agent 接入工作流设计说明

> **日期**：2026-03-25
> **目标**：在 `qa-prompts` 的既有 Workflow 编排中补上一道轻量级复核关口，避免测试资产已经生成但 README、指南与技能说明仍停留在旧版流程。

## 1. 设计动机

现有 `test-lifecycle` 工作流已经具备“需求审计 -> 策略规划 -> 用例生成”的三段式骨架，但缺少一个统一的收口代理来做以下事情：

1. 对照整仓现状检查新流程与旧文档是否分叉。
2. 在真正进入提交或交付动作前，执行一次最小扰动复核，优先暴露高价值问题。
3. 约束新增 Skill 资产满足中文说明、版本元数据与更新时间等仓库治理要求。

因此，本次设计引入 `reviewer-agent` 作为工作流末端关卡。

## 2. 编排调整

`test-lifecycle` 从三段式扩展为四段式：

1. `requirement-reviewer`：识别需求歧义与 P3/P5 风险。
2. `test-strategy-planner`：输出 P1-P5 测试矩阵。
3. `test-case-factory`：将策略固化为正式测试用例。
4. `reviewer-agent`：对最终资产执行一致性复核，并输出“必须修正 / 建议优化 / 可接受风险”摘要。

## 3. Reviewer Agent 的工具链策略

### 首选方案：vibe-tools

若环境中已安装 `vibe-tools`，优先使用其 `repo` 能力，将整个仓库作为审查上下文交给 AI，并明确指定 “Minimalist Refactor” 风格的审查目标。该模式适合发现以下问题：

- 工作流步骤已经新增，但 README 或用户指南仍未同步。
- 新增 Skill 缺少版本号、最后更新时间或中文说明。
- 本轮改动与仓库既有命名、目录职责或交付口径不一致。

### 降级方案：本地文件复核

若 `vibe-tools` 未安装或不可用，则退化为读取本地关键文件：

- `.agents/workflows/`
- `skills/`
- `README.md`
- `docs/user_guides/`
- `docs/plans/`

此时仍保持“最小扰动复核”原则，只输出高信噪比问题。

## 4. 输出约束

Reviewer Agent 的输出必须满足以下约束：

1. 面向人的说明统一使用中文。
2. 只保留真正影响交付一致性的结论，避免泛化为大段最佳实践宣讲。
3. 对阻断性问题明确归类到“必须修正”，便于在提交前执行拦截。

## 5. 影响范围

本次接入影响以下资产：

- `.agents/workflows/test-lifecycle.md`
- `skills/reviewer-agent/SKILL.md`
- `docs/user_guides/test_lifecycle_guide.md`
- `README.md`

这样可以确保编排定义、用户操作说明与仓库总览保持同一口径。
