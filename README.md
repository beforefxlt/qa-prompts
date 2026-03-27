# 测试架构与质量工程作品集

> QA Architecture & Engineering Portfolio

[![领域](https://img.shields.io/badge/领域-工业软件与复杂系统-blue.svg)]()
[![方向](https://img.shields.io/badge/方向-软硬件联调与质量治理-orange.svg)]()
[![结构](https://img.shields.io/badge/结构-Skills_%2B_Workflows-success.svg)]()

本仓库用于集中展示我在复杂系统测试架构、质量治理与 AI 测试工程化方向上的方法论沉淀和工程化落地。场景主要覆盖工业软件、边缘设备、协议通信、软硬件联调和交付环境验证。

它不是单一工具集合，而是一套围绕以下问题展开的质量工程作品集：
- 需求、策略、用例、缺陷分析长期割裂，缺少统一测试方法
- 工业软件和软硬件联调场景中，常规互联网测试套路覆盖不住环境异常和交付风险
- 大模型虽然能生成内容，但如果缺少编排、模板、治理和复核，测试资产很快失控

因此，这个仓库的重点不是“让 AI 多写文档”，而是把测试架构师和质量工程中的关键判断，沉淀成可复用、可组合、可治理的工程资产。

## 目录
- [核心工程贡献](#核心工程贡献)
- [代表性项目与能力证明](#代表性项目与能力证明)
- [质量编排架构](#质量编排架构)
- [标准化模板](#标准化模板)
- [Skills 能力资产](#skills-能力资产)
- [Workflows 流程资产](#workflows-流程资产)
- [文档导航](#文档导航)
- [快速开始](#快速开始)
- [目录结构](#目录结构)
---

## 核心工程贡献

这个仓库主要体现了以下几类测试架构与质量工程能力：

1. **设计 `Skills + Workflows` 双层编排架构**
   通过 `Skills + Workflows` 双层结构，将需求审计、测试策略、用例生成和最终复核拆成可治理的能力模块，降低长链路分析中的失控风险。

2. **抽象 `P1-P5` 复杂系统测试模型**
   通过 `P1-P5` 方法，将基础路径、业务异常、环境异常、边界条件和交付视角纳入统一测试框架，用于需求审计、策略设计和用例生成。

3. **重构缺陷分析为 `8D + QM` 体系复盘**
   通过 `8d-qm-analysis`、缺陷隔离流程和复盘规范，将问题分析从单点 Bug 扩展到流程失效、门禁失效和横向展开。

4. **推动测试资产与文档代码化治理**
   通过模板、版本元数据、工作流边界和文档索引，约束测试计划、用例、报告和缺陷单的一致性，避免测试资产分叉。

5. **围绕工业与复杂系统场景做工程化落地**
   通过 `factory_inspector`、`modbus_anomaly_test` 等实例，体现对协议异常、设备交付、环境脆弱性和产线质量风险的持续关注。

---

## 代表性项目与能力证明

### 1. `factory_inspector`

- **工程场景**：边缘设备和产线机台的出厂检测，重点关注“配置正确但环境脆弱”这类交付问题。
- **落地方式**：采用 Python 插件化检测架构，支持二进制打包，覆盖配置驱动、插件发现、环境异常兜底和 P1-P5 回归验证。
- **体现能力**：测试架构设计、交付环境验证、工程化回归体系、文档与测试同步治理。
- **入口**：[`factory_inspector/README.md`](./factory_inspector/README.md)

### 2. `modbus_anomaly_test`

- **工程场景**：工业通信协议鲁棒性验证，重点关注异常报文、链路干扰、时序错乱和实现脆弱点。
- **落地方式**：围绕协议异常注入、靶机设计、稳定性验证与观测指标构建测试框架，并沉淀为 `protocol-fuzzing-test` 方法论资产。
- **体现能力**：协议测试、fuzzing 思路抽象、靶机设计、复杂故障注入与风险建模。
- **入口**：[`modbus_anomaly_test/README.md`](./modbus_anomaly_test/README.md)

### 3. `8d-qm-analysis`

- **工程场景**：针对跨团队、跨系统、偶发性故障的根因分析和复盘，避免只停留在“谁写错了代码”。
- **落地方式**：以 QM 视角重构 8D，聚焦 D3、D4、D5、D7，强调发生根因、流出根因、防呆设计和横向排查。
- **体现能力**：质量治理、RCA 体系化、流程与门禁问责、复盘资产标准化。
- **入口**：[`skills/8d-qm-analysis/SKILL.md`](./skills/8d-qm-analysis/SKILL.md)

### 4. 测试主流程与治理方案

- **工程场景**：把需求分析、测试策略、用例沉淀和最终复核串成一条可维护的主流程。
- **落地方式**：通过 `/test-lifecycle` 工作流和技能治理方案，收敛测试资产边界、调用顺序、版本元数据和文档一致性要求。
- **体现能力**：方法论沉淀、工作流设计、测试资产治理、工程规范建设。
- **入口**：
  - [`.agents/workflows/test-lifecycle.md`](./.agents/workflows/test-lifecycle.md)
  - [`docs/plans/2026-03-25-test-skills-governance-plan.md`](./docs/plans/2026-03-25-test-skills-governance-plan.md)

---

## 质量编排架构

本仓库采用两层结构来组织测试与质量资产：

```text
原始输入
(需求 / 日志 / 故障现象 / 代码上下文)
        |
        v
Skills
(单点能力：需求审计、策略设计、协议测试、缺陷复盘)
        |
        v
Workflows
(多阶段编排：审计 -> 策略 -> 用例 -> 复核 / 问诊 -> 隔离 -> 建单)
        |
        v
标准化输出
(测试计划 / 用例 / 报告 / 缺陷草稿 / 复盘结论)
```

这个结构背后的重点是：
- `Skills` 负责沉淀单点能力
- `Workflows` 负责复杂任务拆解与上下文治理
- `Templates` 负责统一输出格式
- `Plans / Guides` 负责边界、治理和使用说明

---

## 标准化模板

仓库中的模板用于统一测试资产表达，避免测试过程只停留在口头沟通：

| 模板编号 | 资产名称 | 适用边界 | 存储路径 |
| :--- | :--- | :--- | :--- |
| `TP-001` | 测试计划大纲 | 系统架构分析、环境矩阵、范围裁剪 | `templates/test-plan-template.md` |
| `TCS-001` | 通用用例规范 | 标准测试步骤、前置条件、证据链表达 | `templates/test-case-template.md` |
| `TR-001` | 测试报告模板 | 首挂率、风险项、放行建议 | `templates/test-report-template.md` |
| `BUG-001` | 缺陷排查单 | 缺陷影响面、复现条件、日志线索 | `templates/defect-report-template.md` |

---

## Skills 能力资产

### 测试设计与交付主线
- `@requirement-reviewer`：审查需求中的歧义、逻辑真空和边界缺口
- `@test-strategy-planner`：按 `P1-P5` 模型生成结构化测试矩阵
- `@test-plan-copilot`：面向储能 / 电力场景补全系统级测试计划
- `@test-case-factory`：将测试点整理成符合 `TCS` 规范的正式用例集
- `@test-report-reviewer`：将执行结果整理为结构化放行报告
- `@reviewer-agent`：在交付前做最小扰动复核，检查一致性和治理合规

### 深度排错与专项方法
- `@issue-reporter`：将零散现象整理成标准缺陷草稿
- `@protocol-fuzzing-test`：基于 Modbus 等场景沉淀协议鲁棒性测试方法
- `@8d-qm-analysis`：以 QM 视角进行 D3 / D4 / D5 / D7 强化版 8D 复盘
- `@nginx-docker-diagnosis`：针对容器化 Nginx 典型故障进行隔离分析
- `@bva-boundary-value-analysis`：围绕边界值构建高强度输入矩阵
- `@exploratory-testing-persona`：提供弱网、误操作、高压切换等探索性视角

### 工程验证辅助能力
- `@verify-requirements`：基于代码证据判断需求是否真正实现
- `@webapp-testing`：本地 Web 应用轻量验证
- `@test-driven-development`：按需启用的最小 TDD 约束
- `@test-code-simplifier`：测试代码收口时的低扰动整理

如需看完整入口和边界说明，建议先看 [`docs/onboarding.md`](./docs/onboarding.md)。

---

## Workflows 流程资产

为了避免复杂任务完全依赖即时提示词，本仓库把高频流程收敛成了标准工作流：

- `/test-lifecycle`
  目标：把需求分析、测试策略、正式用例与最终复核串成闭环
  入口文档：[`docs/user_guides/test_lifecycle_guide.md`](./docs/user_guides/test_lifecycle_guide.md)

- `/bug-diagnostic-flow`
  目标：把现场问题从“现象描述”推进到“隔离分析 + BUG-001 草稿”
  入口文档：[`docs/user_guides/bug_diagnostic_flow_guide.md`](./docs/user_guides/bug_diagnostic_flow_guide.md)

---

## 文档导航

| 目标 | 建议先看 | 说明 |
| :--- | :--- | :--- |
| 快速建立整体认知 | `docs/onboarding.md` | 适合第一次进入仓库时看全景 |
| 浏览用户指南索引 | `docs/user_guides/INDEX.md` | 适合按流程挑 guide |
| 浏览治理方案索引 | `docs/plans/INDEX.md` | 适合按主题找设计说明和治理文档 |
| 看测试主交付流程 | `docs/user_guides/test_lifecycle_guide.md` | 适合了解完整 QA 主链 |
| 看缺陷初诊流程 | `docs/user_guides/bug_diagnostic_flow_guide.md` | 适合了解缺陷隔离与建单 |
| 看技能治理方案 | `docs/plans/2026-03-25-test-skills-governance-plan.md` | 适合看资产边界、版本与收敛策略 |
| 看 workflow 对齐说明 | `docs/plans/2026-03-25-workflow-governance-alignment.md` | 适合看流程为什么这样设计 |
| 看案例与培训材料 | `docs/training/` | 适合面试前挑代表性案例 |
| 看测试架构方法论沉淀 | `docs/studyInspire-insights/INDEX.md` | 适合系统理解方法论来源 |

---

## 快速开始

如果你是第一次阅读这个仓库，建议按下面顺序进入：

1. 阅读 [`docs/onboarding.md`](./docs/onboarding.md)，了解仓库全景与常用入口
2. 阅读 [`factory_inspector/README.md`](./factory_inspector/README.md)，看一个完整的工程化落地案例
3. 阅读 [`modbus_anomaly_test/README.md`](./modbus_anomaly_test/README.md)，看协议测试与异常注入能力
4. 阅读 [`docs/plans/2026-03-25-test-skills-governance-plan.md`](./docs/plans/2026-03-25-test-skills-governance-plan.md)，理解治理思路

---

## 目录结构

```text
qa-prompts/
├── .agents/workflows/          # 工作流编排定义
├── skills/                     # 单点能力技能库
├── templates/                  # 标准化测试与缺陷模板
├── docs/
│   ├── onboarding.md           # 总体上手文档
│   ├── user_guides/            # 用户指南与流程说明
│   ├── plans/                  # 治理方案、设计说明、对齐文档
│   ├── training/               # 案例与培训材料
│   └── studyInspire-insights/  # 方法论沉淀
├── factory_inspector/          # 出厂检测工程案例
├── modbus_anomaly_test/        # 协议异常测试工程案例
└── README.md                   # 根入口
```
