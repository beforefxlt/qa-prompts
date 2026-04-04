# 家庭检查单管理应用 API 契约

> **版本**: v2.4.0
> **最后更新**: 2026-04-04
> **变更说明**: 补充完整数值区间约束表，对齐前端 METRIC_OPTIONS

## 1. 资源对象

- `MemberProfile`
- `DocumentRecord`
- `ExamRecord`
- `Observation`
- `ReviewTask`
- `TrendSeries`

## 2. 核心接口

### 2.1 成员档案

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| `GET` | `/api/v1/members` | 获取所有成员列表（过滤已软删除） |
| `POST` | `/api/v1/members` | 创建新成员档案 |
| `GET` | `/api/v1/members/{member_id}` | 获取单个成员详情 |
| `PUT` | `/api/v1/members/{member_id}` | 更新成员档案 |
| `DELETE` | `/api/v1/members/{member_id}` | 软删除成员（is_deleted=true） |

**请求体 - 创建成员**:
```json
{
  "name": "晓萌",
  "gender": "female",
  "date_of_birth": "2018-06-15",
  "member_type": "child"
}
```

**响应体 - 成员对象**:
```json
{
  "id": "uuid",
  "name": "晓萌",
  "gender": "female",
  "date_of_birth": "2018-06-15",
  "member_type": "child",
  "last_check_date": "2026-03-29",
  "pending_review_count": 1
}
```

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| `id` | UUID | 成员唯一标识 |
| `name` | string | 成员姓名 |
| `gender` | string | 性别（male/female） |
| `date_of_birth` | date | 出生日期 |
| `member_type` | string | 成员类型（child/adult/senior） |
| `last_check_date` | string\|null | 最近一次检查日期（ExamRecord.exam_date），无检查记录时为 null |
| `pending_review_count` | int | 待审核检查单数量（ReviewTask.status='pending'），默认 0 |

