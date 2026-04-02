# 家庭检查单管理应用数据库设计 (Database Schema)

> **版本**: v1.2.0
> **最后更新**: 2026-04-03
> **变更说明**: 添加 vision-dashboard 和 growth-dashboard API 的增长率计算逻辑

## 1. 设计目标

支撑"家庭成员多类型管理"与"OCR-审核-入库"完整生命周期，遵循 PRD 与 ARCHITECTURE 中定义的四层数据架构：
- **原始资料层** (Raw Data Layer)：管理成员与检查单原件/脱敏件。
- **OCR 中间层** (OCR Intermediate Layer)：暂存大模型抽取结果与审核过程，严格隔离业务趋势计算。
- **正式指标层** (Formal Observation Layer)：经规则引擎与人工确认的高置信度最终单点数据。
- **派生分析层** (Derived Analysis Layer)：负责年龄特定（如儿童增长及百分位）和特定算法的复杂状态聚合并记录。

---

## 2. 原始资料层 (Raw Data Layer)

### 2.1 `member_profiles` (成员档案表)

约束：采用软删除，保留历史引用。多成员共存。内网免登录场景下无账户关联，直接管理成员。

| 字段名 | 类型 | 约束 / 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 主键 |
| `name` | VARCHAR | 成员昵称 / 姓名 |
| `gender` | VARCHAR | 枚举：`male`, `female`，部分参考带强依赖此字段 |
| `date_of_birth` | DATE | 用于结合检查时间动态计算 `baseline_age_months` |
| `member_type` | VARCHAR | 枚举：`child`, `adult`, `senior`，决定适用规则和页面展现 |
| `is_deleted` | BOOLEAN | 默认 `false`，物理软删标志 |
| `created_at` | TIMESTAMPTZ | 创建时间 |
| `updated_at` | TIMESTAMPTZ | 更新时间 |

### 2.2 `document_records` (检查单记录表)

约束：记录上传实体文件属性。状态流转的核心扭转锚点。

| 字段名 | 类型 | 约束 / 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 主键 |
| `member_id` | UUID | 外键，关联 `member_profiles.id`。索引 |
| `file_url` | VARCHAR | 原图在 MinIO 的存储路径 |
| `desensitized_url` | VARCHAR | 脱敏图路径，公有云请求及前端预览均使用此路径 |
| `status` | VARCHAR | 枚举：`uploaded`, `desensitizing`, `ocr_processing`, `rule_checking`, `pending_review`, `approved`, `ocr_failed`, `rule_conflict`, `review_rejected`, `persisted` |
| `uploaded_at` | TIMESTAMPTZ | 创建/上传时间 |
| `updated_at` | TIMESTAMPTZ | 最后状态更新时间 |

---

## 3. OCR 中间层 (OCR Intermediate Layer)

### 3.1 `ocr_extraction_results` (OCR 原始抽取表)

约束：保留每一次多模态交互原始响应及中间流转结果。**本表数据独立，作为核查快照追溯，不参与趋势计算**。

| 字段名 | 类型 | 约束 / 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 主键 |
| `document_id` | UUID | 外键，指向 `document_records.id`。唯一索引 |
| `raw_json` | JSONB | 大模型返回的未清洗 JSON 全文 |
| `processed_items` | JSONB | 本地规则引擎第一次清洗并填平后的候选结构清单 |
| `confidence_score` | FLOAT | 整体 OCR 解析置信度评分 |
| `rule_conflict_details`| JSONB | 供人工审核提示参考的规则校验不通过详情（若有，如单位不匹配） |
| `created_at` | TIMESTAMPTZ | 创建时间 |

### 3.2 `review_tasks` (审核任务追踪表)

约束：保障 PRD 中的"留存人类修改痕迹"设计。内网场景下 `reviewer_id` 可为 NULL。

| 字段名 | 类型 | 约束 / 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 主键 |
| `document_id` | UUID | 外键，指向 `document_records.id` |
| `status` | VARCHAR | 枚举：`pending`, `approved`, `rejected`, `draft` |
| `reviewer_id` | UUID | 可选，指向 `member_profiles.id`（MVP 可为 NULL） |
| `audit_trail` | JSONB | 记录"人工干预：修改了什么，修改前值与后值，及审核确认时间"的追踪链 |
| `created_at` | TIMESTAMPTZ | 任务生成时间 |
| `updated_at` | TIMESTAMPTZ | 最后修改时间 |

---

## 4. 正式指标层 (Formal Observation Layer)

