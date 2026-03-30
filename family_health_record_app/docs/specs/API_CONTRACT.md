# 家庭检查单管理应用 API 契约草案

## 1. 资源对象

- `ChildProfile`
- `DocumentRecord`
- `ExamRecord`
- `Observation`
- `ReviewTask`
- `TrendSeries`

## 2. 核心接口

### 2.1 儿童档案

- `POST /api/v1/children`
- `GET /api/v1/children`
- `GET /api/v1/children/{child_id}`

### 2.2 检查单上传

- `POST /api/v1/documents/upload`
- `GET /api/v1/documents/{document_id}`
- `POST /api/v1/documents/{document_id}/submit-ocr`

### 2.3 OCR 审核

- `GET /api/v1/review-tasks`
- `GET /api/v1/review-tasks/{task_id}`
- `POST /api/v1/review-tasks/{task_id}/approve`
- `POST /api/v1/review-tasks/{task_id}/reject`
- `POST /api/v1/review-tasks/{task_id}/save-draft`

### 2.4 趋势查询

- `GET /api/v1/children/{child_id}/trends?metric=height&range=3m`
- `GET /api/v1/children/{child_id}/vision-dashboard?range=12m`
- `GET /api/v1/children/{child_id}/growth-dashboard?range=12m`

## 3. 状态流转

`uploaded -> desensitizing -> ocr_processing -> rule_checking -> pending_review -> approved -> persisted`

异常流转：

`ocr_failed`

`rule_conflict`

`review_rejected`

## 4. 契约约束

- 所有时间统一使用 ISO 8601
- 所有数值字段必须带单位
- 审核接口必须保留人工修改痕迹
- 趋势接口返回原始值、参考区间和报警状态
