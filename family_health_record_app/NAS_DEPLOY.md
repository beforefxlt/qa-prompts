# 家庭检查单管理应用 - NAS 部署指南

> 适用于飞牛OS (fnOS) + Intel N100 平台
> 版本: v2.4.0 | 更新日期: 2026-04-03

---

## 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                        飞牛OS (fnOS)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Docker 容器环境                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │  │
│  │  │ Frontend│  │ Backend  │  │  Infrastructure   │  │  │
│  │  │  :3001  │  │  :8000  │  │  ┌─────────────┐  │  │  │
│  │  │ Next.js │  │ FastAPI │  │  │ PostgreSQL   │  │  │  │
│  │  │         │  │         │  │  │   :5432     │  │  │  │
│  │  └──────────┘  └──────────┘  │  └─────────────┘  │  │  │
│  │                             │  ┌─────────────┐  │  │  │
│  │                             │  │   MinIO     │  │  │  │
│  │                             │  │  :9000/9001 │  │  │  │
│  │                             │  └─────────────┘  │  │  │
│  │                             └────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────┴───────────────────────────┐  │
│  │              存储卷 (Docker Volume)                   │  │
│  │  ┌─────────────────┐   ┌─────────────────────────┐   │  │
│  │  │  postgres_data  │   │      minio_data        │   │  │
│  │  │    (数据持久化)   │   │     (检查单图片存储)    │   │  │
│  │  └─────────────────┘   └─────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚠️ 重要：镜像版本管理

- **禁止使用 `latest` 标签**：每次部署必须使用明确版本号（如 `v2.4.0`）
- **版本号来源**：使用 git tag 或 `git describe --tags --always --dirty`
- **好处**：
  - 明确知道运行的是哪个版本
  - 方便回滚到特定版本
  - 避免自动更新导致不可预期的问题

### 版本号示例

```bash
# 获取当前版本号
VERSION=$(git describe --tags --always --dirty)
# 输出类似：v2.4.0-5-g0a78312 或 v2.4.0

# 或手动指定
VERSION=v2.4.0
```

---

## 部署方式对比

| 方式 | 适用场景 | 说明 |
|------|----------|------|
| **方式一：本地构建→NAS** | 网络带宽有限 | 本地构建镜像，导出 tar 传输到 NAS |
| **方式二：NAS 直构建** | 网络带宽充裕 | NAS 直接从代码构建镜像 |

**推荐方式一**：Intel N100 性能较强但构建耗时长，本地构建更省时

---

## 方式一：本地构建 + 传输到 NAS（推荐）

### 步骤 1.1 本地准备

```bash
# 1. 克隆代码到本地电脑
git clone <your-repo-url> /path/family-health-record
cd /path/family-health-record

# 2. 获取版本号（也可自定义）
VERSION=$(git describe --tags --always --dirty)
echo "Building version: $VERSION"

# 3. 进入 infra 目录
cd infra

# 4. 构建后端镜像（使用版本标签）
docker build -t qa-backend:${VERSION} ../backend

# 5. 构建前端镜像（使用版本标签）
docker build -t infra-frontend:${VERSION} ../frontend

# 6. 导出镜像为 tar 文件
docker save -o qa-backend-${VERSION}.tar qa-backend:${VERSION}
docker save -o infra-frontend-${VERSION}.tar infra-frontend:${VERSION}
```

### 步骤 1.2 传输到 NAS

选择以下任一方式：

#### 方式 A：通过 SCP 传输
```bash
scp qa-backend-${VERSION}.tar infra-frontend-${VERSION}.tar nas_user@<nas-ip>:/volume1/docker/
```

#### 方式 B：通过飞牛OS 文件管理器
1. 访问飞牛OS GUI → 文件管理器
2. 上传 `qa-backend-${VERSION}.tar` 和 `infra-frontend-${VERSION}.tar` 到 `/volume1/docker/`

### 步骤 1.3 NAS 上导入镜像

```bash
# 1. SSH 登录 NAS
ssh nas_user@<nas-ip>

# 2. 进入镜像目录
cd /volume1/docker

# 3. 加载镜像
docker load -i qa-backend-${VERSION}.tar
docker load -i infra-frontend-${VERSION}.tar

# 4. 验证镜像
docker images | grep -E "qa-backend|infra-frontend"
```

### 步骤 1.4 配置与启动

```bash
# 1. 创建工作目录
mkdir -p /volume1/docker/family-health-record
cp -r /path/to/infra /volume1/docker/family-health-record/

# 2. 配置环境变量
cd /volume1/docker/family-health-record/infra
cat > .env << 'EOF'
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
EOF

# 3. 更新镜像版本（重要！）
# 编辑 docker-compose.yml，将 image: qa-backend:latest 改为 image: qa-backend:${VERSION}
sed -i "s/qa-backend:latest/qa-backend:${VERSION}/g" docker-compose.yml
sed -i "s/infra-frontend:latest/infra-frontend:${VERSION}/g" docker-compose.yml

# 4. 启动服务
docker compose up -d

# 5. 验证服务状态
docker compose ps
```

---

## 方式二：NAS 直接构建

### 步骤 2.1 克隆代码

```bash
# SSH 登录 NAS
ssh nas_user@<nas-ip>

# 克隆代码
git clone <your-repo-url> /volume1/docker/family-health-record
cd /volume1/docker/family-health-record
```

### 步骤 2.2 构建镜像

