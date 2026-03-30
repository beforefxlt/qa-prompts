# 家庭检查单管理应用 - AI 交付实施计划 (Step 5 - 正式版)

> **版本**: v1.2.0
> **最后更新**: 2026-03-30
> **基线依赖**: ARCHITECTURE.md, DATABASE_SCHEMA.md, PRD.md, API_CONTRACT.md

本计划旨在修正前期技术栈偏差，将后端从 Node.js+SQLite 迁移至 FastAPI+PostgreSQL 生产级架构。

---

## 🏗️ 实施拆解清单

### Task 0: 废弃代码清理与环境初始化 (1h)
* **任务目标**：彻底清理之前的 Node.js 后端草案，防止代码混淆。初始化 FastAPI 项目结构。
* **输入规格**：ARCHITECTURE.md (Section 1)
* **输出文件**：
  * ackend/ (项目根目录)
  * ackend/pyproject.toml 或 equirements.txt
  * ackend/app/main.py
  * 删除 amily_health_record_app/src/ (之前废弃的 Node.js 代码)
* **禁止修改范围**：rontend/ 目录。
* **测试方式**：uvicorn 启动服务并访问 /docs 成功。

### Task 1: 核心数据持久层实现 (FastAPI + SQLAlchemy) (4h)
* **任务目标**：根据 DATABASE_SCHEMA.md 构建 6 张核心表模型，并配置 Alembic 迁移脚本。
* **输入规格**：DATABASE_SCHEMA.md (全结构)
* **输出文件**：
  * ackend/app/models/member.py (ccounts, member_profiles)
  * ackend/app/models/document.py (document_records, ocr_extraction_results, eview_tasks)
  * ackend/app/models/observation.py (exam_records, observations, derived_metrics)
  * ackend/app/db.py
* **禁止修改范围**：API 接口层。
* **测试方式**：pytest 单元测试，验证 member_profiles 软删除逻辑及 observations 与 exam_records 的一对多约束。

### Task 2: 后端图像处理服务 (Pillow + OpenCV) (3h)
* **任务目标**：将之前的 image_masker.ts 迁移至 Python，使用 Pillow 实现敏感信息区域（页头 15%、页脚 10% 等）遮罩，并上传至 MinIO。
* **输入规格**：PRD.md (隐私约束) + ARCHITECTURE.md (OCR 链路)
* **输出文件**：
  * ackend/app/services/image_processor.py
  * ackend/app/services/storage_client.py
* **禁止修改范围**：数据库模型层。
* **测试方式**：测试脚本读取一张样图，输出脱敏后的 .webp，验证敏感区域已涂黑。

### Task 3: OCR 编排与规则引擎服务 (4h)
* **任务目标**：集成公有云多模态模型 API。实现 Python 版本的规则引擎，支持单位换算、超限预警、左右眼逻辑校验与状态机流转。
* **输入规格**：PRD.md (5.1-5.2 章节) + API_CONTRACT.md
* **输出文件**：
  * ackend/app/services/ocr_orchestrator.py
  * ackend/app/services/rule_engine.py (含指标字典与单位换算)
* **禁止修改范围**：文件存储逻辑。
* **测试方式**：Mock OCR 返回异常数据（如血糖 99.0 mmol/L），断言 document_records.status 变更为 ule_conflict 并生成 eview_task。

### Task 4: 前后端集成与 API 适配 (5h)
* **任务目标**：对接 FastAPI 后端接口。保留现有 Next.js 15 UI，修改前端 API 调用层。完成审核台 UI 与后端状态机的闭环交互。
* **输入规格**：API_CONTRACT.md + Task 4 (UI_SPEC.md)
* **输出文件**：
  * rontend/src/api/client.ts
  * rontend/src/hooks/useMetrics.ts
  * ackend/app/routers/ (API 控制器)
* **禁止修改范围**：底层核心业务算法逻辑。
* **测试方式**：Playwright E2E 测试，模拟完整上传、自动 OCR、发现异常、进入审核台并成功保存的过程。

### Task 5: 真实样本全链路大考 (Golden Set) (2h)
* **任务目标**：使用真实 Lenstar 眼轴报告 (	ests/01.jpg) 进行端到端验证，核实眼轴 (24.35mm/23.32mm) 的准确落库情况。
* **输入规格**：TEST_STRATEGY.md (TC-P5-01)
* **输出文件**：
  * ackend/tests/integration/test_golden_set.py
* **测试方式**：验证不仅数值正确落入 observations，且 derived_metrics 中正确计算了眼轴增长偏差（参考同龄人）。
