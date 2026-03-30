# 家庭检查单管理应用实施计划

> **执行方式**：推荐使用 `subagent-driven-development`，按任务边界分配实现代理，并在每个任务后执行“规格一致性复核 + 代码质量复核”。

## 阶段 1：规格冻结

1. 复核 `PRD.md`
2. 复核 `UI_SPEC.md`
3. 复核 `ARCHITECTURE.md`
4. 复核 `API_CONTRACT.md`
5. 复核 `OCR_SCHEMA.md`
6. 复核 `TEST_STRATEGY.md`

## 阶段 2：开发准备

1. 初始化前后端工程
2. 建立 Docker Compose 运行环境
3. 建立 PostgreSQL 与 MinIO 本地开发依赖
4. 建立测试框架
5. 建立 OCR Golden Set 样本规范

## 阶段 3：按域拆解 Subagent

- `Agent-UI`：前端页面、组件、图表、审核工作台
- `Agent-API`：档案、上传、审核、趋势接口
- `Agent-OCR`：脱敏、OCR 编排、规则引擎
- `Agent-Data`：数据库 Schema、派生指标、趋势分析
- `Agent-QA`：测试脚手架、Golden Set、E2E、门禁

## 阶段 4：TDD 实施原则

每个任务必须遵循：
1. 先写最小失败测试
2. 运行确认失败
3. 写最小实现
4. 运行确认通过
5. 再做局部重构

## 阶段 5：集成与验收

1. 联调前后端接口
2. 跑单元测试与集成测试
3. 跑 OCR Golden Set 回归
4. 跑前端 E2E
5. 使用 `verify-requirements` 做需求落地核验
6. 使用 `reviewer-agent` 做最终收口复核