> **说明**: `GET /members` 列表接口返回的 `last_check_date` 和 `pending_review_count` 由后端实时计算，前端直接展示。`GET /members/{member_id}` 单条接口不返回这两个字段。
```

### 2.2 检查单上传

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| `POST` | `/api/v1/documents/upload` | 上传检查单文件（multipart/form-data） |
| `GET` | `/api/v1/documents/{document_id}` | 获取检查单记录详情 |

**请求体 - 上传**:
- Content-Type: `multipart/form-data`
- 字段: `file` (文件), `member_id` (UUID)

**响应体 - 上传成功**:
```json
{
  "document_id": "uuid",
  "status": "uploaded",
  "file_url": "minio://...",
  "desensitized_url": "minio://..."
}
```

### 2.3 OCR 处理

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| `POST` | `/api/v1/documents/{document_id}/submit-ocr` | 触发 OCR 识别与规则校验管线 |

**响应体**:
```json
{
  "document_id": "uuid",
  "status": "persisted | rule_conflict | ocr_failed"
}
```

### 2.4 OCR 审核

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| `GET` | `/api/v1/review-tasks` | 获取待审核任务列表 |
| `GET` | `/api/v1/review-tasks/{task_id}` | 获取审核任务详情（含 OCR 原始结果） |
| `POST` | `/api/v1/review-tasks/{task_id}/approve` | 审核通过，写入正式指标表 |
| `POST` | `/api/v1/review-tasks/{task_id}/reject` | 退回重识别 |
| `POST` | `/api/v1/review-tasks/{task_id}/save-draft` | 保存草稿 |

**请求体 - 审核通过/保存草稿**:
```json
{
  "revised_items": [
    {
      "metric_code": "exam_date",
      "value": "2026-04-01"
    },
    {
      "metric_code": "axial_length",
      "side": "left",
      "value_numeric": 23.55,
      "unit": "mm"
    },
    {
      "metric_code": "axial_length",
      "side": "right",
      "value_numeric": 23.20,
      "unit": "mm"
    }
  ]
}
```

> **⚠️ revised_items 格式规范（前端必须遵守）**：
> 
> 1. **`exam_date` 修改**：使用 `{ "metric_code": "exam_date", "value": "YYYY-MM-DD" }` 格式
> 2. **Observation 数值修改**：必须包含 `metric_code` + `side` 来匹配目标记录，用 `value_numeric` 传递新数值
> 3. **数值类型**：`value_numeric` 必须是 **number 类型**（如 `23.5`），不能是字符串 `"23.5"`
> 4. **禁止格式**：不能发送 `{ "field": "xxx", "value": "yyy" }` — 后端不识别 `field` 字段
> 5. **禁止格式**：不能将整个 `observations` 数组作为一个条目发送 — 必须拆分为独立条目
> 
> **后端匹配逻辑**：遍历 `revised_items`，用 `metric_code` + `side` 在 `ocr_processed_items.observations` 数组中查找匹配项，然后更新 `value_numeric`。

### 2.5 趋势查询

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| `GET` | `/api/v1/members/{member_id}/trends?metric={metric}&range={range}` | 获取指标趋势数据 |
| `GET` | `/api/v1/members/{member_id}/vision-dashboard?range={range}` | 获取视力/眼轴仪表盘数据 |
| `GET` | `/api/v1/members/{member_id}/growth-dashboard?range={range}` | 获取生长发育仪表盘数据 |

**响应体 - 趋势查询**:
```json
{
  "metric": "axial_length",
  "series": [
    { "date": "2026-03-01", "value": 24.12, "side": "left" },
    { "date": "2026-03-01", "value": 23.15, "side": "right" }
  ],
  "reference_range": "23.0-24.0",
  "alert_status": "normal | warning | critical",
  "comparison": {
    "left": { "current": 23.60, "previous": 23.32, "delta": 0.28 },
    "right": { "current": 23.32, "previous": 23.20, "delta": 0.12 }
  }
}
```

### 2.6 数据管理与手动录入 (CRUD)

系统支持对已入库的正式指标进行增删改查。

#### POST /members/{id}/manual-exams
手动录入一次完整的检查记录。

- **Request**:
```json
{
  "exam_date": "2026-04-01",
  "institution_name": "社区卫生服务中心",
  "observations": [
    {
      "metric_code": "height",
      "value_numeric": 125.5,
      "unit": "cm",
      "side": null
    },
    {
      "metric_code": "axial_length",
      "value_numeric": 23.5,
      "unit": "mm",
      "side": "left"
    }
  ]
}
```

- **校验关键点**: `value_numeric` 必须在常规合理区间内，否则返回 `422 Unprocessable Entity`。
  各指标数值区间约束如下：

  | metric_code | 指标名称 | 单位 | 合理区间 | 后端校验位置 | 前端 min/max |
  |:---|:---|:---|:---|:---|:---|
  | `height` | 身高 | cm | 30.0 ~ 250.0 | `schemas/observation.py:validate_sanity_range` | 30 / 250 |
  | `weight` | 体重 | kg | 2.0 ~ 500.0 | `schemas/observation.py:validate_sanity_range` | 2 / 500 |
  | `axial_length` | 眼轴长度 | mm | 15.0 ~ 35.0 | `schemas/observation.py:validate_sanity_range` | 15 / 35 |
  | `vision_acuity` | 视力 | decimal | 无区间校验 | — | — |
  | `glucose` | 血糖 | mmol/L | 0.1 ~ 50.0 | `schemas/observation.py:validate_sanity_range` | 0.1 / 50.0 |
  | `ldl` | 低密度脂蛋白 | mmol/L | 0.1 ~ 10.0 | `schemas/observation.py:validate_sanity_range` | 0.1 / 10.0 |
  | `hemoglobin` | 血红蛋白 | g/L | 30.0 ~ 250.0 | `schemas/observation.py:validate_sanity_range` | 30 / 250 |
  | `hba1c` | 糖化血红蛋白 | % | 3.0 ~ 15.0 | `schemas/observation.py:validate_sanity_range` | 3.0 / 15.0 |
  | `tc` | 总胆固醇 | mmol/L | 0.1 ~ 30.0 | — | — |
  | `tg` | 甘油三酯 | mmol/L | 0.1 ~ 30.0 | — | — |
  | `hdl` | 高密度脂蛋白 | mmol/L | 0.1 ~ 10.0 | — | — |

  > **⚠️ 注意事项**：
  > - 后端 `ObservationUpdate` (PATCH /observations/{id}) 使用独立校验：`0.0 < value_numeric <= 1000.0`
  > - 部分指标（tc/tg/hdl）后端当前无校验，需补充
  > - 前端必须在提交前执行与后端相同的区间校验（见 `ManualEntryOverlay.tsx` 中的 METRIC_OPTIONS）

  > **🔄 同步要求**：当后端 Pydantic 校验规则变更时，必须同步更新：
  > 1. `API_CONTRACT.md` 本表
  > 2. `frontend/src/components/records/ManualEntryOverlay.tsx` 中的 METRIC_OPTIONS

#### PATCH /observations/{id}
修改单条指标数值。

- **Request**: `{"value_numeric": 126.0}`
- **Response**: `200 OK`

#### DELETE /exam-records/{id}
删除整笔检查记录。

- **Response**: `204 No Content`
- **级联效应**: 对应 `observations` 中的所有指标将同步被删除。

---

**响应体 - vision-dashboard**:
```json
{
  "member_id": "uuid",
  "member_type": "child",
  "baseline_age_months": "2009-10-01",
  "axial_length": {
    "series": [
      { "date": "2024-09-21", "value": 24.35, "side": "right" },
      { "date": "2024-09-21", "value": 23.32, "side": "left" }
    ],
    "reference_range": null,
    "alert_status": "normal",
    "growth_rate": -0.13,
    "comparison": {
      "left": { "current": 23.60, "previous": 23.32, "delta": 0.28 },
      "right": { "current": 23.67, "previous": 24.35, "delta": -0.68 }
    }
  },
  "vision_acuity": {
    "series": [
      { "date": "2024-09-21", "value": "0.8", "side": "left" },
      { "date": "2024-09-21", "value": "1.0", "side": "right" }
    ],
    "reference_range": "0.8-1.2",
    "alert_status": "normal",
    "comparison": {
      "left": { "current": 0.9, "previous": 0.8, "delta": 0.1 },
      "right": { "current": 1.0, "previous": 1.0, "delta": 0.0 }
    }
  },
  "growth_deviation": null
}
```

> **说明**: `axial_length.comparison` 按左右眼分组（`left`/`right`），每组包含 `current`（当前值）、`previous`（上次值）、`delta`（差值）。若某侧只有一组数据则为 `null`；若两侧均无数据则整个 `comparison` 为 `null`。

> **说明**: `vision_acuity.comparison` 结构同 `axial_length.comparison`，但 value 可能为字符串（如 "0.8"），comparison 中的值统一转为数字。

> **说明**: `growth-dashboard` 的 `height.comparison` 和 `weight.comparison` 为单维度对比结构：`{current, previous, delta}`。

---

**响应体 - growth-dashboard**:
```json
{
  "member_id": "uuid",
  "member_type": "child",
  "height": {
    "series": [
      { "date": "2025-11-06", "value": 135.0 },
      { "date": "2026-04-03", "value": 140.0 }
    ],
    "reference_range": null,
    "alert_status": "normal",
    "growth_rate": 12.0,
    "comparison": {
      "current": 140.0,
      "previous": 135.0,
      "delta": 5.0
    }
  },
  "weight": {
    "series": [...],
    "comparison": {
      "current": 35.0,
      "previous": 32.5,
      "delta": 2.5
    }
  }
}
```

## 3. 状态流转

标准流转：
`uploaded -> desensitizing -> ocr_processing -> rule_checking -> pending_review -> approved -> persisted`

异常流转：
- `ocr_failed`: OCR 接口超时或返回异常
- `rule_conflict`: 规则引擎检测到单位/阈值/字段冲突
- `review_rejected`: 人工审核退回

## 4. 错误码

| 状态码 | 说明 |
|:---|:---|
| `400` | 请求参数错误（如缺少必填字段） |
| `404` | 资源不存在（成员/检查单/审核任务） |
| `409` | 状态冲突（如对已审核记录重复提交） |
| `500` | 服务器内部错误 |

## 5. 契约约束

- 所有时间统一使用 ISO 8601
- 所有数值字段必须带单位
- 审核接口必须保留人工修改痕迹（audit_trail）
- 趋势接口返回原始值、参考区间和报警状态
- 成员对象必须返回 `member_type`
- 儿童相关接口返回 `baseline_age_months`，用于图表参考带与增长速度计算
- **本应用为内网免登录部署，所有接口无需携带认证 Token**
