# 项目状态文档 (STATUS.md)

> **单一真相源**：每个 Agent 开始工作前必须读取，结束时必须更新。
> **最后更新**: 2026-04-04 by Antigravity

---

## 当前状态

**整体进度**: ✅ 移动端 App 开发完成，10 页面 + 328 UT

| 模块 | 状态 | 说明 |
|------|------|------|
| 后端 API | ✅ 正常 | FastAPI 运行在端口 8000 |
| 后端测试 | ✅ 正常 | 21 unit tests passed |
| 前端页面 | ✅ 正常 | Next.js 运行在端口 3001 |
| 移动端 App | ✅ 完成 | React Native + Expo, 10 页面 |
| 移动端测试 | ✅ 完成 | 328 tests passed |
| CI/CD | ✅ 完成 | GitHub Actions UT 流水线 |
| 数据库 | ✅ 正常 | 已添加 file_hash 列 |

---

## 今日完成的工作

### 1. 移动端 App 开发
- **新增** React Native + Expo 项目 (`mobile_app/`)
- **实现** 10 个页面：首页、成员 Dashboard、成员表单、编辑、趋势、审核列表、审核详情、记录详情、上传
- **添加** 328 个单元测试（constants, models, client, business logic, API services, contract tests）
- **添加** CI/CD 流水线 (`.github/workflows/ut.yml`)

### 2. Bug 修复 (BUG-043)
- **移动端** 修复 `TrendSeries` 缺少 `growth_rate` 字段
- **移动端** 修复 `deleteExamRecord` API 路径错误
- **后端** 修复 `DocumentUploadResponse` 缺少字段

### 3. 文档更新
- **新增** `MOBILE_UI_SPEC.md` - 移动端 UI 规格
- **新增** `MOBILE_API_CONTRACT.md` - 移动端 API 对接说明
- **新增** `MOBILE_TECH_DECISION.md` - 技术选型决策
- **更新** `API_CONTRACT.md` - 添加重复上传响应示例
- **更新** `BUG_LOG.md` - 添加 BUG-043 记录

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
2. 添加前端 UT 测试

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
