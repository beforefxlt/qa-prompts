# 家庭检查单管理应用

> 面向家庭场景的全员健康检查单管理与趋势分析应用，聚焦上传检查单、OCR 结构化、人工审核、指标趋势图与风险提示。

## 当前阶段

已完成移动端 App 开发、QA Pipeline 用例筛选功能、E2E 测试标签标注。

已落地的内容：
- 项目目录骨架
- 产品、UI、架构、数据库、API、OCR、测试策略规格文档
- 面向 AI 开发的实施计划
- OCR Golden Set 与测试资产目录
- **前端 Next.js 15 玻璃拟态界面、降级容灾逻辑与手动录入组件**
- **后端 FastAPI + SQLite/PostgreSQL 异步架构实现与指标 CRUD 接口**
- **手动录入功能：支持动态指标添加、常规合理性校验与级联物理删除**
- **Python 基础规则引擎与图片隐私脱敏机制**
- **Docker Compose 私有化部署编排（PostgreSQL + MinIO + Backend + Frontend）**
- **契约对齐：API_CONTRACT.md 补充数值区间约束、revised_items 格式规范**
- **移动端 App：React Native + Expo，10 页面 + 351 UT**
- **QA Pipeline：支持 --tags/--spec/--exclude 用例筛选**
- **E2E 测试：7 个测试文件，标注 critical/smoke/regression 标签**
- **ESLint + Prettier：移动端代码规范检查**

尚未启动的内容：
- 组件测试（React Native Testing Library）- 因环境冲突暂跳过
- 并发上传去重（内网场景暂不处理）

## 推荐开发顺序

1. 先阅读 `docs/specs/PRD.md`
2. 再阅读 `docs/specs/UI_SPEC.md`
3. 再阅读 `docs/specs/ARCHITECTURE.md`
4. 再阅读 `docs/specs/DATABASE_SCHEMA.md`
5. 再阅读 `docs/specs/API_CONTRACT.md` ⚠️ **前后端开发必读**
6. 再阅读 `docs/specs/TEST_STRATEGY.md`
7. 最后执行 `docs/specs/IMPLEMENTATION_PLAN.md`

## 目录

```text
family_health_record_app/
├── README.md
├── backend/                    # FastAPI 服务与 OCR/规则引擎实现入口
├── frontend/                   # Next.js 15 App Router 实现 (v2.0.0 路由解耦)
│   ├── src/app/
│   │   ├── members/            # [NEW] 路由解耦层 (new/edit/trends/records)
│   │   └── api/client.ts       # 19 个业务接口实现
│   └── src/components/         # 核心组件 (TrendChart/MemberForm/UploadOverlay)
│   └── e2e/                    # Playwright E2E 测试 (7 个文件)
├── mobile_app/                 # React Native + Expo 移动端应用
│   ├── src/app/                # 10 个页面
│   └── src/__tests__/          # 351 个单元测试
├── infra/                      # Docker Compose 与部署编排
├── scripts/                    # QA Pipeline 与构建脚本
└── docs/
    ├── BUG_LOG.md              # [SSOT] 53 个缺陷根因分析（含 5-Why 分析）
    ├── QA_PIPELINE_GUIDE.md    # QA Pipeline 用例筛选使用指南
    └── specs/                  # 规格文档 (含移动端规格)
```

## 部署脚本（CI/CD 入口）

> ⚠️ **重要**：部署脚本位于 `scripts/build_docker.py`（本目录下），用于完整构建 Docker 镜像并重新部署。

```bash
# 进入项目目录
cd family_health_record_app

# 完整构建所有镜像（前端 + 后端）
python scripts/build_docker.py --all

# 仅构建后端
python scripts/build_docker.py --backend

# 仅构建前端
python scripts/build_docker.py --frontend

# 构建完成后启动服务
cd infra && docker compose up -d
```

详细部署说明请参考 [`DEPLOY.md`](./DEPLOY.md)。

## 快速启动（Docker Compose）

```bash
# 启动全部服务（db + minio + backend + frontend）
cd infra && docker compose up -d

# 访问地址
# 前端: http://localhost:3001
# 后端 API: http://localhost:8000
# 后端文档: http://localhost:8000/docs
# MinIO 控制台: http://localhost:9001
```

## 技术基线

- 前端：`Next.js App Router + TypeScript + Recharts`
- 后端：`FastAPI + Pydantic + SQLAlchemy + PostgreSQL`
- 存储：`PostgreSQL + MinIO`
- OCR：`多模态大模型 + 本地脱敏 + 规则引擎`
- 部署：`Docker Compose`

## 开发原则

- 所有人类可读文档统一使用中文
- 大模型只做候选抽取，不直接写入正式指标表
- 所有 OCR 结果必须经过规则校验与人工审核
- 先写测试与样本，再进入实现
- 多 Subagent 并行时必须严格拆分文件写域
- **前后端契约优先：修改校验规则必须同步更新 API_CONTRACT.md**

## QA Pipeline

支持用例分类筛选的测试流水线：

```bash
# 全量测试
python scripts/qa_pipeline.py --mode docker

# 仅跑 E2E 核心链路
python scripts/qa_pipeline.py --mode e2e --tags critical

# 仅跑冒烟测试
python scripts/qa_pipeline.py --mode e2e --tags smoke

# 仅跑 UT
python scripts/qa_pipeline.py --mode local --no-ut

# 排除 UX 测试
python scripts/qa_pipeline.py --mode e2e --exclude "ux"
```

详细说明参考 [`docs/QA_PIPELINE_GUIDE.md`](./docs/QA_PIPELINE_GUIDE.md)
