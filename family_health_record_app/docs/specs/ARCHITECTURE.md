# 家庭检查单管理应用架构说明

## 1. 总体架构

采用模块化单体架构：
- 前端：`Next.js App Router`
- 后端：`FastAPI`
- 数据库：`SQLite`（开发环境）/ `PostgreSQL`（生产环境）
- 对象存储：`MinIO`
- 异步任务：`Redis + Celery`（规划中）

## 2. 核心模块

### 2.1 前端模块

- 档案与检查单管理
- 上传与处理状态展示
- OCR 审核工作台
- 趋势分析与图表展示

### 2.2 后端模块

- 成员档案服务（CRUD + 软删除）
- 文件上传服务
- 图像脱敏服务
- OCR 编排服务
- 规则引擎服务
- 审核与入库服务
- 趋势分析服务

## 3. OCR 处理链路

1. 原始文件上传到 MinIO
2. 后台任务在私有服务内执行脱敏处理
3. 生成 `ocr_safe_image`
4. 调用 SiliconFlow API + Qwen/Qwen3-VL-30B-A3B-Instruct 模型进行候选结构化抽取
5. 对返回 JSON 执行本地规则校验
6. 写入原始抽取结果表
7. 通过审核后写入正式 observation 表

## 4. 数据模型要点

详细字段设计见 `DATABASE_SCHEMA.md`。本文件只保留架构层面的实体边界与约束原则。

核心实体：
- `member_profile`
- `document_record`
- `exam_record`
- `observation`
- `derived_metric`
- `ocr_extraction_result`

关键字段要求：
- `member_profile.member_type`
- `exam_record.baseline_age_months`
- `observation.side`
- `observation.unit`
- `observation.confidence_score`
- `derived_metric.algorithm_version`

## 5. 安全与隐私

- 内网免登录部署，无需认证中间件
- 公有云只接收脱敏图，不接收原图
- 脱敏默认在后端私有服务内完成
- 正式指标入库前必须经过规则校验与人工审核
- 原始抽取结果与正式 observation 表严格分层
- OCR 样本与测试夹具必须匿名化

## 6. 计算与分析边界

### 6.1 原始值
- 身高、体重、血糖、TC、TG、HDL、LDL、视力、眼轴

### 6.2 派生值（已实现）
- 眼轴增长率（growth_rate）：基于首次和末次检查的平均值计算年增长率
- 身高/体重年增长速度（growth_rate）：同上逻辑
- 两次检查差值（comparison）：
  - 趋势 API：展示同侧或首值的前后差
  - vision-dashboard API：按左右眼分组（`left`/`right`），每组包含 `current`、`previous`、`delta`

### 6.3 计算规则
- 年增长率：需至少2组不同日期的数据才能计算，否则返回 null
- 两次差值：需至少2组不同日期的数据，优先匹配相同 side，无则使用首值
- 所有增长率和差值均为真实计算结果，前端不再硬编码默认值

说明：
- 派生值统一作为后台算法结果管理，根据成员资料中的年龄自动选择计算逻辑，不与原始医学值混淆
