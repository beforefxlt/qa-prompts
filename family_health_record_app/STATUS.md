# 项目状态文档 (STATUS.md)

> **单一真相源**：每个 Agent 开始工作前必须读取，结束时必须更新。
> **最后更新**: 2026-04-04 by Antigravity

---

## 当前状态

**整体进度**: ✅ 移动端 App 开发完成，代码审查修复完成，全链路测试完成

| 模块 | 状态 | 说明 |
|------|------|------|
| 后端 API | ✅ 正常 | FastAPI 运行在端口 8000 |
| 后端测试 | ✅ 正常 | 95+ tests passed |
| 前端页面 | ✅ 正常 | Next.js 运行在端口 3001 |
| 移动端 App | ✅ 完成 | React Native + Expo, 10 页面 |
| 移动端测试 | ✅ 完成 | 351 tests passed (98.4% 语句覆盖) |
| 全链路测试 | ✅ 完成 | 20 个场景（正常+异常+幂等+弱网+数据污染） |
| E2E 测试 | ✅ 完成 | 8 个测试文件，含环境自检 |
| CI/CD | ✅ 完成 | pre-commit hook + GitHub Actions |
| QA Pipeline | ✅ 完成 | 支持 --tags/--spec/--exclude 筛选 |
| ESLint | ✅ 完成 | 含自定义 no-identical-ternary 规则 |
| 数据库 | ✅ 正常 | 已添加 file_hash 列 |

---

## 今日完成的工作

### 1. 移动端代码审查 — 9 个 Bug 修复
- **BUG-044**: 审核页图片 URL 永远为空 → 提取 `resolveImageUrl()` 纯函数
- **BUG-045**: deleteExamRecord URL 缺少 memberId → 修复路径
- **BUG-046**: Dashboard 显示最旧值 → 提取 `getLatestValue()` 纯函数，4 处替换
- **BUG-047**: 空状态判断逻辑错误 → 提取 `shouldShowEmptyState()` 纯函数
- **BUG-048**: 趋势图 labels 缺失右眼日期 → 提取 `splitSeriesBySide()` 纯函数
- **BUG-049**: MINIO_BASE_URL 硬编码 localhost → 改为 10.0.2.2
- **BUG-050**: calculateComparison 无序数据 → 使用 sorted.filter()
- **BUG-051**: screenWidth 不响应旋转 → 改用 useWindowDimensions()
- **BUG-052**: URL 参数不同步 → 添加 router.replace()

### 2. 测试体系建设
- **新增 53 个测试用例**：27 个回归 + 20 个全链路 + 6 个已有文件更新
- **新增全链路测试文件** `full-pipeline.test.ts`（20 个场景）
- **新增后端集成测试** `test_full_pipeline.py`（2 个场景，使用真实 01.jpg）
- **新增 E2E 测试** `upload-to-dashboard.spec.ts`（含环境自检）
- **测试覆盖率**: 98.4% 语句 / 96.3% 分支 / 95.7% 函数

### 3. 自动化门禁建设
- **ESLint 自定义规则** `custom/no-identical-ternary` 拦截 `x ? a : a` 模式
- **pre-commit hook** 新增 `mobile-unit-tests`（全量 281 UT，~4.5s）
- **AGENTS.md 负向提示词** 新增 7 条（NP-01 ~ NP-07）
- **E2E 环境自检** `fetch('/health')` 不通则自动 skip

### 4. 文档对齐
- **更新** BUG_LOG.md — 新增 BUG-044 ~ BUG-053 记录
- **更新** AGENTS.md — 新增 7 条负向提示词
- **更新** .pre-commit-config.yaml — 新增移动端 UT hook
- **更新** eslint.config.js — 新增自定义规则
- **新增** retrospective 文档 `docs/retrospective/2026-04-04-android-client-testing.md`

---

## 待完成的任务（下次继续）

### P0 高优先级
1. **添加后端 UT 测试** 
   - 测试 `growth_rate` 计算（单组数据返回 null，两组数据返回正确值）
   - 测试 `comparison` 差值计算
   - 位置：`backend/tests/integration/test_routes.py`

2. **修复 vision-dashboard API 的 comparison**
   - 当前只计算 growth_rate，需要添加 2 次检查的差值
   - 用于显示"上次检查 vs 本次检查"的具体差值

3. **血糖/低密度脂蛋白等指标的增长率**
   - 检查是否有对应的 dashboard API
   - 如果有，添加 growth_rate 计算

### P1 中优先级
1. 完善前端展示（如果有 growth 数据，显示趋势卡片）
2. 组件测试（React Native Testing Library）- 因环境冲突暂跳过

### P2 低优先级
1. 并发上传去重（内网场景暂不处理，已标记 skip）
2. E2E 测试环境稳定性优化

---

## API 变更摘要

### 新增字段

| API | 字段 | 类型 | 说明 |
|-----|------|------|------|
| `/members/{id}/vision-dashboard` | `axial_length.growth_rate` | float? | 年增长率，null 表示数据不足 |
| `/members/{id}/growth-dashboard` | `height.growth_rate` | float? | 身高年增长率 |
| `/members/{id}/growth-dashboard` | `weight.growth_rate` | float? | 体重年增长率 |
| `/members/{id}/trends` | `comparison` | object | 两次检查差值 |

### 计算规则
- **growth_rate**: 需要至少 2 组不同日期数据，否则返回 null
- **comparison**: 需要至少 2 组数据，优先匹配相同 side

---

## 部署脚本位置

> ⚠️ 重要：部署脚本已移至 `family_health_record_app/scripts/build_docker.py`

```bash
# 进入项目目录
cd family_health_record_app

# 完整构建
python scripts/build_docker.py --all

# 启动服务
cd infra && docker compose up -d
```

---

## 环境状态

**Docker 服务**:
- 后端: http://localhost:8000 (qa-backend)
- 前端: http://localhost:3001 (infra-frontend)
- 数据库: PostgreSQL 16 (健康)
- 存储: MinIO (健康)

**成员数据**:
- 测试成员 ID: `cfcb0a17-b294-4db9-a37e-d056e7f5d6d8`
- 眼轴数据: 2024-09-21 (右 24.35, 左 23.32), 2026-03-29 (右 23.67, 左 23.6)
