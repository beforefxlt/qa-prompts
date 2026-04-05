# 移动端 API 对接说明

> **版本**: v1.0.0  
> **基于**: API_CONTRACT.md (v2.4.0)  
> **最后更新**: 2026-04-04

## 1. 概述

本文档说明移动端（React Native + Expo）与后端 API 的对接方式。
移动端 API 调用与 Web 端基本一致，仅在以下场景有差异：

1. 图片上传方式
2. 分页处理（移动端优化）
3. 错误处理（移动端特有）
4. 离线支持（可选）

**核心约束**：本应用为内网免登录部署，所有接口无需携带认证 Token。

## 2. API 端点对照

### 2.1 基础配置

| 配置项 | 值 |
|--------|-----|
| **Base URL** | `http://localhost:8000` |
| **API 版本** | `v1` |
| **完整前缀** | `/api/v1` |
| **认证** | 无需 Token |

> **注意**：移动端开发时，后端服务需运行在可访问的 IP/域名。模拟器中可用 `10.0.2.2` 访问主机 localhost。

### 2.2 端点清单

| 序号 | 方法 | 路径 | Web 版 | 移动版 | 差异说明 |
|------|------|------|--------|--------|----------|
| 1 | GET | `/api/v1/members` | ✅ | ✅ | 一致 |
| 2 | POST | `/api/v1/members` | ✅ | ✅ | 一致 |
| 3 | GET | `/api/v1/members/{id}` | ✅ | ✅ | 一致 |
| 4 | PUT | `/api/v1/members/{id}` | ✅ | ✅ | 一致 |
| 5 | DELETE | `/api/v1/members/{id}` | ✅ | ✅ | 一致 |
| 6 | POST | `/api/v1/documents/upload` | ✅ | ⚠️ | 见 3.1 |
| 7 | GET | `/api/v1/documents/{id}` | ✅ | ✅ | 一致 |
| 8 | POST | `/api/v1/documents/{id}/submit-ocr` | ✅ | ✅ | 一致 |
| 9 | GET | `/api/v1/review-tasks` | ✅ | ⚠️ | 见 3.2 |
| 10 | GET | `/api/v1/review-tasks/{id}` | ✅ | ✅ | 一致 |
| 11 | POST | `/api/v1/review-tasks/{id}/approve` | ✅ | ✅ | 一致 |
| 12 | POST | `/api/v1/review-tasks/{id}/reject` | ✅ | ✅ | 一致 |
| 13 | POST | `/api/v1/review-tasks/{id}/save-draft` | ✅ | ✅ | 一致 |
| 14 | GET | `/api/v1/members/{id}/trends` | ✅ | ✅ | 一致 |
| 15 | GET | `/api/v1/members/{id}/vision-dashboard` | ✅ | ✅ | 一致 |
| 16 | GET | `/api/v1/members/{id}/growth-dashboard` | ✅ | ✅ | 一致 |
| 17 | POST | `/api/v1/records/members/{id}/manual-exams` | ✅ | ✅ | 一致 |
| 18 | PATCH | `/api/v1/records/observations/{id}` | ✅ | ✅ | 一致 |
| 19 | DELETE | `/api/v1/records/exam-records/{id}` | ✅ | ✅ | 一致 |
| 20 | GET | `/api/v1/documents/records/{record_id}` | ✅ | ✅ | 一致 |

## 3. 差异详细说明

### 3.1 图片上传（POST /api/v1/documents/upload）

**响应体示例**:
```json
{
  "document_id": "uuid",
  "status": "uploaded",
  "file_url": "minio://...",
  "desensitized_url": "minio://..."
}
```

**重复上传响应**:
```json
{
  "document_id": "uuid",
  "status": "duplicate",
  "message": "该检查单已上传过，请勿重复上传"
}
```

**Web 版**：使用 `FormData` + `axios` 自动处理 `multipart/form-data`

**移动版**：使用 `expo-image-picker` 获取文件 URI，需手动构建 `FormData`

