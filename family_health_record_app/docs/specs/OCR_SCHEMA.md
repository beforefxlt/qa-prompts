# OCR 结构化抽取规格

## 1. 目标

定义公有云多模态模型的候选输出结构，并为本地规则引擎提供统一输入。

## 2. 文档分类

- `vision_exam`
- `growth_exam`
- `metabolic_exam`
- `unknown`

## 3. 通用字段

- `document_type`
- `exam_date`
- `institution_name`
- `patient_age_text`
- `confidence_score`
- `items`

## 4. 指标项结构

每个 `item` 至少包含：
- `metric_code`
- `label`
- `value_text`
- `value_numeric`
- `unit`
- `side`
- `reference_range_text`
- `confidence_score`

## 5. 规则引擎校验要求

- 眼轴必须使用 `mm`
- 血糖必须使用 `mmol/L`
- `TC/TG/HDL/LDL` 必须使用 `mmol/L`
- 身高必须使用 `cm`
- 体重必须使用 `kg`
- 左右眼字段不可同时为空（视力类检查）
- 必须根据 `patient_age_text` 与成员档案信息动态匹配参考值区间，不匹配时必须提示审核
- 同一检查单中同一指标不可出现重复冲突值
- 置信度低于系统阈值时不得直接进入正式指标表

## 6. 入库原则

- OCR 输出先写入原始结果表
- 规则校验失败时不得写入正式指标表
- 低置信度、单位不匹配、字段缺失、左右眼串位必须转为人工审核
