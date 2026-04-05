# 家庭检查单管理应用 - 部署指南

> ⚠️ **重要**：自动构建脚本位于 `scripts/build_docker.py`（本目录下），每次 CI/CD 或完整重新部署时使用。

```bash
# 进入项目目录
cd family_health_record_app

# 执行构建
python scripts/build_docker.py --all
```

## 部署方式

### 方式一：使用预构建镜像（推荐）

预构建镜像已包含所有依赖，启动速度快。

#### 1. 准备环境
```bash
# 克隆代码
git clone <your-repo-url> /path/to/health-record-app
cd /path/to/health-record-app

# 配置环境变量
cd infra
cat > .env << EOF
SILICONFLOW_API_KEY=your_api_key_here
EOF
```

#### 2. 启动服务
```bash
cd infra
docker compose up -d
```

#### 3. 访问应用
- 前端: http://localhost:3001
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- MinIO 控制台: http://localhost:9001 (minioadmin/minioadmin)

### 方式二：从源码构建

#### 1. 构建基础镜像
```bash
cd infra
docker build -f Dockerfile.base -t qa-base:latest .
```

#### 2. 启动服务（自动安装依赖）
```bash
docker compose up -d --build
```

## Docker 镜像说明

| 镜像 | 大小 | 说明 |
|:---|:---|:---|
| qa-base | 448MB | 基础镜像 (Python 3.11 + Node.js 20 + 国内源) |
| qa-backend | 617MB | 后端镜像 (含 Python 依赖) |
| infra-frontend | ~500MB | 前端镜像 (含 Node.js 依赖) |

### 镜像特性
- ✅ **国内源加速**: 阿里云 apt/pip 源、淘宝 npm 源
- ✅ **依赖预装**: 首次启动无需等待依赖安装
- ✅ **无 volume 挂载**: 避免 Windows 文件挂载问题

## 服务架构

```
┌─────────────────────────────────────────────────┐
│                   Docker Network                 │
├─────────────┬─────────────┬─────────────────────┤
│  Frontend   │   Backend   │  Infrastructure     │
│  Port 3001  │  Port 8000  │                     │
│  Next.js    │  FastAPI    │  ┌───────────────┐  │
│             │             │  │ PostgreSQL 16 │  │
│             │             │  │ (内部 5432)   │  │
│             │             │  └───────────────┘  │
│             │             │  ┌───────────────┐  │
│             │             │  │    MinIO      │  │
│             │             │  │  Port 9000/1  │  │
│             │             │  └───────────────┘  │
└─────────────┴─────────────┴─────────────────────┘
```

## 服务说明

| 服务 | 镜像 | 端口 | 说明 |
|:---|:---|:---|:---|
| db | postgres:16-alpine | 内部 | PostgreSQL 数据库 |
| minio | minio/minio | 9000/9001 | 对象存储 |
| backend | qa-backend | 8000 | FastAPI 后端 API |
| frontend | infra-frontend | 3001 | Next.js 前端 |

## 数据持久化

数据存储在 Docker volumes 中:
- `postgres_data` - 数据库文件
- `minio_data` - 上传的文件

### 备份数据
```bash
# 备份 PostgreSQL
docker exec health-record-db pg_dump -U health_record health_record > backup.sql

# 备份 MinIO
docker cp health-record-minio:/data ./minio_backup
```

### 恢复数据
```bash
# 恢复 PostgreSQL
cat backup.sql | docker exec -i health-record-db psql -U health_record health_record
```

## 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
docker compose logs -f backend  # 只看后端日志

# 重启服务
docker compose restart backend

# 停止服务
docker compose down

# 停止并删除数据
docker compose down -v

# 进入容器调试
docker exec -it health-record-backend bash
docker exec -it health-record-frontend bash
```

## 测试

### 运行后端测试
```bash
docker exec health-record-backend python -m pytest tests/ -v
```

### 运行 E2E 测试
```bash
# 确保服务已启动
docker compose up -d

# 运行 Playwright 测试
cd family_health_record_app/frontend
npx playwright test
```

### 使用 QA Pipeline 运行测试
```bash
# 全量测试
python scripts/qa_pipeline.py --mode docker

# 仅跑 E2E 核心链路
python scripts/qa_pipeline.py --mode e2e --tags critical

# 仅跑冒烟测试
python scripts/qa_pipeline.py --mode e2e --tags smoke

# 仅跑 UT
python scripts/qa_pipeline.py --mode local --no-ut

# 排除 UX 测试
python scripts/qa_pipeline.py --mode e2e --exclude "ux"
```

详细说明参考 [`docs/QA_PIPELINE_GUIDE.md`](./docs/QA_PIPELINE_GUIDE.md)

### 移动端 APK 构建
- 详细文档：[移动端构建问题汇总](../mobile_app/docs/BUILD_ISSUES.md)
- **Release APK**（推荐用于真机/模拟器部署）：`mobile_app/android/app/build/outputs/apk/release/app-release.apk`
- **Debug APK**（需 Metro 服务器）：`mobile_app/android/app/build/outputs/apk/debug/app-debug.apk`

### 健康检查
```bash
# 检查后端
curl http://localhost:8000/api/v1/health

# 检查前端
curl http://localhost:3001
```

## 故障排除

### 1. 端口被占用
```bash
# 查看端口占用
netstat -ano | findstr :8000
netstat -ano | findstr :3001

# 修改 docker-compose.yml 中的端口映射
ports:
  - "8080:8000"  # 改用 8080
```

### 2. 容器启动失败
```bash
# 查看详细日志
docker compose logs backend --tail 100

# 重新构建
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 3. 数据库连接失败
```bash
# 检查 PostgreSQL 状态
docker exec health-record-db pg_isready -U health_record

# 检查环境变量
docker exec health-record-backend env | grep DATABASE_URL
```

### 4. 前端构建失败
```bash
# 重新构建前端镜像
cd infra
docker compose build frontend --no-cache
docker compose up -d --force-recreate frontend
```

## 生产环境部署建议

1. **修改默认密码**: 更改 PostgreSQL 和 MinIO 的默认密码
2. **启用 HTTPS**: 使用 Nginx 反向代理 + SSL 证书
3. **数据备份**: 定期备份 volumes
4. **监控**: 添加健康检查和日志收集
5. **资源限制**: 在 docker-compose.yml 中添加资源限制
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

## 更新日志

### v1.4.0 (2026-04-02)
- ✅ OCR 提示词管理器重构 (prompt_manager.py)
- ✅ 审核页面图片预览功能
- ✅ 修复前端 Docker 部署问题（移除 volume 挂载）
- ✅ 新增测试代码检查脚本
- ✅ 更新 AGENTS.md 规范（第7、8条红线）
- ✅ 修正 Dockerfile 配置文件名