```typescript
// 移动端示例
import * as ImagePicker from 'expo-image-picker';

const pickImage = async () => {
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ImagePicker.MediaTypeOptions.Images,
    quality: 0.8,
  });

  if (!result.canceled) {
    const file = result.assets[0];
    
    // 构建 FormData（关键）
    const formData = new FormData();
    formData.append('file', {
      uri: file.uri,
      type: 'image/jpeg',
      name: 'image.jpg',
    } as any);
    formData.append('member_id', memberId);

    // 上传
    const response = await fetch(`${BASE_URL}/api/v1/documents/upload`, {
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }
};
```

> **注意**：`FormData` 在 React Native 中需要将文件对象转为 `any` 类型才能正确发送。

### 3.2 待审核任务列表（GET /api/v1/review-tasks）

**Web 版**：返回全量数据

**移动版**：建议添加分页参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码 |
| `page_size` | int | 20 | 每页数量 |

```typescript
// 移动端请求
const response = await fetch(
  `${BASE_URL}/api/v1/review-tasks?page=1&page_size=20`
);
```

### 3.3 分页响应格式

移动端建议使用以下分页格式（需要后端支持或前端自行处理）：

```typescript
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}
```

> **注意**：当前后端 API_CONTRACT.md 中未定义分页响应格式，移动端需自行在客户端实现分页逻辑（如 FlatList 的 `onEndReached`）。

### 3.4 图片 URL 处理

后端返回的图片 URL 格式为 `minio://bucket/key`，移动端需要转换为可访问的 HTTP URL：

```typescript
const MINIO_BASE_URL = 'http://localhost:9000/health-records/';

function transformMinioUrl(minioUrl: string): string {
  if (!minioUrl) return '';
  if (minioUrl.startsWith('http')) return minioUrl;
  
  // minio://bucket/key -> http://localhost:9000/bucket/key
  const key = minioUrl.replace('minio://', '');
  return `${MINIO_BASE_URL}${key}`;
}
```

> **注意**：实际生产环境中需将 `localhost:9000` 替换为实际的 MinIO 服务地址。

## 4. 数据模型（TypeScript）

### 4.1 成员模型

```typescript
interface MemberProfile {
  id: string;
  name: string;
  gender: 'male' | 'female';
  date_of_birth: string; // YYYY-MM-DD
  member_type: 'child' | 'adult' | 'senior';
  last_check_date: string | null;
  pending_review_count: number;
}
```

### 4.2 文档模型

```typescript
interface DocumentRecord {
  id: string;
  member_id: string;
  status: DocumentStatus;
  file_url: string;
  desensitized_url: string;
  uploaded_at: string;
}

type DocumentStatus = 
  | 'uploaded'
  | 'desensitizing'
  | 'ocr_processing'
  | 'rule_checking'
  | 'pending_review'
  | 'approved'
  | 'persisted'
  | 'ocr_failed'
  | 'rule_conflict'
  | 'review_rejected';
```

### 4.3 审核任务模型

```typescript
interface ReviewTask {
  id: string;
  document_id: string;
  member_id: string;
  status: 'pending' | 'approved' | 'rejected';
  ocr_result: {
    exam_date: string;
    observations: OCRObservation[];
    confidence_score: number;
  };
  revised_items: RevisedItem[];
  created_at: string;
}

interface OCRObservation {
  metric_code: string;
  value_numeric?: number;
  value?: string;
  unit?: string;
  side?: 'left' | 'right' | null;
  confidence?: number;
}

interface RevisedItem {
  metric_code: string;
  side?: 'left' | 'right' | null;
  value?: string;
  value_numeric?: number;
  unit?: string;
}
```

### 4.4 趋势数据模型

```typescript
interface TrendSeries {
  metric: string;
  series: TrendPoint[];
  reference_range: string | null;
  alert_status: 'normal' | 'warning' | 'critical';
  comparison: TrendComparison | null;
  growth_rate?: number | null;
}

interface TrendPoint {
  date: string;
  value: number | string;
  side?: 'left' | 'right' | null;
}

interface TrendComparison {
  // 单维度对比（如身高、体重）
  current: number;
  previous: number;
  delta: number;
} | {
  // 双维度对比（如眼轴、视力）
  left: { current: number; previous: number; delta: number };
  right: { current: number; previous: number; delta: number };
}
```

