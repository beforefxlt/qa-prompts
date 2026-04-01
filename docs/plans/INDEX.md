# 方案与设计索引

本目录收录与仓库治理、工作流设计、架构调整相关的说明文档。  
这些文档主要回答两类问题：

1. 某个能力为什么这样设计
2. 某次治理、收敛或对齐具体改了什么

如果你想直接使用仓库能力，优先看 `docs/onboarding.md` 或 `docs/user_guides/`；  
如果你想理解背后的设计取舍、治理边界和演进脉络，再进入本目录。

## 推荐阅读顺序

1. 想先理解测试 Skills 的收敛与版本基线：
   `docs/plans/2026-03-25-test-skills-governance-plan.md`
2. 想理解 workflow 为什么要这样调整：
   `docs/plans/2026-03-25-workflow-governance-alignment.md`
3. 想理解 `reviewer-agent` 是如何接入主流程的：
   `docs/plans/2026-03-25-reviewer-agent-workflow-design.md`
4. 想看更早期的案例型设计背景：
   `docs/plans/2026-03-24-factory-inspection-design.md`
5. 想看 AI 驱动的家庭检查单管理应用工作流设计：
   `docs/plans/2026-03-30-family-health-record-app-workflow-design.md`

## 文档列表

| 文档 | 类型 | 说明 |
| :--- | :--- | :--- |
| `docs/plans/2026-03-25-test-skills-governance-plan.md` | 治理方案 | 说明测试 Skills 的边界、版本管理和收敛策略 |
| `docs/plans/2026-03-25-workflow-governance-alignment.md` | 对齐说明 | 说明 workflow 与最新 Skill 治理方案如何完成对齐 |
| `docs/plans/2026-03-25-reviewer-agent-workflow-design.md` | 设计说明 | 说明 `reviewer-agent` 接入主工作流的设计动机与影响范围 |
| `docs/plans/2026-03-24-factory-inspection-design.md` | 架构设计 | 较早期的工厂检测案例设计说明 |
| `docs/plans/2026-03-30-family-health-record-app-workflow-design.md` | 工作流设计 | 说明家庭检查单管理应用的规格冻结、测试门禁与 Subagent 协作方式 |
| `docs/plans/2026-04-01-workflow-v2-retrospective.md` | 复盘改进 | 基于 v1.5.0 实践的工作流 v2.0.0 升级设计说明（拆分 UI 步骤、硬门禁、页面完整性检查） |

## 与其他文档的关系

- 要看“怎么用”，去 `docs/user_guides/`
- 要看“先从哪开始”，去 `docs/onboarding.md`
- 要看“案例与培训材料”，去 `docs/training/`
- 要看“长期方法论沉淀”，去 `docs/studyInspire-insights/`
