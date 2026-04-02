# 测试脚本说明

## 脚本列表

| 脚本 | 说明 | 使用场景 |
|------|------|----------|
| `qa_pipeline.py` | 完整 QA 流程（支持 Docker/本地模式） | CI/CD、本地测试 |
| `docker_qa_pipeline.py` | Docker 专用测试流程 | Docker 环境测试 |
| `sync_traceability.py` | 契约同步 | 更新测试用例映射 |
| `audit_coverage.py` | 覆盖率审计 | 检查测试覆盖率 |

## 使用方法

### 1. Docker 模式（推荐）

使用预构建镜像，启动快，环境一致。

```bash
# 默认 Docker 模式
python family_health_record_app/scripts/qa_pipeline.py

# 或显式指定
python family_health_record_app/scripts/qa_pipeline.py --mode docker
```

**流程**:
1. 检查 Docker 环境
2. 启动容器 (PostgreSQL + MinIO + Backend + Frontend)
3. 等待服务就绪
4. 运行后端单元测试 (pytest)
5. 运行 E2E 测试 (Playwright)
6. 显示服务状态

### 2. 本地模式

直接在本地启动后端服务器，适合开发调试。

```bash
python family_health_record_app/scripts/qa_pipeline.py --mode local
```

**流程**:
1. 清理端口 8000
2. 同步契约
3. 运行后端单元测试
4. 启动本地后端服务器
5. 运行 E2E 测试
6. 清理服务器进程

### 3. Docker QA Pipeline

独立的 Docker 测试脚本，功能与 `qa_pipeline.py --mode docker` 相同。

```bash
python family_health_record_app/scripts/docker_qa_pipeline.py
```

## 前置条件

### Docker 模式
- Docker Desktop 已启动
- 预构建镜像已存在 (`qa-backend`, `qa-frontend`)

### 本地模式
- Python 3.11+
- Node.js 20+
- 后端依赖已安装 (`pip install -r requirements.txt`)
- 前端依赖已安装 (`npm install`)

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SILICONFLOW_API_KEY` | OCR API 密钥 | 从 `.env` 读取 |
| `DATABASE_URL` | 数据库连接 | Docker: PostgreSQL, 本地: SQLite |
| `PLAYWRIGHT_BASE_URL` | E2E 测试目标 | http://localhost:3001 |

## 输出示例

```
============================================================
>>> [QA Pipeline Start] 模式: docker <<<
============================================================

[1/6] 检查 Docker 环境...

[2/6] 清理旧容器...

[3/6] 启动 Docker 服务...
执行命令: docker compose up -d

[4/6] 等待服务启动...
✅ 后端 已就绪
✅ 前端 已就绪

[5/6] 运行后端单元测试...
============================= test session starts ==============================
...
89 passed in 2.34s

[6/6] 运行 E2E 测试...
Running 17 tests using 1 worker
...
17 passed in 45.23s

============================================================
>>> [Docker QA Pipeline Complete] <<<
============================================================

访问地址:
  - 前端: http://localhost:3001
  - 后端: http://localhost:8000
  - API 文档: http://localhost:8000/docs
```

## 故障排除

### Docker 未运行
```
❌ Docker 未运行，请先启动 Docker Desktop
```
**解决**: 启动 Docker Desktop，等待状态变为 "Running"

### 后端启动超时
```
❌ 后端启动超时
```
**解决**: 
1. 查看日志: `docker compose logs backend`
2. 检查端口占用: `netstat -ano | findstr :8000`
3. 重启 Docker Desktop

### 前端构建失败
```
❌ 前端 启动超时
```
**解决**:
1. 查看日志: `docker compose logs frontend`
2. 清理缓存: `rm -rf family_health_record_app/frontend/.next`
3. 重启服务: `docker compose restart frontend`

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: QA Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start Docker
        run: |
          cd family_health_record_app/infra
          docker compose up -d
          
      - name: Wait for services
        run: sleep 60
        
      - name: Run backend tests
        run: |
          docker exec health-record-backend python -m pytest tests/ -v
          
      - name: Run E2E tests
        run: |
          cd family_health_record_app/frontend
          npx playwright test
```