```bash
cd infra

# 获取版本号
VERSION=$(git describe --tags --always --dirty)

# 构建后端镜像（约 5-10 分钟）
docker build -t qa-backend:${VERSION} ../backend

# 构建前端镜像（约 3-5 分钟）
docker build -t infra-frontend:${VERSION} ../frontend
```

### 步骤 2.3 配置与启动

```bash
# 配置环境变量
cat > .env << 'EOF'
SILICONFLOW_API_KEY=your_api_key_here
EOF

# 启动服务
docker compose up -d
```

---

## 访问方式

| 服务 | 局域网地址 | 说明 |
|------|------------|------|
| 前端 | `http://<nas-ip>:3001` | 健康检查单管理界面 |
| 后端 API | `http://<nas-ip>:8000` | API 端点 |
| API 文档 | `http://<nas-ip>:8000/docs` | Swagger 文档 |
| MinIO 控制台 | `http://<nas-ip>:9001` | 文件存储管理 |
| MinIO 账号 | `minioadmin` / `minioadmin` | 首次登录需修改 |

---

## 外网访问配置

### 方案一：飞牛OS 反向代理（推荐）

1. 登录飞牛OS 管理后台
2. 打开「系统设置」→「反向代理」
3. 添加规则：
   - 名称：`health-app`
   - 协议：`http`
   - 外部域名：`<your-domain>.com`（或使用 DDNS）
   - 外部端口：`80`
   - 目标：`localhost:3001`

### 方案二：DDNS + 端口映射

```bash
# 在路由器上映射端口
TCP 3001 → NAS:3001  (前端)
TCP 8000 → NAS:8000  (后端 API)
```

### 方案三：Nginx Proxy Manager

如需 HTTPS，可部署 Nginx Proxy Manager：

```yaml
# docker-compose.yml 添加
nginx-proxy:
  image: jc21/nginx-proxy-manager
  ports:
    - "80:80"
    - "443:443"
    - "81:81"
  volumes:
    - ./nginx-proxy-data:/data
```

---

## 数据备份与恢复

### 备份数据

```bash
# 1. 备份 PostgreSQL 数据库
docker exec health-record-db pg_dump -U health_record health_record > /volume1/backup/health_record_$(date +%Y%m%d).sql

# 2. 备份 MinIO 文件
docker cp health-record-minio:/data /volume1/backup/minio_data_$(date +%Y%m%d)
```

### 恢复数据

```bash
# 1. 恢复 PostgreSQL
cat /volume1/backup/health_record_20260403.sql | docker exec -i health-record-db psql -U health_record health_record

# 2. 恢复 MinIO（需先停止容器）
docker compose down
docker volume rm infra_minio_data
# 重新挂载备份的数据目录
docker compose up -d
```

---

## 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
docker compose logs -f backend    # 只看后端
docker compose logs -f frontend   # 只看前端

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 停止并删除数据（谨慎！）
docker compose down -v

# 进入容器调试
docker exec -it health-record-backend bash
docker exec -it health-record-frontend bash

# 健康检查
curl http://localhost:8000/api/v1/health
curl http://localhost:3001
```

---

## 资源规划（Intel N100）

| 容器 | CPU 建议 | 内存建议 | 说明 |
|------|----------|----------|------|
| PostgreSQL | 0.5 核 | 512MB | 数据存储 |
| MinIO | 0.5 核 | 256MB | 对象存储 |
| Backend | 1 核 | 1GB | API 服务 |
| Frontend | 0.5 核 | 512MB | Web 服务 |
| **总计** | **~2.5 核** | **~2GB** | Intel N100 完全胜任 |

---

## 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像（如有代码变更）
docker compose build --no-cache

# 3. 重启服务
docker compose up -d

# 4. 运行数据库迁移（如需要）
docker exec health-record-backend python -m alembic upgrade head
```

---

## 故障排除

### 1. 端口被占用

```bash
# 查看端口占用
ss -tlnp | grep -E "3001|8000|9000|9001"

# 修改 docker-compose.yml 端口映射
ports:
  - "8080:8000"  # 改用其他端口
```

### 2. 服务启动失败

```bash
# 查看详细日志
docker compose logs --tail=100

# 检查容器状态
docker compose ps -a
```

### 3. 数据库连接失败

```bash
# 检查 PostgreSQL
docker exec health-record-db pg_isready -U health_record

# 检查环境变量
docker exec health-record-backend env | grep DATABASE_URL
```

### 4. 前端无法访问后端

```bash
# 检查后端是否运行
docker compose ps backend

# 检查前端环境变量
docker exec health-record-frontend env | grep API
```

---

## 安全建议

1. **修改默认密码**：首次登录 MinIO 后修改 `minioadmin` 密码
2. **配置防火墙**：仅允许内网访问 3001/8000 端口
3. **启用 HTTPS**：使用反向代理 + SSL 证书
4. **定期备份**：建议每周自动备份
5. **日志监控**：配置日志收集便于问题排查

---

## 技术支持

- 后端 API 文档：`http://<nas-ip>:8000/docs`
- 健康检查：`http://<nas-ip>:8000/api/v1/health`
- 日志查看：`docker compose logs -f`

---

## 更新日志

### v2.4.0 (2026-04-03)
- 新增血红蛋白、LDL、血糖、糖化血红蛋白手工录入支持
- 新增趋势页指标切换
- 优化 E2E 测试配置
