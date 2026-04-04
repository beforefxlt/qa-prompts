---
name: verify-fix
description: Use when submitting bug fixes - ensures verification checklist is completed before claiming fix is done
version: v1.0.0
last_updated: 2026-04-04
---

# Verify Fix Protocol

> **核心原则**：修复后必须验证 - 不准声称"已修复"就结束

## Why This Matters

基于 BUG_LOG 分析：
- BUG-022: 声称修复但未重启服务、未实际测试
- BUG-035: 只改局部代码，未跑构建验证
- BUG-039: 修改代码后未重启容器直接测试

**根因**：缺少验证清单流程

---

## 禁止规则 (❌)

```
❌ 不准修复代码后直接说"已修复"就结束
❌ 不准修改代码后不运行验证脚本
❌ 不准修改 API/Schema 后不运行 pytest
❌ 不准修改前端代码后不运行 npm run build
❌ 不准修改配置后不重启服务就测试
```

---

## 验证流程

### Step 1: 代码修改完成

```
完成 Bug 修复代码
```

### Step 2: 运行对应验证

| 修改类型 | 必须运行 |
|:---------|:---------|
| 后端代码改动 | `pytest` |
| 前端代码改动 | `npm run build` |
| API/Schema 改动 | `pytest` + 检查契约文档 |
| Docker/配置改动 | 重启服务后测试 |
| 路由变更 | `pytest` + `npm run build` |

### Step 3: 验证结果判定

```
pytest 结果:
  - 失败 → 修复失败，返回 Step 1
  - 通过 → 继续

npm run build 结果:
  - 失败 → 修复失败，返回 Step 1  
  - 通过 → 继续
```

### Step 4: 只有全部 PASS 才能声称"修复完成"

```
pytest ✅ + npm run build ✅ = 可以声称修复完成
pytest ❌ = 不准声称修复完成
```

---

## 验证命令速查

```bash
# 后端验证
cd family_health_record_app/backend && pytest -v

# 前端验证
cd family_health_record_app/frontend && npm run build

# 契约检查
python family_health_record_app/scripts/check_no_test_code.py

# 快速验证（推荐）
python family_health_record_app/backend/verify_fix.py
```

---

## 触发场景

此 SKILL 应该在以下场景自动加载：
- 检测到 `BUG-xxx` 相关的代码修改
- 提交包含 `fix:` 或 `bug:` 的 commit message
- 修改 `app/routers/` 或 `app/schemas/`

---

## 常见陷阱

| 陷阱 | 正确做法 |
|:-----|:---------|
| "代码看起来对" | 必须运行 pytest 验证 |
| "只是小改" | 必须运行 npm run build |
| "已经测试过了" | 修复后必须重新验证 |
| "应该没问题" | 验证清单必须完整执行 |

---

## Related Files

- `family_health_record_app/backend/verify_fix.py`
- `family_health_record_app/scripts/check_no_test_code.py`
- `family_health_record_app/docs/BUG_LOG.md`