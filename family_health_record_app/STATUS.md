# 项目状态文档 (STATUS.md)

> **单一真相源**：每个 Agent 开始工作前必须读取，结束时必须更新。
> **最后更新**: 2026-04-02 by Antigravity

---

## 当前状态

**整体进度**: ✅ Docker 部署方案完成，预构建镜像可用

| 模块 | 状态 | 说明 |
|------|------|------|
| 后端 API | ✅ 正常 | FastAPI 运行在端口 8000 |
| 后端测试 | ✅ 通过 | 89 个 pytest 测试全部通过 |
| 前端页面 | ✅ 正常 | Next.js 运行在端口 3001 |
| Docker 部署 | ✅ 完成 | 预构建镜像 + 国内源加速 |

---

## Docker 镜像

| 镜像 | 大小 | 说明 |
|------|------|------|
| qa-base | 448MB | 基础镜像 (Python 3.11 + Node.js 20) |
| qa-backend | 617MB | 后端含依赖 |
| qa-frontend | 1.32GB | 前端含依赖 |

### 镜像特性
- ✅ 国内源：阿里云 apt/pip、淘宝 npm
- ✅ 依赖预装：启动无需等待
- ✅ 热更新：源码挂载即时生效

---

## 快速启动

```bash
cd infra
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

### E2E 测试
```bash
cd family_health_record_app/frontend
npx playwright test
```

### 健康检查
```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","version":"v1.3.0"}
```

---

## 已完成的修复

### BUG-020: 前端 204 No Content 解析崩溃 ✅
- 修复 `client.ts`：在解析 JSON 前判断 `status !== 204`

### BUG-021: 趋势图/折线图渲染失效 ✅
- 修复 `trends/page.tsx`：修正 `null side` 的逻辑判断

---

## 待完成任务

| 优先级 | 任务 | 状态 |
|--------|------|------|
| P1 | E2E 测试用例完善 | 进行中 |
| P1 | 测试覆盖率提升 | 当前 10.3% |
| P2 | 用户认证/授权 | 待定 |

---

## 开发日志

- **2026-04-02**: 完成 Docker 预构建镜像方案，配置国内源，更新部署文档
- **2026-04-01**: 成功执行 MCP 前端测试，修复删除和趋势图 Bug

---

## 环境状态

**Docker 服务**:
- 后端: http://localhost:8000 (qa-backend)
- 前端: http://localhost:3001 (qa-frontend)
- 数据库: PostgreSQL 16 (健康)
- 存储: MinIO (健康)
