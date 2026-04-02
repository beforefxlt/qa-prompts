# 项目状态文档 (STATUS.md)

> **单一真相源**：每个 Agent 开始工作前必须读取，结束时必须更新。
> **最后更新**: 2026-04-03 by Antigravity

---

## 当前状态

**整体进度**: ✅ 增长率计算逻辑修复完成，前后端数据一致

| 模块 | 状态 | 说明 |
|------|------|------|
| 后端 API | ✅ 正常 | FastAPI 运行在端口 8000 |
| 后端测试 | ⚠️ 需更新 | 需添加 growth_rate 和 comparison 的 UT |
| 前端页面 | ✅ 正常 | Next.js 运行在端口 3001 |
| Docker 部署 | ✅ 完成 | 预构建镜像，无 volume 挂载 |
| 数据库 | ✅ 正常 | 已添加 file_hash 列 |

---

## 今日修复的问题

### 1. 数据库 schema 缺失
- **问题**: `document_records` 表缺少 `file_hash` 列
- **修复**: 添加了 `file_hash VARCHAR(64)` 列
- **影响**: 重复上传检测功能

### 2. 智能提取失败（网络问题）
- **问题**: 前端报错"网络连接失败，请确认后端 API 是否在 8000 端口运行"
- **根因**: CORS 配置正确但之前前端 Docker 镜像未更新
- **修复**: 重新构建前端镜像（build_docker.py）

### 3. 预计年增长硬编码（BUG）
- **问题**: 前端显示 +0.22 mm/year 是硬编码默认值，数据不足时仍显示
- **修复**: 
  - 后端 `vision-dashboard` API 添加 `growth_rate` 计算逻辑
  - 后端 `growth-dashboard` API 添加 `growth_rate` 计算逻辑
  - 前端移除硬编码，显示实际值或 "N/A"

### 4. 文档更新
- **ARCHITECTURE.md**: 更新计算与分析边界说明
- **DATABASE_SCHEMA.md**: 升级到 v1.2.0
- **README.md**: 添加部署脚本路径说明

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
