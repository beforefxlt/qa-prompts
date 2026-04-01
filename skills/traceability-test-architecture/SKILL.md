---
name: traceability-test-architecture
version: v1.1.0
last_updated: 2026-04-01
description: 为项目建立基于规格编号的可追溯测试架构，涵盖 TC 编号体系、traceability.yaml 映射、unit/contract/integration/resilience/golden 分层、统一审计报告与 TDD 门禁。适用于用户要求设计测试体系、建立测试追溯关系、统一质量入口、统计自动覆盖缺口、或将 SPEC 与测试实现强绑定的场景。
---

# 可追溯测试架构技能

## 目标

把“规格、测试、代码、审计”收敛到一套可机读、可门禁、可长期演进的测试架构中。

你的输出不应只是一批测试文件，而应至少产出以下其中几项：

- `traceability.yaml`
- 分层后的测试目录
- 带 `TC-*` 编号的测试描述
- 统一执行入口脚本
- 覆盖审计脚本或审计摘要
- 与工作流门禁对应的检查规则

## 直接复用资源

如果项目还没有任何测试骨架，优先复用本 Skill 自带资源，而不是从零手写：

- `assets/scaffold/traceability.yaml`
- `assets/scaffold/scripts/qa_unit.py`
- `assets/scaffold/scripts/qa_contract.py`
- `assets/scaffold/scripts/qa_integration.py`
- `assets/scaffold/scripts/qa_resilience.py`
- `assets/scaffold/scripts/qa_golden.py`
- `assets/scaffold/scripts/qa_e2e.py`
- `assets/scaffold/scripts/qa_all.py`
- `assets/scaffold/scripts/qa_audit.py`

需要快速检查初始化顺序时，阅读：

- `references/bootstrap-checklist.md`

## 先做什么

1. 先确认规格来源。
2. 先抽取正式 TC 列表。
3. 先建立追溯映射。
4. 再重构测试目录和执行入口。
5. 最后再讨论门禁。

不要先搬目录再想映射，也不要先写测试再补编号。

## 规格来源优先级

优先查找以下文件：

- `PRD.md`
- `UI_SPEC.md`
- `API_CONTRACT.md`
- `TEST_STRATEGY.md`
- `test_strategy_matrix.md`
- 其他显式的 `SPEC.md`

如果存在多个规格文件，必须先识别：

- 哪些文档定义业务承诺
- 哪些文档定义接口承诺
- 哪些文档定义测试矩阵

## 编号规则

默认采用：

- `TC-P1-001`
- `TC-P2-001`
- `TC-P3-001`
- `TC-P4-001`
- `TC-P5-001`

要求：

- 编号稳定，不随测试文件名变化而变化。
- 测试描述应显式包含完整编号。
- 不要混用 `P5-01` 和 `TC-P5-001`。

## traceability.yaml 最小要求

每个条目至少包含：

- `tc_id`
- `title`
- `level`
- `layer`
- `spec_source`
- `code_paths`
- `tests`
- `status`

其中：

- `tests` 至少写到测试文件和测试函数名
- `status` 至少区分 `automated`、`stub`、`manual`、`missing`

## 测试分层规则

推荐物理目录：

```text
backend/tests/
  unit/
  contract/
  integration/
  resilience/
  golden/
```

划分口径：

- `unit`：纯函数、规则引擎、模型约束、本地组件
- `contract`：API 路由、schema、SPEC 对齐、接口契约
- `integration`：数据库、服务协作、主链编排
- `resilience`：外部依赖失败、超时、重试、降级
- `golden`：黄金样本、快照、标准输入输出基线

若原仓库已有部分分层，优先兼容迁移，不要破坏现有发现机制。

## 前端 E2E 规则

前端 `test()` 描述必须带完整 `TC-P5-xxx` 编号。

示例：

```ts
test('TC-P5-001 首页空状态文案清晰可读', async ({ page }) => {
  // ...
})
```

如果测试本质上是主流程成功路径，也可以映射到 `P1`，但在前端验收项目里通常优先落在 `P5`。

## 统一入口规则

优先建立一个统一入口，并默认采用 Python 编排脚本，以适配后续非 Windows 的 CI/CD 环境，例如：

- `scripts/qa_all.py`
- `scripts/qa_audit.py`

默认执行顺序：

1. `python scripts/qa_unit.py`
2. `python scripts/qa_contract.py`、`python scripts/qa_integration.py`
3. `python scripts/qa_e2e.py`
4. 契约扫描
5. 追溯审计

输出必须包含：

- 总 TC 数
- 自动覆盖数
- Stub 数
- 缺失数
- 失配数

## 分层编排脚本规则

项目初始化阶段就应创建分层编排脚本骨架，不要等测试变多后再补。

推荐至少建立：

- `scripts/qa_unit.py`
- `scripts/qa_contract.py`
- `scripts/qa_integration.py`
- `scripts/qa_resilience.py`
- `scripts/qa_golden.py`
- `scripts/qa_e2e.py`
- `scripts/qa_all.py`
- `scripts/qa_audit.py`

原则：

- 即使某一层当前没有测试，也先创建空骨架。
- 新增测试时，优先挂入既有脚本对应的集合。
- 本地开发、CI、交付审计应尽量复用同一套 Python 脚本命名。
- 不要默认依赖 `.ps1`，除非项目明确只在 Windows 内部环境运行。
- `qa_all.py` 负责全链执行，`qa_audit.py` 负责只输出覆盖缺口和追溯摘要。

这样做的目的不是方便，而是防止测试增长后执行口径漂移。

如果项目尚未创建这些文件，优先从本 Skill 的 `assets/scaffold/` 复制，再按项目实际目录微调。

## 门禁规则

### 可追溯性门禁

检查：

- `traceability.yaml` 新增条目是否有对应测试函数
- 测试函数是否真实存在
- 新增测试是否带 `TC-*`
- 新增规格是否同步进入追溯表

### TDD 顺序门禁

检查：

- 修改功能性 `SPEC.md` 时是否同步提交测试 Stub
- 新增规格条目但无测试条目时阻断
- 有新页面或新接口定义但无测试映射时阻断

注意对纯文案修订降级处理，避免误伤。

## 输出格式建议

完成工作后，优先输出：

1. 已建立的编号与追溯策略
2. 已落地的目录与脚本
3. 当前覆盖统计
4. 仍缺失的条目与下一步风险

## 常见反模式

- 先搬测试目录，再回填映射
- 只做目录分层，不做 `traceability.yaml`
- 不建分层执行脚本，等测试变多后再临时拼命令
- E2E 名称不带编号
- 只报 `Pass/Fail`，不报缺口
- SPEC 变更后没有同步 stub

## 配套参考

需要理解设计思想时，优先阅读：

- `docs/user_guides/traceability_test_design_guide.md`

需要执行需求落地核验时，可结合：

- `skills/verify-requirements/SKILL.md`

需要制定 P1-P5 测试矩阵时，可结合：

- `skills/test-strategy-planner/SKILL.md`
