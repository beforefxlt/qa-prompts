---
description: 家庭检查单管理应用 AI 交付流水线 (Health Record App Delivery Workflow)
version: v1.0.0
last_updated: 2026-03-30
---

# 家庭检查单管理应用 AI 交付流水线

> **触发条件**：当用户准备从 0 到 1 开发“家庭检查单管理应用”或同类健康数据管理产品时，启动本流程。
> **核心原则**：先规格冻结，再测试驱动，再按明确边界拆 Subagent 并行开发。禁止跳过 UI 规格、OCR 样本与测试门禁直接写实现。

## Step 1: 产品与风险收敛

1. 收集产品目标、目标用户、核心指标、隐私边界。
2. 使用 `requirement-reviewer` 审计需求真空、隐私风险、P3/P5 缺口。
3. 将阶段结论写入 `/tmp/health_record_requirement_audit.md`。
4. 用户确认需求范围后再进入下一步。

## Step 2: UI 规格冻结

1. 输出信息架构、页面清单、关键任务流、低保真线框要求。
2. 重点固化上传、OCR 审核、趋势图、报警红区四类页面。
3. 将结果写入 `/tmp/health_record_ui_spec.md`。
4. 用户确认页面结构后再进入架构设计。

## Step 3: 技术架构与数据模型设计

1. 输出系统模块图、数据模型、OCR 链路、规则引擎边界、部署结构。
2. 明确原始抽取结果与正式 observation 的分层关系。
3. 将结果写入 `/tmp/health_record_architecture.md`。
4. 用户确认架构后再进入测试设计。

## Step 4: 测试策略冻结

1. 使用 `test-strategy-planner` 输出 P1-P5 测试矩阵。
2. 强制补齐 OCR Golden Set、规则引擎、E2E、隐私与容灾测试。
3. 将结果写入 `/tmp/health_record_test_strategy.md`。
4. 用户确认测试门禁后再进入实施计划。

## Step 5: 实施计划拆解

1. 使用 `writing-plans` 思路拆成可执行任务。
2. 每个任务必须写清：目标、输入规格、输出文件、测试方式、禁止修改范围。
3. 任务粒度以 2 到 8 小时为宜，避免“大而全任务包”。
4. 计划文件进入正式仓库路径。

## Step 6: Subagent 并行开发

1. 使用 `subagent-driven-development` 执行计划。
2. 按写域拆分 `UI / API / OCR / Data / QA`。
3. 每个 Subagent 必须先写失败测试，再实现最小代码。
4. 每个任务完成后必须依次执行：
   - 规格一致性复核
   - 代码质量复核

## Step 7: 集成与回归

1. 合并实现后跑单元测试、API 合约测试、集成测试。
2. 跑 OCR Golden Set 回归。
3. 跑前端 E2E 与关键页面截图检查。
4. 若隐私脱敏、单位校验或审核状态流失败，直接阻断交付。

## Step 8: 核验与收口

1. 使用 `verify-requirements` 逐条核验规格是否落地。
2. 使用 `reviewer-agent` 做最终一致性与文档同步复核。
3. 若文档、测试、架构说明未同步，不允许进入提交阶段。
