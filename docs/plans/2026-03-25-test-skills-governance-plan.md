# 测试 Skills 治理与版本管理方案

> **日期**：2026-03-25
> **目标**：收敛 `qa-prompts` 中测试相关 Skills 的职责边界，减少过度设计与重复触发，并为后续演进建立统一的版本管理基线。

## 1. 当前问题摘要

本轮审查发现四类高优先级问题：

1. **主链路口径分叉**：`README.md`、Workflow 与核心 Skill 同时存在 `P1-P5` 和 `P0-P4` 两套模型表述。
2. **职责边界模糊**：`test-plan-copilot` 与 `test-strategy-planner`、`bva-boundary-value-analysis` 与 `test-case-factory` 的使用边界不够清晰。
3. **治理元数据不完整**：多个测试 Skill 缺少 `version` 与 `last_updated`，不满足仓库的技能版本化要求。
4. **说明口径不统一**：部分测试 Skill 以英文为主，入口文档对技能分层展示也不完整，影响团队理解与调度。

## 2. 治理目标

本次治理分三个层次落地：

1. **统一主链路**：明确测试交付主链路固定为  
   `requirement-reviewer` -> `test-strategy-planner` -> `test-case-factory` -> `reviewer-agent`
2. **收敛专项技能边界**：保留专项 Skill，但要求其只解决清晰的局部问题，不再与主链路争夺同一职责。
3. **建立版本基线**：为测试相关 Skill 统一补齐 `version` / `last_updated`，并约定语义化升级规则。

## 3. 技能分层与职责收敛

### 3.1 主链路技能

| Skill | 定位 | 输出物 | 调度规则 |
| :--- | :--- | :--- | :--- |
| `requirement-reviewer` | 需求审计 | 风险/歧义表 | 只做挑刺，不生成正式测试计划 |
| `test-strategy-planner` | 通用测试策略设计 | P1-P5 测试矩阵 | 只做架构层规划，不直接展开详细用例 |
| `test-case-factory` | 正式用例生产 | 符合 TCS 的测试用例集 | 只在策略确认后生成正式用例 |
| `reviewer-agent` | 提交前收口复核 | 一致性问题摘要 | 只做复核，不代替主链路前序技能 |

### 3.2 专项测试设计技能

| Skill | 建议定位 | 与主链路关系 |
| :--- | :--- | :--- |
| `bva-boundary-value-analysis` | 字段级/参数级边界值快速出表工具 | 不替代 `test-case-factory` 的完整 TCS 用例产出 |
| `exploratory-testing-persona` | 探索性/破坏性测试切入点生成器 | 作为补充视角，不替代结构化用例设计 |
| `protocol-fuzzing-test` | 工业协议专项鲁棒性测试方法论 | 只在 Modbus/CAN 等协议场景触发，不并入主链默认步骤；主体覆盖靶机设计，不绑定具体工具实现 |
| `issue-reporter` | 缺陷单标准化生成 | 承接测试执行结果，不参与测试设计主链 |

### 3.3 领域扩展技能

| Skill | 建议定位 | 治理动作 |
| :--- | :--- | :--- |
| `test-plan-copilot` | 储能/电力系统垂直领域的 `TP-001` 计划生成器 | 明确其为行业专版，不与 `test-strategy-planner` 抢通用规划职责 |

### 3.4 工程验证辅助技能

| Skill | 建议定位 | 治理动作 |
| :--- | :--- | :--- |
| `verify-requirements` | 基于代码证据的需求实现核验 | 从“测试设计 Skill”中剥离为“实现核验辅助” |
| `webapp-testing` | 本地 Web UI 执行验证工具 | 归类为执行/验证工具，不替代测试设计 Skill，当前按需保留 |
| `test-driven-development` | 工程实践约束 | 归类为开发纪律 Skill，不纳入 QA 资产主链，当前按需保留 |
| `test-code-simplifier` | 测试代码低扰动收口 | 保持可选，不升格为默认步骤 |
| `test-report-reviewer` | 执行结果报告生成 | 与主链后段衔接，但不参与前端测试设计 |

