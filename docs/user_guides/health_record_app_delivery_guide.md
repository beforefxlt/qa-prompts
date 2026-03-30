# 家庭检查单管理应用交付指南

本指南说明如何使用仓库中的 AI 工作流来推进“家庭检查单管理应用”的规格设计、测试设计和后续开发。

## 适用场景

- 准备从 0 到 1 开发一个家庭健康档案类应用
- 需要把 OCR、人工审核、趋势分析和测试门禁一起设计清楚
- 计划后续用多个 Subagent 并行编码

## 推荐入口

1. 先阅读 `family_health_record_app/docs/specs/PRD.md`
2. 再阅读 `family_health_record_app/docs/specs/UI_SPEC.md`
3. 再阅读 `family_health_record_app/docs/specs/ARCHITECTURE.md`
4. 再阅读 `family_health_record_app/docs/specs/TEST_STRATEGY.md`
5. 最后执行 `.agents/workflows/health-record-app-delivery.md`

## 标准推进顺序

### 1. 规格冻结

先冻结产品范围、UI、架构、OCR Schema 和测试策略，再进入编码。

### 2. 计划拆解

将任务拆成多个小任务，并为每个任务明确：
- 目标
- 输入文档
- 输出文件
- 测试入口
- 禁止改动边界

### 3. TDD 编码

每个模块先写失败测试，再补实现，避免“功能做完再补测”。

### 4. Subagent 并行

建议将项目拆为 `UI / API / OCR / Data / QA` 五类写域，避免多个代理同时修改同一核心文件。

### 5. 集成回归

必须统一执行：
- 单元测试
- OCR Golden Set 回归
- API 合约测试
- 前端 E2E
- 隐私与异常链路检查

## 特别提醒

- UI 设计不后置，应在规格阶段完成信息架构与低保真稿
- OCR 输出不能直接入正式指标表
- 文档、测试和架构说明应与代码同步演进
