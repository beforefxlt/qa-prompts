# 家庭检查单管理应用工作流设计说明

## 背景

本轮讨论的目标不是直接开发，而是先把一个适合 AI 协作开发的项目工作流整理清楚，并以正式文档的方式沉淀到仓库。

该项目具备以下明显特征：
- 涉及隐私与敏感数据
- 依赖 OCR 与大模型结构化抽取
- 存在图表、趋势、阈值和派生指标
- 后续计划用多 Subagent 并行开发

因此，不能直接套用“普通 CRUD Web 应用”的轻量流程。

## 设计目标

- 先规格冻结，避免 AI 直接按想象编码
- 把 UI 设计提前到编码前
- 把 OCR Golden Set 与规则引擎校验前置为一等公民
- 把多 Subagent 并行开发纳入正式流程，而不是临时策略
- 让文档、测试、实现三者保持同步

## 工作流设计结论

推荐主链如下：

`需求审计 -> UI 规格 -> 架构设计 -> 测试策略 -> 实施计划 -> Subagent 并行 TDD -> 集成回归 -> 需求核验 -> 最终复核`

相对于仓库原有的通用测试主链，本方案新增并强调了四个环节：
- UI 规格冻结
- OCR 结构化与脱敏边界设计
- OCR Golden Set 回归
- Subagent 并行开发治理

## 借鉴来源

本设计吸收了以下工程实践：
- 仓库内 `test-lifecycle` 的阶段化思路
- `test-driven-development` 的最小 Red/Green/Refactor 纪律
- `subagent-driven-development` 的任务边界与双重复核思想
- 外部 `superpowers` 集合中“先计划、后并行、强测试门禁”的经验

## 资产落地范围

本次初始化新增以下资产：
- 项目目录 `family_health_record_app/`
- 项目规格文档集 `family_health_record_app/docs/specs/`
- 工作流文档 `.agents/workflows/health-record-app-delivery.md`
- 用户指南 `docs/user_guides/health_record_app_delivery_guide.md`

## 后续建议

下一阶段应先基于当前规格文档补齐两项内容，再进入真实编码：

1. 细化数据库表设计
2. 细化前端低保真线框与页面流程图
