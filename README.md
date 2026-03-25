# ⚡ 工业与复杂系统质量保障 AI 工具箱 (QA AI Toolkit)
 
> 从“人肉写用例”到“AI 架构赋能”，专注于工业控制、软硬联调与复杂系统质量红线的全自动测试生成体系。

## 📋 目录
- [概述](#概述)
- [核心双擎架构](#核心双擎架构)
- [资产列表：Templates (标准化模板)](#资产列表-templates-标准化模板)
- [资产列表：Skills (智能组装厂)](#资产列表-skills-智能组装厂)
- [工作流：Workflows (智能管家 SOP)](#工作流-workflows-智能管家-sop)
- [快速开始](#快速开始)
- [目录结构](#目录结构)

---

## 🌟 这个 Toolkit 是什么？能做些什么？

本仓库并非一堆冷冰冰的代码，而是一套**专为“各类复杂工业软件与嵌入式系统”量身定制的【AI 高级测试架构师】**。
我们摒弃了纯互联网软件“点点点”的测试方法，将**资深测试专家的思想模型（如 P0-P4 维度监控、出厂硬件隔离、通讯规约红线）**硬编码成了随叫随到的 AI 外挂技能 (Skills)。

### 💡 它能为您带来什么突破？
1. 🚀 **消灭零碎操作：一句话完成闭环**
   - 告别繁琐的手工填表。只要喂给它一段模糊的需求（如：“给厂测程序加个推日志的功能”），它会通过**工作流引擎**自动切分为：【挑刺审查找漏洞】 -> 【输出 P0-P4 策略网】 -> 【直接生成符合 TCS 标准的测试用例集 (TCC)】三部曲。
2. 🛡️ **填补毁灭性盲点：“不测理想状态，专死磕绝境”**
   - 代码里 `pytest` 全绿，一到产线就宕机？本工具箱内置了强大的**负向测试视界（P0: 环境没装这个命令怎么办？磁盘满了怎么办？ / P4: 二进制打包后这行代码还能运行吗？）**。让大模型强迫团队思考边缘问题。
3. 🐞 **深度靶向排错：超越简单的代码翻译**
   - Nginx+Docker 上线白屏却查不出日志？工业协议 (Modbus/CAN) 一直解析异常？本工具箱内置了工业特化的报错排查探针（Diagnosis Skills），帮 QA 瞬间读懂报错天书并转为专业隔离单。

**简而言之：它是让 QA 工程师从“写用例的工具人”，升维成在“上帝视角排兵布阵的指挥官”的核心武器库。**

---

## 核心双擎架构

```text
┌─────────────────────┐       自动化解析       ┌─────────────────────┐
│   原始模糊需求/战报   │ ──────────────────────▶│   标准结构化测试实体   │
│ (PRD/交接说明/故障截图)│  (唤醒专用的 AI Skill)  │ (计划/用例/度量报告/缺陷)│
└─────────────────────┘                        └─────────────────────┘
```

---

## 资产列表：Templates (标准化模板)

以下模板剔除了所有多余的情绪化词汇和排版干扰（无表情符号/过度翻译），可直接作为各部门流转及项目签字归档的正式文件：

| 模板编号 | 资产名称 | 适用边界 | 存储路径 |
| :--- | :--- | :--- | :--- |
| **TP-001** | 测试计划大纲 | 系统架构分析、硬件环境搭建、回归裁剪边界 | `templates/test-plan-template.md` |
| **TCS-001** | 通用用例规范 | 核心测试标准，涵盖 P1 基础路径（核心业务价值）及各维度证据链 | `templates/test-case-template.md` |
| **TR-001** | 全量迭代报告 | 提测首挂率计算、安全红线排雷与质量放行信心 | `templates/test-report-template.md` |
| **BUG-001**| 缺陷排查单 | 缺陷影响面推演、必现条件隔离与核心系统日志溯源 | `templates/defect-report-template.md` |

---

## 资产列表：Skills (智能辅助流)

在集成后台交互工具内输入触发词，即可秒级产出正规物料：

### 📝 文档与用例自动化流 (Docs & Test Pipeline)
- 🤖 `@requirement-reviewer`：侦测产品需求里隐藏的技术逻辑黑洞与控制死区缺失（强制左移）。
- 🤖 `@test-strategy-planner`：基于需求生成涵盖 P1-P5（基础、异常、基建、边界、交付视角）的全局测试矩阵。
- 🤖 `@test-case-factory`：自动剥离隔离前提/激励步骤，产出严格遵循 `TCS` 规范的严谨用例集 (TCC)。
- 🤖 `@test-report-reviewer`：投喂流水账战果，自动核算放行率，套成 `TR-001` 给出无懈可击的技术放行建议。
- 🤖 `@test-code-simplifier`：仅在测试代码开发、重构或提交前收口阶段启用，对 pytest 用例、fixture、协议测试脚本做低扰动简化；不是默认每轮都要调用。
- 🤖 `@reviewer-agent`：作为工作流收口关卡，专门复核 QA 工作流编排、测试资产完整性、文档同步性与技能治理合规性；若环境允许，优先结合 `vibe-tools repo` 执行 “Minimalist Refactor” 风格审查。
- 🤖 `@issue-reporter`：标准化缺陷追踪，从凌乱的现象推演成 `BUG-001` 隔离单。

### 🔪 深度排错与探索流 (Deep Fuzzing & Diagnostics)
- 🤖 `@nginx-docker-diagnosis`：精准定位容器化 Nginx 的 404/白屏/端口映射 等系统运维故障。
- 🤖 `@protocol-fuzzing-test`：(工业规约特化) 针对 Modbus/CAN 协议的底层负向注入与模糊测试策略。
- 🤖 `@code-to-business-doc`：给到遗留烂代码，逆向翻译出可读的业务 PRD。
- 🤖 `@bva-boundary-value-analysis`：针对 API 发掘出（含超界/非法/越限闭锁）的严密死角组合。
- 🤖 `@exploratory-testing-persona`：注入极端干涉手段（断网/风暴/重试）的自由测试切入点指引。

---

## 工作流：Workflows (智能管家 SOP)

告别让 AI “一把梭哈”的幻觉，我们将原子化的 Skill 通过 `.agents/workflows/` 强编排成了流水线。核心原则：**先通 Happy Path（业务价值核心），再挖异常边界，最后由 Reviewer Agent 做最小扰动复核**。

- 🌊 **`/test-lifecycle` (自动化测试交付流水线)**：输入特性描述，AI 将自动串联【审计 -> 策略 -> 用例 -> 复核】四段式流程，期间通过 `/tmp/` 保存中间产物防过拟合，并可在收口阶段优先调用 `vibe-tools repo` 做 QA 资产一致性复核。
  - 📖 参阅指南：[`docs/user_guides/test_lifecycle_guide.md`](./docs/user_guides/test_lifecycle_guide.md)

---

## 🏗️ 实战演兵：Factory Inspector (Reference Implementation)

本工具箱不仅仅是方法论，我们还随库附带了一个完整的生产级实战案例：**`factory_inspector`**。

这是为一个 **Ubuntu 边缘设备** 打造的模块化出厂检测工具，它完美示范了如何应用本 Toolkit 的核心思想：
- 🛠️ **插件化架构**：支持通过 Python 脚本快速扩展硬件检测项。
- 📦 **交付视角 (P5) 实践**：支持 `PyInstaller` 一键打包为二进制单文件，解决生产环境依赖地狱。
- 🧪 **P1-P5 全自动化用例**：内置了 30 个自动化测试项，支持高压验证。

👉 **[点击进入 Factory Inspector 项目实体](./factory_inspector/README.md)**

---

## ⚡ 核心演练场：Modbus Anomaly Test (Protocol Fuzzing)

针对工业通信规约安全，本项目包含了一套完整的 **Modbus 协议异常注入与鲁棒性验证框架**：
- 🛡️ **插件化漏洞靶机**：基于 Hook 架构的 `vulnerable_target.py`，支持动态注入 `OOB` (越界)、`Leak` (泄露) 等 6 类深度协议漏洞。
- 🔬 **工业特化 Fuzzer**：可模拟超长报文、TCP 分片截断、事务 ID (TID) 篡改等各种非标报文攻击。
- 📊 **P1-P5 闭环验证**：配套全量自动化测试套件与长时稳定性 (Soak) 监测工具。

👉 **[点击进入 Modbus Anomaly Test 获取工业规约测试能力](./modbus_anomaly_test/README.md)**

---

## 快速开始

如果希望亲手建立你的 AI 测试防线，建议你的第一站是阅读团队的新手教程：
👉 **[`docs/onboarding.md`](./docs/onboarding.md)** 了解整个外挂工作流的详细串联玩法。

> **📚 核心培训资产**：
> - 想要了解这套 AI 流程是如何重塑出厂检测工程的，请阅读最新案例：**[`docs/training/2026-03-24-factory-inspector-case-study.md`](./docs/training/2026-03-24-factory-inspector-case-study.md)** 及其配套 PPT大纲。
> - 要获取更宏观的测试架构演进，查阅 `docs/studyInspire-insights/INDEX.md`。

---

## 核心目录结构

qa-prompts/
├── .agents/workflows/          # [核心引擎] AI Agent 自动化作业流水线 (如 test-lifecycle.md)
├── skills/                     # [智能外挂] AI 原子调用技能库 (如 test-strategy-planner等)
├── templates/                  # [基石资产] 极度职业化的工控/测试管理模板表单
├── docs/                       # [指引沉淀]
│   ├── onboarding.md           # 团队上岗与系统使用操作手册
│   ├── user_guides/            # 具体 Workflow 与工具的使用说明
│   ├── training/               # 实战演练案例与教学 PPT
│   └── studyInspire-insights/  # 深层次测试架构师经验沉淀
├── factory_inspector/          # [实战练兵场] Ubuntu 边缘设备模块化出厂检测工具项目实体
└── README.md                   # 根索引
```
