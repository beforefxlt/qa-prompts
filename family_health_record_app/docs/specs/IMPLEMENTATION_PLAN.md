# 家庭检查单管理应用 - AI 交付实施计划 (Step 5 - 正式版)

> **版本**: v1.3.0
> **最后更新**: 2026-03-31
> **基线依赖**: ARCHITECTURE.md, DATABASE_SCHEMA.md, PRD.md, API_CONTRACT.md, UI_SPEC.md
> **变更说明**: 移除认证模块，补充空状态引导、成员管理 CRUD、OCR 审核页实现

本计划旨在修正前期技术栈偏差，将后端从 Node.js+SQLite 迁移至 FastAPI+PostgreSQL 生产级架构，并对齐内网免登录场景。

---

## 实施拆解清单

### Task 0: 废弃代码清理与环境初始化 (1h)
* **任务目标**：彻底清理之前的 Node.js 后端草案，防止代码混淆。初始化 FastAPI 项目结构。
* **输入规格**：ARCHITECTURE.md (Section 1)
* **输出文件**：
  * `backend/` (项目根目录)
  * `backend/pyproject.toml` 或 `requirements.txt`
  * `backend/app/main.py`
  * 删除 `family_health_record_app/src/` (之前废弃的 Node.js 代码)
* **禁止修改范围**：`frontend/` 目录。
* **测试方式**：uvicorn 启动服务并访问 /docs 成功。

### Task 0.5: 数据库模型与迁移 (2h)
* **任务目标**：根据 DATABASE_SCHEMA.md 构建核心表模型（移除 accounts 表依赖），配置 Alembic 迁移脚本。
* **输入规格**：DATABASE_SCHEMA.md (v1.1.0)
* **输出文件**：
  * `backend/app/models/member.py` (member_profiles)
  * `backend/app/models/document.py` (document_records, ocr_extraction_results, review_tasks)
  * `backend/app/models/observation.py` (exam_records, observations, derived_metrics)
  * `backend/app/db.py`
* **禁止修改范围**：API 接口层。
* **测试方式**：pytest 单元测试，验证 member_profiles 软删除逻辑及 observations 与 exam_records 的一对多约束。

### Task 1: 成员档案服务 (CRUD) (2h)
* **任务目标**：实现成员档案的创建、查询、更新、软删除接口。
* **输入规格**：API_CONTRACT.md §2.1 + UI_SPEC.md §3.2, §3.3
* **输出文件**：
  * `backend/app/routers/members.py`
  * `backend/app/schemas/member.py` (Pydantic 模型)
* **禁止修改范围**：文件存储逻辑、OCR 管线。
* **测试方式**：
  * API 合约测试：创建成员 → 查询列表 → 更新信息 → 软删除 → 验证列表不再返回
  * 边界测试：空姓名、非法日期、错误 member_type 枚举值

### Task 2: 后端图像处理服务 (Pillow + OpenCV) (3h)
* **任务目标**：将之前的 image_masker.ts 迁移至 Python，使用 Pillow 实现敏感信息区域（页头 15%、页脚 10% 等）遮罩，并上传至 MinIO。
* **输入规格**：PRD.md (隐私约束) + ARCHITECTURE.md (OCR 链路)
* **输出文件**：
  * `backend/app/services/image_processor.py`
  * `backend/app/services/storage_client.py`
* **禁止修改范围**：数据库模型层。
* **测试方式**：测试脚本读取一张样图，输出脱敏后的 .webp，验证敏感区域已涂黑。

### Task 3: OCR 编排与规则引擎服务 (4h)
* **任务目标**：集成公有云多模态模型 API。实现 Python 版本的规则引擎，支持单位换算、超限预警、左右眼逻辑校验与状态机流转。
* **输入规格**：PRD.md (5.1-5.3 章节) + API_CONTRACT.md + OCR_SCHEMA.md
* **输出文件**：
  * `backend/app/services/ocr_orchestrator.py`
  * `backend/app/services/rule_engine.py` (含指标字典与单位换算)
* **禁止修改范围**：文件存储逻辑。
* **测试方式**：Mock OCR 返回异常数据（如血糖 99.0 mmol/L），断言 document_records.status 变更为 rule_conflict 并生成 review_task。

### Task 4: 审核与入库服务 (3h)
* **任务目标**：实现 OCR 审核工作台的后端接口，支持审核通过、退回、保存草稿，以及最终入库逻辑。
* **输入规格**：API_CONTRACT.md §2.4 + PRD.md §5.3
* **输出文件**：
  * `backend/app/routers/review.py`
  * `backend/app/schemas/review.py`
* **禁止修改范围**：OCR 管线核心逻辑。
* **测试方式**：
  * 审核通过 → 验证 observations 表写入 + audit_trail 记录
  * 退回重识别 → 验证状态变更为 review_rejected
  * 保存草稿 → 验证 review_tasks 状态为 draft

### Task 5: 趋势分析服务 (2h)
* **任务目标**：实现趋势查询接口，支持指标切换、时间范围切换、参考区间与报警状态返回。
* **输入规格**：API_CONTRACT.md §2.5 + PRD.md §6.1
* **输出文件**：
  * `backend/app/routers/trends.py`
  * `backend/app/services/trend_aggregator.py`
* **禁止修改范围**：OCR 管线、审核服务。
* **测试方式**：
  * 查询空数据 → 返回空 series
  * 查询有数据 → 验证 series 按日期排序、reference_range 正确、alert_status 正确
  * 切换时间范围 → 验证数据切片正确

### Task 6: 前后端集成与 API 适配 (5h)
* **任务目标**：对接 FastAPI 后端接口。保留现有 Next.js 15 UI，修改前端 API 调用层。完成审核台 UI 与后端状态机的闭环交互。
* **输入规格**：API_CONTRACT.md + UI_SPEC.md
* **输出文件**：
  * `frontend/src/api/client.ts` (完整重写，覆盖所有资源)
  * `frontend/src/hooks/useMetrics.ts`
  * `frontend/src/app/` 页面组件更新（空状态引导、成员管理、审核页）
* **禁止修改范围**：底层核心业务算法逻辑。
* **测试方式**：Playwright E2E 测试，模拟完整上传、自动 OCR、发现异常、进入审核台并成功保存的过程。

### Task 7: 真实样本全链路大考 (Golden Set) (2h)
* **任务目标**：使用真实 Lenstar 眼轴报告 (tests/01.jpg) 进行端到端验证，核实眼轴 (24.35mm/23.32mm) 的准确落库情况。
* **输入规格**：TEST_STRATEGY.md
* **输出文件**：
  * `backend/tests/integration/test_golden_set.py`
* **测试方式**：验证不仅数值正确落入 observations，且 derived_metrics 中正确计算了眼轴增长偏差（参考同龄人）。

### Task 8: 空状态与首次使用引导 (2h)
* **任务目标**：实现前端空状态引导页，确保首次用户能顺利完成"创建成员 → 开始使用"流程。
* **输入规格**：UI_SPEC.md §3.0 + PRD.md §5.0
* **输出文件**：
  * `frontend/src/app/page.tsx` (首页空状态逻辑)
  * `frontend/src/app/members/new/page.tsx` (成员创建页)
* **测试方式**：
  * E2E 测试：打开首页 → 看到空状态 → 点击添加成员 → 填写表单 → 保存 → 返回首页看到成员卡片
  * 边界测试：不填必填字段 → 提交拦截
