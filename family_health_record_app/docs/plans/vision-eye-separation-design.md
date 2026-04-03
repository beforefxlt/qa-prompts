# 设计文档：视力数据左右眼分离展示与录入增强

> **版本**: v1.0.0
> **创建日期**: 2026-04-03
> **状态**: Draft
> **关联需求**: 视力数据需要支持左右眼分开记录、分开展示、分开折线图

---

## 1. 需求概述

### 1.1 背景

当前系统已实现左右眼数据的**存储分离**（`observations.side` 字段），但在**展示层**和**录入层**存在以下不足：

1. 图表只能双眼合并展示（实线 vs 虚线），无法单独查看某只眼的趋势
2. 手动录入需要逐条添加左右眼记录，效率低
3. 趋势页历史列表虽有左右眼分列，但缺少单眼聚焦能力

### 1.2 目标

| 目标 | 说明 |
|:---|:---|
| **分开记录** | 手动录入支持左右眼并排同时填写，一次提交 |
| **分开展示** | Dashboard 和趋势页增加「双眼 / 左眼 / 右眼」切换按钮 |
| **分开折线图** | 切换到单眼模式时，选中眼正常显示，另一眼淡化为灰色背景线 |

### 1.3 范围界定

| 在范围内 | 不在范围内 |
|:---|:---|
| 眼轴 (axial_length) 左右眼切换 | 新增其他眼部指标（球镜/柱镜等） |
| 视力 (vision_acuity) 左右眼切换 | 后端数据库结构变更 |
| 手动录入表单左右眼并排输入 | OCR 识别链路变更 |
| Dashboard 近视防控看板 | 派生指标计算逻辑 |
| 趋势分析页 (trends) | |

---

## 2. 现状分析

### 2.1 数据库层（无需变更）

`observations` 表已支持 `side` 字段：

| 字段 | 类型 | 约束 |
|:---|:---|:---|
| `side` | VARCHAR | 枚举：`left`, `right`, `NULL` |

### 2.2 后端 API 层（需增强）

| 接口 | 现状 | 需变更 |
|:---|:---|:---|
| `GET /members/{id}/trends` | 返回 `{date, value, side}` 系列 + comparison | ✅ 已支持，无需变更 |
| `GET /members/{id}/vision-dashboard` | 返回 axial_length + vision_acuity 系列 | ⚠️ vision_acuity 缺少 comparison/alert_status |
| `POST /members/{id}/manual-exams` | 接受 observations 数组 | ✅ 已支持，前端改造即可 |

### 2.3 前端层（主要变更点）

| 组件 | 现状 | 需变更 |
|:---|:---|:---|
| `TrendChart.tsx` | 固定双眼渲染（实线+虚线） | 增加 eyeMode prop，支持单眼/双眼模式 |
| `page.tsx` (Dashboard) | 只有眼轴趋势卡片 | 增加视力趋势卡片 + 眼轴/视力切换按钮 |
| `trends/page.tsx` | 固定双眼渲染 | 增加「双眼/左眼/右眼」切换控件 |
| `ManualEntryOverlay.tsx` | 逐条添加指标+侧向选择 | 眼轴/视力改为左右眼并排输入 |

---

## 3. API 契约变更

### 3.1 vision-dashboard 增强

**接口**: `GET /api/v1/members/{member_id}/vision-dashboard`

**变更**: 为 `vision_acuity` 增加与 `axial_length` 相同的完整结构。

**变更后响应体**:

```json
{
  "member_id": "uuid",
  "member_type": "child",
  "baseline_age_months": "2009-10-01",
  "axial_length": {
    "series": [
      { "date": "2024-09-21", "value": 24.35, "side": "right" },
      { "date": "2024-09-21", "value": 23.32, "side": "left" },
      { "date": "2025-03-15", "value": 24.50, "side": "right" },
      { "date": "2025-03-15", "value": 23.45, "side": "left" }
    ],
    "reference_range": null,
    "alert_status": "normal",
    "growth_rate": 0.15,
    "comparison": {
      "left": { "current": 23.45, "previous": 23.32, "delta": 0.13 },
      "right": { "current": 24.50, "previous": 24.35, "delta": 0.15 }
    }
  },
  "vision_acuity": {
    "series": [
      { "date": "2024-09-21", "value": "0.8", "side": "left" },
      { "date": "2024-09-21", "value": "1.0", "side": "right" },
      { "date": "2025-03-15", "value": "0.9", "side": "left" },
      { "date": "2025-03-15", "value": "1.0", "side": "right" }
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

**字段说明**:

| 路径 | 类型 | 说明 |
|:---|:---|:---|
| `vision_acuity.series` | Array | 同 axial_length，每个数据点含 `{date, value, side}` |
| `vision_acuity.reference_range` | string\|null | 视力参考区间，如 "0.8-1.2" |
| `vision_acuity.alert_status` | string | `normal` / `warning` |
| `vision_acuity.comparison` | object\|null | 最近两次检查的左右眼对比，结构同 axial_length.comparison |
| `vision_acuity.comparison.left` | object\|null | 左眼对比：`{current, previous, delta}` |
| `vision_acuity.comparison.right` | object\|null | 右眼对比：`{current, previous, delta}` |

> **说明**: vision_acuity 的 `value` 字段可能是字符串（如 "0.8"）或数字，前端需兼容处理。comparison 中的值统一转为数字。

### 3.2 trends 接口（无需变更）

`GET /api/v1/members/{member_id}/trends?metric={metric}` 已完整支持左右眼分离，返回结构不变。

### 3.3 manual-exams 接口（无需变更）

`POST /api/v1/members/{member_id}/manual-exams` 已支持 observations 数组，前端只需在一次请求中同时发送左右眼两条 observation 即可。

---

## 4. UI 设计

### 4.1 组件一：EyeModeToggle（眼睛模式切换器）

**位置**: 出现在 Dashboard 近视防控看板 和 趋势分析页 的图表上方

**外观**:

```
┌─────────────────────────────────────────┐
│  📊 近视防控看板           [详细趋势 →] │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ [● 双眼] [○ 左眼] [○ 右眼]       │  │ ← 新增切换器
│  │                                   │  │
│  │     ┌─ 折线图区域 ───────────┐   │  │
│  │     │                        │   │  │
│  │     │                        │   │  │
│  │     └────────────────────────┘   │  │
│  │                                   │  │
│  │  左眼当前: 23.32mm  上次: 23.10  │  │
│  │  右眼当前: 24.35mm  上次: 24.10  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**交互规则**:

| 模式 | 图表表现 | 底部数值展示 |
|:---|:---|:---|
| **双眼** | 左眼实线 (#3b82f6)，右眼虚线 (#60a5fa) | 左右眼分两列展示 |
| **左眼** | 左眼实线正常显示，右眼变为浅灰色淡线 (#cbd5e1, opacity: 0.3) | 只展示左眼当前/上次值 |
| **右眼** | 右眼实线正常显示，左眼变为浅灰色淡线 (#cbd5e1, opacity: 0.3) | 只展示右眼当前/上次值 |

**状态持久化**: 切换状态**不持久化**，每次进入页面重置为「双眼」模式。

### 4.2 组件二：Dashboard 视力趋势卡片

**位置**: Dashboard 近视防控看板区域，眼轴卡片下方或并列

**外观**（儿童 Dashboard 布局调整）:

```
┌─────────────────────────────────────────────────────────┐
│  👁 近视防控看板                          [详细趋势 →]   │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  眼轴 (Axial)    │  │  视力 (Acuity)   │            │ ← 新增
│  │  [●双眼][○左][○右]│  │  [●双眼][○左][○右]│            │
│  │                  │  │                  │            │
│  │   ┌─折线图─┐     │  │   ┌─折线图─┐     │            │
│  │   │        │     │  │   │        │     │            │
│  │   └────────┘     │  │   └────────┘     │            │
│  │                  │  │                  │            │
│  │  左 23.32 右24.35│  │  左 0.8  右 1.0  │            │
│  └──────────────────┘  └──────────────────┘            │
│                                                         │
│  ┌──────────────────────────────────────────┐          │
│  │  最近两次检查对比                         │          │
│  │  眼轴: 左 +0.22mm  右 +0.25mm            │          │
│  │  视力: 左 +0.1     右 0.0                │          │ ← 新增
│  └──────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────┘
```

**布局策略**:

| 屏幕尺寸 | 布局 |
|:---|:---|
| 桌面端 (md+) | 眼轴和视力卡片左右并排 (grid-cols-2) |
| 移动端 | 眼轴卡片在上，视力卡片在下 (stacked) |

### 4.3 组件三：手动录入双眼并排表单

**位置**: ManualEntryOverlay 弹窗内

**变更**: 当选择 `axial_length` 或 `vision_acuity` 时，不再显示侧向下拉框，改为左右眼并排输入框。

**外观**:

```
┌─────────────────────────────────────────────────────────┐
│  ✍️ 手动录入指标                              [×]       │
│                                                         │
│  检查日期: [2026-04-03]    机构: [市第一眼科医院]       │
│                                                         │
│  指标列表:                              [+ 添加指标]    │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 类型: [眼轴长度 ▼]                                │ │
│  │                                                   │ │
│  │  ┌─────────────────┐  ┌─────────────────┐        │ │
│  │  │ 👁 左眼 (mm)     │  │ 👁 右眼 (mm)     │        │ │
│  │  │ [23.32      ]   │  │ [24.35      ]   │        │ │
│  │  └─────────────────┘  └─────────────────┘        │ │
│  │                                                   │ │
│  │                           [🗑 删除此行]           │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 类型: [视力 ▼]                                    │ │
│  │                                                   │ │
│  │  ┌─────────────────┐  ┌─────────────────┐        │ │
│  │  │ 👁 左眼          │  │ 👁 右眼          │        │ │
│  │  │ [0.8        ]   │  │ [1.0        ]   │        │ │
│  │  └─────────────────┘  └─────────────────┘        │ │
│  │                                                   │ │
│  │                           [🗑 删除此行]           │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 类型: [身高 ▼]                                    │ │
│  │ 数值 (cm): [125.5]        [🗑 删除此行]           │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│                              [取消]  [保存记录]        │
└─────────────────────────────────────────────────────────┘
```

**交互规则**:

| 场景 | 行为 |
|:---|:---|
| 选择眼轴/视力 | 显示左右眼并排输入框，无侧向下拉 |
| 选择身高/体重等非眼部指标 | 显示单个数值输入框（保持原有样式） |
| 只填左眼不填右眼 | 只提交左眼 observation，右眼不提交 |
| 只填右眼不填左眼 | 只提交右眼 observation，左眼不提交 |
| 左右眼都填 | 提交两条 observation（side 分别为 left/right） |
| 左右眼都不填 | 该行不提交任何 observation |

### 4.4 组件四：趋势页历史列表（优化确认）

**现状**: 趋势页历史列表已实现左右眼分列展示，无需结构变更。

**优化点**: 与 EyeModeToggle 联动 — 当切换到单眼模式时，历史列表中高亮对应眼的数据列，淡化另一列。

---

## 5. 交互设计详述

### 5.1 EyeModeToggle 组件 Props

```typescript
type EyeMode = 'both' | 'left' | 'right';

interface EyeModeToggleProps {
  mode: EyeMode;
  onChange: (mode: EyeMode) => void;
}
```

### 5.2 TrendChart 组件 Props 变更

**变更前**:
```typescript
interface TrendChartProps {
  data: ChartPoint[];
  metric: string;
  height?: number | string;
  referenceRange?: string;
}
```

**变更后**:
```typescript
type EyeMode = 'both' | 'left' | 'right';

interface TrendChartProps {
  data: ChartPoint[];
  metric: string;
  height?: number | string;
  referenceRange?: string;
  eyeMode?: EyeMode;  // 新增，默认 'both'
}
```

### 5.3 ChartPoint 类型（不变）

```typescript
type ChartPoint = {
  date: string;
  left?: number;
  right?: number;
  value?: number;  // 兼容单列数据
};
```

### 5.4 TrendChart 渲染逻辑

```
eyeMode === 'both':
  左眼 → 实线 #3b82f6, strokeWidth: 3
  右眼 → 虚线 #60a5fa, strokeDasharray: "5 5", strokeWidth: 2

eyeMode === 'left':
  左眼 → 实线 #3b82f6, strokeWidth: 3 (正常)
  右眼 → 实线 #cbd5e1, strokeWidth: 1, opacity: 0.3 (淡化)

eyeMode === 'right':
  右眼 → 实线 #3b82f6, strokeWidth: 3 (正常)
  左眼 → 实线 #cbd5e1, strokeWidth: 1, opacity: 0.3 (淡化)
```

### 5.5 底部数值展示逻辑

```
eyeMode === 'both':
  左右眼分两列展示，各显示当前值/上次值

eyeMode === 'left':
  只展示左眼列，标题改为"左眼当前"/"左眼上次"
  右眼列隐藏

eyeMode === 'right':
  只展示右眼列，标题改为"右眼当前"/"右眼上次"
  左眼列隐藏

eyeMode 不适用于非眼部指标（height/weight）:
  保持原有"当前数值/上次数值"布局
```

### 5.6 手动录入表单提交逻辑

**变更**: `ManualEntryOverlay.tsx` 的 `ObservationInput` 类型扩展

```typescript
// 变更前
type ObservationInput = {
  metric_code: string;
  value_numeric: number;
  unit: string;
  side: string | null;
};

// 变更后 — 眼部指标使用双眼输入模式
type EyeObservationInput = {
  metric_code: 'axial_length' | 'vision_acuity';
  left_value: number | null;   // 左眼值，null 表示未填写
  right_value: number | null;  // 右眼值，null 表示未填写
  unit: string;
};

type SingleObservationInput = {
  metric_code: string;  // 非眼部指标
  value_numeric: number;
  unit: string;
};

type ObservationInput = EyeObservationInput | SingleObservationInput;
```

**提交时转换逻辑**:

```typescript
// 将表单数据转换为 API 期望的 observations 数组
function buildObservations(inputs: ObservationInput[]) {
  const observations = [];
  
  for (const input of inputs) {
    if (isEyeInput(input)) {
      if (input.left_value !== null) {
        observations.push({
          metric_code: input.metric_code,
          value_numeric: input.left_value,
          unit: input.unit,
          side: 'left'
        });
      }
      if (input.right_value !== null) {
        observations.push({
          metric_code: input.metric_code,
          value_numeric: input.right_value,
          unit: input.unit,
          side: 'right'
        });
      }
    } else {
      observations.push(input);
    }
  }
  
  return observations;
}
```

---

## 6. 后端变更清单

### 6.1 trends.py — vision-dashboard 增强

**文件**: `backend/app/routers/trends.py`

**变更**: 在 `get_vision_dashboard` 函数中，为 `vision_acuity` 增加 `reference_range`、`alert_status`、`comparison` 字段，逻辑与 `axial_length` 完全对称。

**伪代码**:

```python
# 在 vision-dashboard 返回前增加：

# 计算视力年变化率（同眼轴逻辑）
vision_growth_rate = _calculate_growth_rate(vision_rows)  # 复用现有函数

# 计算最近两次检查的左右眼视力对比
vision_comparison = _build_comparison(vision_rows)  # 同 axial_comparison 逻辑

return {
    ...
    "vision_acuity": {
        "series": [...],
        "reference_range": next((row.reference_range for row in vision_rows if row.reference_range), None),
        "alert_status": "warning" if any(row.is_abnormal for row in vision_rows) else "normal",
        "comparison": vision_comparison,
    },
    ...
}
```

> **注意**: vision_acuity 的 `value` 可能来自 `value_text`（字符串如 "0.8"）或 `value_numeric`。在计算 comparison 时需统一转为 float。

### 6.2 数据库变更

**无需变更**。现有 `observations.side` 字段已满足需求。

---

## 7. 前端变更清单

### 7.1 文件变更矩阵

| 文件 | 变更类型 | 说明 |
|:---|:---|:---|
| `frontend/src/components/charts/TrendChart.tsx` | 修改 | 增加 `eyeMode` prop，变更渲染逻辑 |
| `frontend/src/components/charts/EyeModeToggle.tsx` | **新增** | 眼睛模式切换器组件 |
| `frontend/src/app/members/[id]/page.tsx` | 修改 | 增加视力趋势卡片 + 切换器状态 |
| `frontend/src/app/members/[id]/trends/page.tsx` | 修改 | 增加切换器 + 传递 eyeMode 给 TrendChart |
| `frontend/src/components/records/ManualEntryOverlay.tsx` | 修改 | 眼部指标改为双眼并排输入 |
| `frontend/src/app/api/client.ts` | 不变 | API 接口无需变更 |

### 7.2 新增组件：EyeModeToggle.tsx

```typescript
'use client';

import React from 'react';

type EyeMode = 'both' | 'left' | 'right';

interface EyeModeToggleProps {
  mode: EyeMode;
  onChange: (mode: EyeMode) => void;
}

const MODE_LABELS: Record<EyeMode, string> = {
  both: '双眼',
  left: '左眼',
  right: '右眼',
};

export const EyeModeToggle: React.FC<EyeModeToggleProps> = ({ mode, onChange }) => {
  return (
    <div className="inline-flex bg-slate-100 rounded-full p-1 gap-1">
      {(['both', 'left', 'right'] as EyeMode[]).map((m) => (
        <button
          key={m}
          onClick={() => onChange(m)}
          className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
            mode === m
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          {MODE_LABELS[m]}
        </button>
      ))}
    </div>
  );
};
```

---

## 8. 测试计划

### 8.1 后端测试

| 测试用例 | 说明 |
|:---|:---|
| `test_vision_dashboard_returns_comparison` | vision-dashboard 返回 vision_acuity.comparison |
| `test_vision_dashboard_comparison_same_date_no_comparison` | 同次检查的左右眼不产生 comparison |
| `test_vision_dashboard_acuity_string_value` | vision_acuity 的 value 为字符串时 comparison 正确计算 |

### 8.2 前端测试

| 测试用例 | 说明 |
|:---|:---|
| `EyeModeToggle renders three modes` | 渲染双眼/左眼/右眼三个按钮 |
| `EyeModeToggle calls onChange on click` | 点击切换按钮触发 onChange |
| `TrendChart renders both eyes in both mode` | eyeMode='both' 时渲染两条线 |
| `TrendChart dims non-selected eye in left mode` | eyeMode='left' 时右眼线淡化 |
| `TrendChart dims non-selected eye in right mode` | eyeMode='right' 时左眼线淡化 |
| `ManualEntryOverlay shows dual inputs for axial_length` | 选择眼轴时显示左右眼并排输入 |
| `ManualEntryOverlay shows dual inputs for vision_acuity` | 选择视力时显示左右眼并排输入 |
| `ManualEntryOverlay shows single input for height` | 选择身高时显示单个输入框 |
| `ManualEntryOverlay submits only filled eyes` | 只填左眼时只提交左眼 observation |

---

## 9. 验收标准

| # | 验收项 | 验证方式 |
|:---|:---|:---|
| 1 | Dashboard 儿童页面同时展示眼轴和视力趋势卡片 | 手动验证 |
| 2 | 眼轴/视力卡片上方有「双眼/左眼/右眼」切换按钮 | 手动验证 |
| 3 | 切换到「左眼」时，左眼实线正常，右眼变为灰色淡线 | 手动验证 |
| 4 | 切换到「右眼」时，右眼实线正常，左眼变为灰色淡线 | 手动验证 |
| 5 | 切换回「双眼」时，恢复实线+虚线样式 | 手动验证 |
| 6 | 趋势分析页同样支持眼睛模式切换 | 手动验证 |
| 7 | 手动录入眼轴/视力时，显示左右眼并排输入框 | 手动验证 |
| 8 | 手动录入只填左眼，提交后趋势图只有左眼数据点 | 手动验证 |
| 9 | 手动录入左右眼都填，提交后趋势图有双眼数据点 | 手动验证 |
| 10 | vision-dashboard API 返回 vision_acuity.comparison | 后端测试 |
| 11 | 所有新增 UT 用例通过 | `pytest` + `npm test` |

---

## 10. 风险与依赖

| 风险 | 影响 | 缓解措施 |
|:---|:---|:---|
| vision_acuity 的 value 为字符串 | comparison 计算可能失败 | 后端统一转为 float 处理 |
| 部分历史数据只有单眼 | 单眼模式下另一眼无淡化线可显示 | 前端判断数据存在性再渲染 |
| 移动端屏幕窄 | 双眼并排输入框可能拥挤 | 移动端改为上下堆叠布局 |

---

## 11. 实施顺序

| 阶段 | 任务 | 预计工作量 |
|:---|:---|:---|
| **Phase 1** | 后端：vision-dashboard 增加 comparison/alert_status | 0.5h |
| **Phase 2** | 前端：新增 EyeModeToggle 组件 | 0.5h |
| **Phase 3** | 前端：TrendChart 支持 eyeMode prop | 1h |
| **Phase 4** | 前端：Dashboard 增加视力趋势卡片 | 1h |
| **Phase 5** | 前端：趋势页集成 EyeModeToggle | 0.5h |
| **Phase 6** | 前端：ManualEntryOverlay 双眼并排输入 | 1h |
| **Phase 7** | 测试：后端 UT + 前端 UT | 1h |
| **Phase 8** | 集成验证 + BUG_LOG 更新 | 0.5h |

**总计**: 约 6 小时
