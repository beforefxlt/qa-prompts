# 家庭检查单管理应用

> 面向家庭场景的全员健康检查单管理与趋势分析应用，聚焦上传检查单、OCR 结构化、人工审核、指标趋势图与风险提示。

## 当前阶段

当前目录完成了项目初始化与规格沉淀，目标是为后续 AI 驱动开发提供稳定入口。

已落地的内容：
- 项目目录骨架
- 产品、UI、架构、数据库、API、OCR、测试策略规格文档
- 面向 AI 开发的实施计划
- OCR Golden Set 与测试资产目录
- **前端 Next.js 15 玻璃拟态界面与降级容灾逻辑**
- **后端 FastAPI + PostgreSQL 四层六表架构实现**
- **Python 基础规则引擎与图片隐私脱敏机制**

尚未启动的内容：
- 自动化测试脚本补充
- Docker 私有化部署脚本

## 推荐开发顺序

1. 先阅读 `docs/specs/PRD.md`
2. 再阅读 `docs/specs/UI_SPEC.md`
3. 再阅读 `docs/specs/ARCHITECTURE.md`
4. 再阅读 `docs/specs/DATABASE_SCHEMA.md`
5. 再阅读 `docs/specs/TEST_STRATEGY.md`
6. 最后执行 `docs/specs/IMPLEMENTATION_PLAN.md`

## 目录

```text
family_health_record_app/
├── README.md
├── backend/                    # FastAPI 服务与 OCR/规则引擎实现入口
├── frontend/                   # Next.js 前端与图表交互实现入口
├── infra/                      # Docker Compose 与部署编排
├── tests/                      # 跨层测试资产说明
├── datasets/
│   └── ocr_golden_set/         # OCR 回归样本集说明
└── docs/
    └── specs/
        ├── PRD.md
        ├── UI_SPEC.md
        ├── ARCHITECTURE.md
        ├── DATABASE_SCHEMA.md
        ├── API_CONTRACT.md
        ├── OCR_SCHEMA.md
        ├── TEST_STRATEGY.md
        └── IMPLEMENTATION_PLAN.md
```

## 技术基线

- 前端：`Next.js App Router + TypeScript + Apache ECharts`
- 后端：`FastAPI + Pydantic`
- 存储：`PostgreSQL + MinIO`
- 队列：`Redis + Celery`
- OCR：`多模态大模型 + 本地脱敏 + 规则引擎`
- 部署：`Docker Compose`

## 开发原则

- 所有人类可读文档统一使用中文
- 大模型只做候选抽取，不直接写入正式指标表
- 所有 OCR 结果必须经过规则校验与人工审核
- 先写测试与样本，再进入实现
- 多 Subagent 并行时必须严格拆分文件写域
