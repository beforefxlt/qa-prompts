# OCR 结构化抽取规格

> **版本**: v2.2.0
> **最后更新**: 2026-04-03
> **变更说明**: OCR 模型升级为 Qwen/Qwen3-VL-30B-A3B-Instruct，移除代理配置

## 1. 目标

定义公有云多模态模型的候选输出结构，并为本地规则引擎提供统一输入。

## 2. 文档分类

- `vision_exam`: 视力/眼轴类检查单（儿童）
- `growth_exam`: 生长发育类检查单（身高/体重，儿童）
- `metabolic_exam`: 代谢类检查单（血糖/血脂，成人/老人）
- `unknown`: 无法识别的检查单类型

## 3. 通用字段

OCR 返回的 JSON 必须包含以下通用字段：

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| `document_type` | string | 文档分类枚举值 |
| `exam_date` | string | 检查日期，ISO 8601 格式 (YYYY-MM-DD) |
| `institution_name` | string | 检查机构名称（可为空） |
| `patient_age_text` | string | 检查单上原始年龄描述（如"8岁6月"） |
| `confidence_score` | float | 整体置信度评分 (0.0-1.0) |
| `items` | array | 指标项列表 |

## 4. 指标项结构

每个 `item` 至少包含：

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| `metric_code` | string | 指标字典码（如 `axial_length`, `glucose`） |
| `label` | string | 检查单上的原始标签文字 |
| `value_text` | string | 原始表达文字（如"5.0-"、">10"） |
| `value_numeric` | float | 标准化后的数值（可为空） |
| `unit` | string | 计量单位 |
| `side` | string | 枚举：`left`, `right`, `null`（非眼部指标为空） |
| `reference_range_text` | string | 检查单上印刷的参考范围（可为空） |
| `confidence_score` | float | 该单项的置信度评分 |

## 5. 规则引擎校验要求

### 5.1 单位校验

| 指标 | 必须使用的单位 | 错误示例 |
|:---|:---|:---|
| 眼轴 | `mm` | cm, μm |
| 血糖 | `mmol/L` | mg/dL |
| TC/TG/HDL/LDL | `mmol/L` | mg/dL |
| 血红蛋白 | `g/L` | g/dL, g% |
| 糖化血红蛋白 | `%` | mmol/mol |
| 身高 | `cm` | m, inch |
| 体重 | `kg` | g, lb |

### 5.2 字段完整性校验

- 眼轴/视力类检查：左右眼字段不可同时为空
- 所有检查：检查日期不可缺失或无法解析
- 所有检查：至少包含 1 个有效指标项

### 5.3 逻辑校验

- 根据 `patient_age_text` 与成员档案信息动态匹配参考值区间，不匹配时必须提示审核
- 同一检查单中同一指标不可出现重复冲突值
- 眼轴数值必须在合理范围内 (18mm-30mm)，超出范围标记为异常
- 血糖数值必须在合理范围内 (1.0-35.0 mmol/L)，超出范围标记为异常
- 血红蛋白数值必须在合理范围内 (30-250 g/L)，超出范围标记为异常
- LDL 数值必须在合理范围内 (0.1-10.0 mmol/L)，超出范围标记为异常
- HbA1c 数值必须在合理范围内 (3.0-15.0 %)，超出范围标记为异常

### 5.4 置信度阈值

- `≥ 0.8`: 高置信，可直接入库（仍需规则校验通过）
- `0.6-0.8`: 中置信，进入人工审核
- `< 0.6`: 低置信，必须进入人工审核

## 6. 入库原则

- OCR 输出先写入 `ocr_extraction_results` 原始结果表
- 规则校验失败时不得写入正式指标表 (`observations`)
- 低置信度、单位不匹配、字段缺失、左右眼串位必须转为人工审核 (`review_tasks`)
- 人工审核通过后，数据写入 `exam_records` + `observations`
- 所有人工修改必须记录在 `review_tasks.audit_trail` 中

## 7. 与审核页的交互约束

- 审核页必须展示 OCR 原始返回的 `raw_json` 与规则引擎处理后的 `processed_items`
- 冲突字段在审核页标红，并显示具体冲突原因
- 审核页允许用户修改任意字段值，修改后更新 `processed_items` 并记录到 `audit_trail`
- 审核通过后，`confidence_score` 锁定为 1.0（人工确认后的数据视为完全可信）
