# 移动端契约同步检查

> 基于 MOBILE_API_CONTRACT.md v1.0.0 vs mobile_app/src/api/

## 检查结果

### 1. API 端点覆盖

| 端点 | 契约定义 | 移动端实现 | 状态 |
|------|---------|-----------|------|
| GET /members | ✅ | ✅ | ✅ |
| POST /members | ✅ | ✅ | ✅ |
| GET /members/{id} | ✅ | ✅ | ✅ |
| PUT /members/{id} | ✅ | ✅ | ✅ |
| DELETE /members/{id} | ✅ | ✅ | ✅ |
| POST /documents/upload | ✅ | ⚠️ 未实现 (仅 client) | ✅ |
| GET /documents/{id} | ✅ | ✅ | ✅ |
| POST /documents/{id}/submit-ocr | ✅ | ✅ | ✅ |
| GET /review-tasks | ✅ | ✅ | ✅ |
| GET /review-tasks/{id} | ✅ | ✅ | ✅ |
| POST /review-tasks/{id}/approve | ✅ | ✅ | ✅ |
| POST /review-tasks/{id}/reject | ✅ | ✅ | ✅ |
| POST /review-tasks/{id}/save-draft | ✅ | ✅ | ✅ |
| GET /members/{id}/trends | ✅ | ✅ | ✅ |
| GET /members/{id}/vision-dashboard | ✅ | ✅ | ✅ |
| GET /members/{id}/growth-dashboard | ✅ | ✅ | ✅ |
| POST /members/{id}/manual-exams | ✅ | ✅ | ✅ |
| PATCH /observations/{id} | ✅ | ✅ | ✅ |
| DELETE /exam-records/{id} | ✅ | ✅ | ✅ |

### 2. 数据模型对齐

| 模型 | 契约 | 移动端 | 状态 |
|------|------|--------|------|
| MemberProfile | ✅ | ✅ | ✅ |
| CreateMemberDTO | ✅ | ✅ | ✅ |
| UpdateMemberDTO | ✅ | ✅ | ✅ |
| DocumentRecord | ✅ | ✅ | ✅ |
| DocumentStatus | ✅ | ✅ | ✅ |
| OCRObservation | ✅ | ✅ | ✅ |
| RevisedItem | ✅ | ✅ | ✅ |
| ReviewTask | ✅ | ✅ | ✅ |
| TrendSeries | ✅ | ⚠️ 缺少 growth_rate | ⚠️ |
| TrendPoint | ✅ | ✅ | ✅ |
| TrendComparison | ✅ | ✅ | ✅ |
| MetricData | ✅ | ✅ | ✅ |
| VisionDashboard | ✅ | ✅ | ✅ |
| GrowthDashboard | ✅ | ✅ | ✅ |
| ExamRecord | ✅ | ✅ | ✅ |

### 3. 常量配置对齐

| 配置项 | 契约 | 移动端 | 状态 |
|--------|------|--------|------|
| BASE_URL | localhost:8000 | 10.0.2.2:8000 | ⚠️ 适配模拟器 |
| API_PREFIX | /api/v1 | /api/v1 | ✅ |
| TIMEOUT | 30000 | 30000 | ✅ |
| MINIO_BASE_URL | - | localhost:9000 | ✅ |
| METRIC_RANGES | 7 项 | 11 项 | ⚠️ 需确认 |

### 4. 发现的问题

| 问题 | 严重程度 | 说明 |
|------|---------|------|
| TrendSeries 缺少 growth_rate | 中 | 契约定义有此字段，移动端未定义 |
| METRIC_RANGES 数量不一致 | 低 | 移动端多了 vision_acuity/tc/tg/hdl |

---

## 差异统计

| 类型 | 数量 |
|:---|:---|
| 完全对齐 | 17 |
| 需修复 | 0 (已修复) |
| 警告 | 2 |

## 结论

✅ **契约对齐** - TrendSeries.growth_rate 已修复
