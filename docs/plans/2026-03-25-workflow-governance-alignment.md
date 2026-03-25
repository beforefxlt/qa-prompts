# 工作流治理对齐说明

> **日期**：2026-03-25
> **目标**：对齐 `.agents/workflows/` 与最新测试 Skill 治理方案，修正过时编排、资产边界冲突与入口文档遗漏。

## 1. 本次修正范围

涉及以下资产：

- `.agents/workflows/test-lifecycle.md`
- `.agents/workflows/bug-diagnostic-flow.md`
- `README.md`
- `docs/user_guides/test_lifecycle_guide.md`

## 2. 关键问题

### 2.1 `bug-diagnostic-flow` 与仓库总规范冲突

原流程要求将 `BUG-001` 正式文档写入仓库内 `docs/defects/`。  
这与仓库总规范中“Bug 分析单属于单次应用产物，严禁上传至 Git 库”的要求冲突。

### 2.2 `bug-diagnostic-flow` 存在过时执行描述

原流程仍使用“强制调用 `view_file`”“彻底忘掉上游对话原话”这类过时或不精确表述，不利于在当前 Agent 环境中稳定执行。

### 2.3 `test-lifecycle` 与最新 Skill 边界需要显式对齐

随着 `bva-boundary-value-analysis`、`test-plan-copilot`、`test-code-simplifier` 等 Skill 完成边界收敛，主工作流需要明确：

- 谁属于主链
- 谁属于专项工具
- 谁只在用户明确要求时按需启用

### 2.4 入口文档遗漏 `bug-diagnostic-flow`

根 README 的 Workflow 列表只展示了 `test-lifecycle`，未将已存在的 `bug-diagnostic-flow` 纳入入口说明，导致用户对可用工作流认知不完整。

## 3. 修正动作

### 3.1 `bug-diagnostic-flow`

1. 明确 `BUG-001` 草稿默认只落在 `/tmp/bug_report_draft.md`
2. 明确默认不直接进入 Git 仓库
3. 在正式建单阶段优先复用 `issue-reporter`
4. 将过时的 `view_file` 和“彻底忘掉”表述，改为“只读取上一步物理结果继续分析”

### 3.2 `test-lifecycle`

1. 保持主链固定为  
   `requirement-reviewer -> test-strategy-planner -> test-case-factory -> reviewer-agent`
2. 显式声明 `bva-boundary-value-analysis` 与 `test-plan-copilot` 不替代主链步骤
3. 显式声明 `test-code-simplifier` 不是默认步骤，只能在用户明确要求时按需插入

### 3.3 文档入口

1. 在 `README.md` 中补充 `bug-diagnostic-flow`
2. 在 `docs/user_guides/test_lifecycle_guide.md` 中补充主链与辅助 Skill 的边界说明

## 4. 对齐后的工作流原则

1. **主链稳定**：主交付工作流只保留最小必要步骤
2. **辅助技能按需插入**：专项 Skill 不自动膨胀主流程
3. **单次诊断资产不入库**：Bug 草稿默认停留在 `/tmp/` 或外部系统
4. **入口文档必须同步**：Workflow 调整后，README 与用户指南同步更新