### 4.5 Dashboard 模型

```typescript
interface VisionDashboard {
  member_id: string;
  member_type: string;
  baseline_age_months: number;
  axial_length: MetricData;
  vision_acuity: MetricData;
}

interface GrowthDashboard {
  member_id: string;
  member_type: string;
  height: MetricData;
  weight: MetricData;
}

interface MetricData {
  series: TrendPoint[];
  reference_range: string | null;
  alert_status: 'normal' | 'warning' | 'critical';
  growth_rate: number | null;
  comparison: TrendComparison | null;
}
```

## 5. 错误处理

### 5.1 HTTP 状态码映射

| 状态码 | 处理方式 |
|--------|----------|
| 200 | 成功 |
| 400 | 提示用户检查输入 |
| 404 | 提示"资源不存在" |
| 409 | 提示"状态冲突，请刷新重试" |
| 422 | 提示后端校验失败原因 |
| 500 | 提示"服务器错误，请稍后重试" |

### 5.2 网络错误处理

```typescript
interface NetworkError {
  code: 'NETWORK_ERROR' | 'TIMEOUT' | 'UNKNOWN';
  message: string;
}

// 处理示例
try {
  const response = await fetch(...);
} catch (error) {
  if (error.message === 'Network request failed') {
    // 提示用户检查网络
  }
}
```

## 6. 离线缓存（可选）

### 6.1 缓存策略

| 数据类型 | 缓存策略 | 失效时间 |
|----------|----------|----------|
| 成员列表 | Cache-First | 5 分钟 |
| 趋势数据 | Network-First | 1 分钟 |
| 图片 | No Cache | — |

### 6.2 缓存实现

推荐使用 `expo-file-system` 或 `@react-native-async-storage/async-storage`：

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// 读取缓存
const cached = await AsyncStorage.getItem('members');
if (cached) {
  const data = JSON.parse(cached);
  const cachedTime = data.timestamp;
  if (Date.now() - cachedTime < 5 * 60 * 1000) {
    return data.members;
  }
}
```

## 7. 常量配置

```typescript
// mobile_app/src/constants/api.ts
export const API_CONFIG = {
  BASE_URL: __DEV 
    ? 'http://10.0.2.2:8000'  // Android 模拟器访问主机
    : 'http://localhost:8000',
  API_PREFIX: '/api/v1',
  TIMEOUT: 30000, // 30 秒
  MINIO_BASE_URL: 'http://localhost:9000/health-records/',
} as const;

// 指标配置（与后端 validate_sanity_range 对齐）
export const METRIC_RANGES = {
  height: { min: 30, max: 250, unit: 'cm' },
  weight: { min: 2, max: 500, unit: 'kg' },
  axial_length: { min: 15, max: 35, unit: 'mm' },
  glucose: { min: 0.1, max: 50, unit: 'mmol/L' },
  ldl: { min: 0.1, max: 10, unit: 'mmol/L' },
  hemoglobin: { min: 30, max: 250, unit: 'g/L' },
  hba1c: { min: 3, max: 15, unit: '%' },
} as const;
```

## 8. API 调用封装示例

```typescript
// mobile_app/src/api/client.ts
const API_BASE = 'http://10.0.2.2:8000/api/v1';

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// 成员服务
export const memberService = {
  list: () => apiRequest<MemberProfile[]>('/members'),
  get: (id: string) => apiRequest<MemberProfile>(`/members/${id}`),
  create: (data: CreateMemberDTO) => 
    apiRequest<MemberProfile>('/members', { 
      method: 'POST', 
      body: JSON.stringify(data) 
    }),
  update: (id: string, data: UpdateMemberDTO) =>
    apiRequest<MemberProfile>(`/members/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    apiRequest<void>(`/members/${id}`, { method: 'DELETE' }),
};
```

## 9. 参考资料

- 后端 API 契约：[API_CONTRACT.md](./API_CONTRACT.md)
- 移动端 UI 规格：[MOBILE_UI_SPEC.md](./MOBILE_UI_SPEC.md)
- 技术选型：[MOBILE_TECH_DECISION.md](./MOBILE_TECH_DECISION.md)
