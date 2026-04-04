# QA Pipeline 用例筛选功能

## 功能概述

扩展 `scripts/qa_pipeline.py` 支持批量回归时指定用例类别，精确控制测试范围。

## 测试分类标签

| 标签 | 说明 | 适用场景 |
|------|------|----------|
| `critical` | 核心链路（上传→OCR→审核→仪表盘） | 发布前必跑 |
| `smoke` | 冒烟测试 | 日常验证 |
| `regression` | 回归测试 | 全量回归 |
| `ut` | 单元测试（后端 + 移动端） | 开发阶段 |

## 使用方式

### 基础用法

```bash
# 全量测试（默认）
python scripts/qa_pipeline.py --mode docker

# 仅跑 E2E 核心链路
python scripts/qa_pipeline.py --mode e2e --tags critical

# 仅跑冒烟测试
python scripts/qa_pipeline.py --mode e2e --tags smoke

# 仅跑回归测试
python scripts/qa_pipeline.py --mode e2e --tags regression

# 仅跑 UT
python scripts/qa_pipeline.py --mode local --no-ut --run-ut

# 跑 UT + E2E 核心链路
python scripts/qa_pipeline.py --mode docker --tags critical
```

### 高级筛选

```bash
# 按文件名匹配
python scripts/qa_pipeline.py --mode e2e --spec "upload*"

# 排除特定测试
python scripts/qa_pipeline.py --mode e2e --exclude "ux"

# 组合使用
python scripts/qa_pipeline.py --mode e2e --tags "critical,smoke" --exclude "ux"
```

### 模式说明

| 模式 | 说明 | 默认行为 |
|------|------|----------|
| `docker` | Docker 后端 + 本地前端 + 测试 | 跑 UT + E2E |
| `local` | 全本地 SQLite | 跑 UT + E2E |
| `e2e` | 仅启动服务跑 E2E | 跳过 UT |
| `dev` | 仅启动开发环境 | 不跑测试 |

## E2E 标签分布

| 测试文件 | 标签 |
|----------|------|
| `upload-to-dashboard.spec.ts` | `@critical @smoke @regression` |
| `manual-crud.spec.ts` | `@critical @regression` |
| `member-management.spec.ts` | `@critical @smoke @regression` |
| `dashboard.spec.ts` | `@smoke @regression` |
| `error-states.spec.ts` | `@smoke @regression` |
| `review-workflow.spec.ts` | `@smoke @regression` |
| `ux-experience.spec.ts` | `@regression` |

## 实现细节

### 命令构建逻辑

1. **标签筛选** → `npx playwright test --grep "critical|smoke"`
2. **文件名匹配** → `npx playwright test upload*`
3. **排除测试** → `npx playwright test --ignore=e2e/ux.spec.ts`
4. **UT 筛选** → `pytest -m ut` / `pytest -k 'member'`

### 参数优先级

```
--spec > --tags > --exclude > 默认全量
```

## 验证

```bash
# 验证帮助信息
python scripts/qa_pipeline.py --help

# 验证命令构建
python -c "from scripts.qa_pipeline import build_e2e_command; print(build_e2e_command(tags='critical'))"
```