### 4.1 `exam_records` (检查事件/报告头)

约束：作为各项数据的一组事件总成（一对多 `observations`）。只在 `review_tasks` 变为 `approved` 且最终 `persisted` 状态化后由系统提取生成。

| 字段名 | 类型 | 约束 / 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 主键 |
| `document_id` | UUID | 外键。关联最终核准的源 `document_records` |
| `member_id` | UUID | 外键。该报告关联的检查成员 |
| `exam_date` | DATE | 检查实际发生日期 (OCR 或人工补充修正后的真实验收系) |
| `institution_name` | VARCHAR | 检查机构名 (可为 NULL) |
| `baseline_age_months` | INTEGER | 冗余字段（由入库时的 `exam_date` 与 `date_of_birth` 动态得出），频繁用于图表参考带的性能查询 |
| `created_at` | TIMESTAMPTZ | 最终入库时间 |

### 4.2 `observations` (具体医学观察表)

约束：**图表渲染与核心业务逻辑的唯一和绝对的数据源顶点**。只由审核确认的数据生成，数据绝对可信。

| 字段名 | 类型 | 约束 / 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 主键 |
| `exam_record_id` | UUID | 外键，关联 `exam_records.id`。建立索引用于快速整单拉取 |
| `metric_code` | VARCHAR | 字典枚举项：`height`, `weight`, `glucose`, `tc`, `tg`, `hdl`, `ldl`, `axial_length`, `vision_acuity` |
| `value_numeric` | FLOAT | 标准化后的数值型结果（便于趋势折线及阈值边界判断排序比对） |
| `value_text` | VARCHAR | 原始表达文字或无法量化的符号串（如"5.0-"或某些复合表达的视力） |
| `unit` | VARCHAR | 计量单位：配合 PRD/OCR 约束要求统一后的唯一物理表达 |
| `side` | VARCHAR | 枚举：`left`, `right`，为空代表该指标对本分类不可用（如身高） |
| `is_abnormal` | BOOLEAN | 落点越界标记，入库算法判断其是否在合法参照界外的标记（布尔） |
| `reference_range`| VARCHAR | 所匹配参照范围描述字符（用于图库面板直接渲染越界提醒边界） |
| `confidence_score`| FLOAT | 此字段原始提取评分（发生过人工修补将自动锁定为 1.0 的满分状态） |

---

## 5. 派生分析层 (Derived Analysis Layer)

### 5.1 `derived_metrics` (派生/二次聚合分析表)

约束：基于"成员资料和年龄分层"（例如儿童启用的成长率公式或成人特定公式）经过后台算法提炼后的总结性分析。绝不可覆盖或写入 `observations` 混淆视听。

| 字段名 | 类型 | 约束 / 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 主键 |
| `member_id` | UUID | 外键，关联 `member_profiles.id` |
| `metric_category`| VARCHAR | 分类标示，如：`velocity_curve`(生长速度), `metabolic_risk_flag`(合并代谢异常), `reserve_estimation`(眼健康预测) |
| `value_numeric` | FLOAT | 抽提或测算后的具体分析数字反馈 (可为空) |
| `value_json` | JSONB | 高复杂度返回（特定状态机，异常警告组，包含复杂参照系说明） |
| `algorithm_version`| VARCHAR | 标记使用什么引擎算法版本出的数据结果 (如：`WHO_growth_V2`, `Metabolic_Adult_v1.0`) |
| `calculation_date`| TIMESTAMPTZ | 运算批次时间及生效时区 |

---

## 6. 核心开发约束 (Global Development Constraints)

1. **唯一事实源 (Source of Truth)**：所有应用侧（如前端呈现历史、趋势图展现、导出统计分析报表等）只能调用基于正式指标层 `exam_records/observations` 构建的 API，**绝对禁止**前端调用去直接展示 `ocr_extraction_results` 或 `document_records` 表单结构当事实来源。
2. **唯一可信溯源**：一条 `document_records` 成功通过审核后，在 `exam_records` 对应的回插约束有且唯一限定条件 (必须从 `review_tasks.audit_trail` 等链路找到最后由人或者默认通过机器的确权的证据)。
3. **安全删除**：针对 `member_profiles` 的物理层擦除在 MVP 中暂不启动。采用由 `is_deleted` 作显式过滤进行保护屏蔽。不能破坏已上云存证的 `desensitized_url` 等凭证关系。
4. **内网免登录**：本应用部署于内网环境，无需账户认证。`accounts` 表在 MVP 阶段不启用，所有接口直接操作成员数据。
