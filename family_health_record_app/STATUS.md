# 项目状态文档 (STATUS.md)

> **单一真相源**：每个 Agent 开始工作前必须读取，结束时必须更新。
> **最后更新**: 2026-04-02 by Antigravity

---

## 当前状态

**整体进度**: ✅ OCR 提示词管理重构完成，Docker 部署方案稳定

| 模块 | 状态 | 说明 |
|------|------|------|
| 后端 API | ✅ 正常 | FastAPI 运行在端口 8000 |
| 后端测试 | ✅ 通过 | 99 个 pytest 测试全部通过 |
| 前端页面 | ✅ 正常 | Next.js 运行在端口 3001，样式正常 |
| E2E 测试 | ⚠️ 待修复 | 前端 Docker 挂载问题导致 E2E 无法运行 |
| Docker 部署 | ✅ 完成 | 预构建镜像，无 volume 挂载 |

---

## 后端测试结果

```
99 passed, 4 warnings in 34.50s
```

| 测试类型 | 用例数 | 状态 |
|----------|--------|------|
| 单元测试 | 11 | ✅ |
| API 合约 | 15 | ✅ |
| Golden Set | 4 | ✅ |
| 集成测试 | 30 | ✅ |
| 容灾测试 | 11 | ✅ |
| 体验测试 | 11 | ✅ |
| 基础设施 | 3 | ✅ |
| 路由测试 | 14 | ✅ |

---

## Docker 镜像

| 镜像 | 大小 | 说明 |
|------|------|------|
| qa-base | 448MB | 基础镜像 (Python 3.11 + Node.js 20) |
| qa-backend | 617MB | 后端含 pytest 依赖 |
| infra-frontend | ~500MB | 前端含依赖 |

---

## 快速启动

```bash
cd family_health_record_app/infra
docker compose up -d
```

访问：
- 前端: http://localhost:3001
- 后端: http://localhost:8000
- API 文档: http://localhost:8000/docs

---

## 测试运行

### 后端测试
```bash
docker exec health-record-backend python -m pytest tests/ -v
```

### 健康检查
```bash
curl http://localhost:8000/api/v1/health
```

---

## 本次更新

### 新增功能
1. ✅ OCR 提示词管理器 (`prompt_manager.py`)
   - 动态组合提示词，支持多单据类型
   - 公共指令与具体逻辑分离
   - 支持眼轴、血常规等多类单据

2. ✅ 审核页面图片预览
   - 新增 `/{document_id}/preview` 端点
   - 从 MinIO 获取脱敏图片

3. ✅ 测试代码检查脚本 (`scripts/check_no_test_code.py`)
   - 自动扫描生产代码中的测试逻辑

### 修复的问题
1. ✅ OCR 文件路径不一致（MinIO key 格式处理）
2. ✅ OCR E2E mock 逻辑移除
3. ✅ 前端 Docker 部署问题（移除 volume 挂载）
4. ✅ Golden Set 测试适配新签名
5. ✅ 前端配置文件名修正（`.js` 替代 `.ts`/`.mjs`）

### 规范更新
1. ✅ AGENTS.md 第7条红线：修复自测验证
2. ✅ AGENTS.md 第8条红线：生产代码禁止测试逻辑

---

## 待完成任务

| 优先级 | 任务 | 状态 |
|--------|------|------|
| P1 | E2E 测试修复 | 进行中 |
| P1 | 视觉回归测试 | 待定 |
| P2 | 用户认证/授权 | 待定 |

---

## 开发日志

- **2026-04-02**: 
  - OCR 提示词管理重构
  - 审核页面图片预览
  - 前端 Docker 部署修复
  - 新增测试代码检查脚本
  - 更新 AGENTS.md 规范
- **2026-04-01**: 
  - 完成 Docker 预构建镜像方案
  - 修复 E2E 测试 (17/17)

---

## 环境状态

**Docker 服务**:
- 后端: http://localhost:8000 (qa-backend)
- 前端: http://localhost:3001 (infra-frontend)
- 数据库: PostgreSQL 16 (健康)
- 存储: MinIO (健康)
