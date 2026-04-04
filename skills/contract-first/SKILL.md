---
name: contract-first
description: Use when adding/modifying API endpoints, Pydantic schemas, or backend validation rules
version: v1.0.0
last_updated: 2026-04-04
---

# Contract-First Development

> **核心原则**：契约先行 - 后端校验规则必须同步到文档，前端必须对齐

## Why This Matters

基于 BUG_LOG 分析：
- BUG-034: 前后端 gender 字段值不一致（"男" vs "male"）
- BUG-036: 前端默认值 0 不满足后端 ≥30 校验
- BUG-037: revised_items 格式完全错误
- BUG-038: 前端无 > 0 校验，后端要求 > 0

**根因**：契约断裂 - Pydantic 校验规则未同步到前端和文档

---

## 禁止规则 (❌)

```
❌ 不准在 Pydantic schema 添加校验后，不更新 API_CONTRACT.md
❌ 不准在后端添加新字段校验，不同步前端表单校验
❌ 不准修改 API 路径/参数，不更新 API_CONTRACT.md
❌ 不准在 schemas/ 添加新校验规则，不更新 METRIC_OPTIONS
❌ 不准修改后端默认值，不检查前端是否兼容
```

---

## 必须规则 (✅)

### 1. 新增 Pydantic 校验 → 必须同步到 3 处

```
schemas/observation.py:validate_sanity_range 添加新指标校验
    ↓
API_CONTRACT.md 数值约束表添加新行
    ↓
frontend/src/components/records/METRIC_OPTIONS 添加 min/max
```

### 2. 修改 API 字段 → 必须更新 2 处

```
后端 schema 字段变更
    ↓
API_CONTRACT.md 示例请求/响应更新
    ↓
前端对应字段处理逻辑检查
```

### 3. 新增 API → 必须更新契约文档

```
新增 API 端点
    ↓
API_CONTRACT.md 添加接口定义（方法/路径/请求/响应）
    ↓
检查前端是否有对应调用
```

---

## 触发场景

此 SKILL 应该在以下场景自动加载：
- 修改 `app/schemas/` 目录下的文件
- 修改 `app/routers/` 目录下的文件
- 修改 `API_CONTRACT.md`
- 修改 `frontend/src/components/records/ManualEntryOverlay.tsx`

---

## 验证清单

完成修改后，必须检查：

- [ ] API_CONTRACT.md 数值约束表是否已更新？
- [ ] 前端 METRIC_OPTIONS.min/max 是否与后端对齐？
- [ ] 新增校验规则是否在测试中覆盖边界值？

---

## Related Files

- `family_health_record_app/docs/specs/API_CONTRACT.md`
- `family_health_record_app/backend/app/schemas/`
- `family_health_record_app/frontend/src/components/records/ManualEntryOverlay.tsx`
- `family_health_record_app/docs/BUG_LOG.md` (根因分析)