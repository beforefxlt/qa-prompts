# ⚡ 储能/电力控制系统质量保障 AI 工具箱 (QA AI Toolkit)

> 从“人肉写用例”到“AI 外挂脑补”，专注于硬件在环(HIL)、涉网规约与工控红线的测试自动化生成体系。

## 📋 目录
- [概述](#概述)
- [核心双擎架构](#核心双擎架构)
- [资产列表：Templates (标准化模板)](#资产列表-templates-标准化模板)
- [资产列表：Skills (智能组装厂)](#资产列表-skills-智能组装厂)
- [快速开始](#快速开始)
- [目录结构](#目录结构)

---

## 概述

本仓库专为**电力、储能及工业控制系统（EMS/BMS/PCS）**的测试全生命周期打造。我们摒弃了纯互联网软件的测试方法论，转而采用以“硬件隔离、通讯规约、交叉依赖溯源”为核心的强管控体系。

基于 AI 大模型的理解能力，我们构建了 **“标准模板约束 + 智能 Skill 自动化填表”** 的双擎框架，让底层软硬件联调中高频、繁杂的度量与文档工作变得极度敏捷，大幅释放 QA 人力去探索深水区的系统缺陷。

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
| **TC-001** | 核心用例表单 | 北南向规约验证、包含前置稳态与录波抓包证据链 | `templates/test-case-template.md` |
| **TR-001** | 全量迭代报告 | 提测首挂率计算、安全红线排雷与质量放行信心 | `templates/test-report-template.md` |
| **BUG-001**| 缺陷排查单 | 缺陷影响面推演、必现条件隔离与核心系统日志溯源 | `templates/defect-report-template.md` |

---

## 资产列表：Skills (智能辅助流)

在集成后台交互工具内输入触发词，即可秒级产出正规物料：

### 📝 文档自动化流 (Docs Pipeline)
- 🤖 `@test-plan-copilot`：投喂需求段落，AI 帮你填补“工控配置矩阵”与“系统级依赖重灾区”，产出 `TP-001` 草案。
- 🤖 `@test-case-factory`：投喂接口文档或现象，AI 强拉格式分离稳态环境/激励步骤/抓包证据，产出 `TC-001` 严谨用例。
- 🤖 `@test-report-reviewer`：投喂流水账战果，自动算硬红线度量（首挂率），套成 `TR-001` 给出无懈可击的技术放行建议。

### 🔪 深度破坏探索流 (Deep Fuzzing)
- 🤖 `@requirement-reviewer`：侦测产品需求里隐藏的技术逻辑黑洞与控制死区缺失。
- 🤖 `@bva-boundary-value-analysis`：针对 API 发掘出（含超界/非法/越限闭锁）的严密死角组合。
- 🤖 `@exploratory-testing-persona`：注入极端干涉手段（断网/防孤岛风暴/无应答重试）的自由测试切入点指引。

---

## 快速开始

如果希望亲手建立你的 AI 测试防线，建议你的第一站是阅读团队的新手教程：
👉 **[`docs/onboarding.md`](./docs/onboarding.md)** 了解整个外挂工作流的详细串联玩法。

> **架构进阶**：要获取更为宏观的测试质量策略大图及团队管理沉淀，请查阅历史宝藏库 `docs/studyInspire-insights/INDEX.md`。

---

## 核心目录结构

```text
qa-prompts/
├── skills/                     # [智能外挂] AI 调用技能库
│   ├── test-plan-copilot/      # 自动分析推演 测试计划
│   ├── test-case-factory/      # 自动剥离隔离 测试用例
│   ├── test-report-reviewer/   # 自动撰写研判 战报放行单
│   ├── bva-boundary-value-analysis/
│   ├── requirement-reviewer/
│   └── exploratory-testing-persona/
├── templates/                  # [基石资产] 极度职业化的工控模板
│   ├── test-plan-template.md
│   ├── test-case-template.md
│   ├── test-report-template.md
│   └── defect-report-template.md
├── docs/                       # [指引沉淀]
│   ├── onboarding.md           # 团队上岗与系统使用操作手册
│   └── studyInspire-insights/  # 深层次测试架构师经验沉淀
└── README.md                   # 根索引
```
