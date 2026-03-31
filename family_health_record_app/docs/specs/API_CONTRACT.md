# 家庭检查单管理应用 API 契约

> **版本**: v1.1.0
> **最后更新**: 2026-03-31
> **变更说明**: 移除认证相关接口（内网免登录），补充成员管理 CRUD 接口

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
  "is_deleted": false,
  "created_at": "2026-03-30T10:00:00Z",
  "updated_at": "2026-03-30T10:00:00Z"
}
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
      "metric_code": "glucose",
      "value_numeric": 5.6,
      "unit": "mmol/L"
    }
  ]
}
```

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
    "current": 24.35,
    "previous": 24.12,
    "delta": 0.23
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