## 4. 过度设计与冗余处置策略

### 4.1 过度设计

以下 Skill 不建议继续膨胀能力范围：

1. `protocol-fuzzing-test`  
   保留为工业协议专项 Skill，但应收敛为“靶机设计 + 方法论主体 + 参考实现附录”，避免正文退化成具体工具说明书。
2. `verify-requirements`  
   保留为代码符合性核验 Skill，并收敛为“先抽取需求，再按仓库结构自适应搜索”的风格，减少对固定目录结构的强假设。
3. `test-driven-development`  
   保留为工程纪律 Skill，但不再作为 QA 测试设计目录中的核心能力宣传，内容收敛为最小方法说明。

### 4.2 冗余与边界不清

1. `test-plan-copilot` vs `test-strategy-planner`  
   保留两者，但前者限定为“储能/电力/工控 TP-001 模板化计划”，后者固定为通用 P1-P5 策略矩阵。
2. `bva-boundary-value-analysis` vs `test-case-factory`  
   保留两者，但前者只负责字段级快刀输出，后者负责正式 TCS 用例集。

## 5. 版本管理规则

测试 Skill 统一采用语义化版本号 `vX.Y.Z`：

1. **Patch (`Z`)**  
   只修正文案、错别字、元数据、链接、示例，不改变技能角色、输出结构或触发边界。
2. **Minor (`Y`)**  
   调整技能触发边界、输出结构、主分类模型、职责说明，但保持整体角色不变。
3. **Major (`X`)**  
   技能被合并、拆分、弃用，或输出契约发生不兼容变化。

所有测试 Skill 的每次改动都必须同步：

1. 更新 `version`
2. 更新 `last_updated`
3. 在入口文档中补齐技能分类或边界变化
4. 若影响主链路或模板口径，必须同步更新 `docs/plans/` 或用户指南

## 6. 本次建立的版本基线

| Skill | 当前版本 | 本次动作 |
| :--- | :--- | :--- |
| `requirement-reviewer` | `v1.0.0` | 补齐版本元数据 |
| `test-strategy-planner` | `v1.1.0` | 统一为 P1-P5 主模型 |
| `test-plan-copilot` | `v1.1.0` | 明确为储能/电力垂直领域计划 Skill |
| `test-case-factory` | `v1.2.0` | 与 P1-P5 主模型对齐 |
| `test-report-reviewer` | `v1.0.0` | 补齐版本元数据 |
| `test-code-simplifier` | `v1.0.0` | 维持现状，纳入版本基线 |
| `reviewer-agent` | `v1.0.1` | 修正文案错误并收紧复核口径 |
| `issue-reporter` | `v1.0.1` | 统一中文描述口径 |
| `protocol-fuzzing-test` | `v1.2.0` | 纳入靶机设计方法，收敛为方法论型 Skill，工具脚本降级为参考实现 |
| `bva-boundary-value-analysis` | `v1.1.0` | 明确与 `test-case-factory` 的边界 |
| `exploratory-testing-persona` | `v1.1.0` | 明确为补充性探索技能 |
| `verify-requirements` | `v1.2.0` | 收敛为自适应代码证据核验方法，去除固定目录结构假设 |
| `webapp-testing` | `v1.2.0` | 收敛为按需启用的本地 Web 验证辅助 Skill |
| `test-driven-development` | `v1.2.0` | 收敛为按需启用的最小 TDD 辅助 Skill |

## 7. 后续演进建议

下一阶段建议继续做三件事：

1. **中文化收口**：将仍以英文为主的测试 Skill 正文逐步翻译为中文，并保留必要英文术语括注。
2. **建立变更记录模板**：为测试 Skill 建立统一的简短 changelog 规范，至少记录最近一次职责变化。
3. **入口文档单点收敛**：后续将 `README.md` 与 `docs/onboarding.md` 中的测试技能目录抽成一份共享清单，避免再次分叉。
