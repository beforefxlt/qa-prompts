# 家庭检查单管理应用 - 部署指南

## NAS 部署步骤

### 1. 准备环境
```bash
# 克隆代码到 NAS
git clone <your-repo-url> /path/to/health-record-app
cd /path/to/health-record-app

# 复制环境变量配置
cp backend/.env.example backend/.env
# 编辑 .env 文件，填入真实的 SILICONFLOW_API_KEY
```

### 2. 配置 Docker 代理 (如需要)
```bash
# 在 NAS 上创建 Docker daemon 配置
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "proxies": {
    "http-proxy": "http://127.0.0.1:10800",
    "https-proxy": "http://127.0.0.1:10800"
  }
}
EOF

# 重启 Docker
sudo systemctl restart docker
```

### 3. 构建并启动
```bash
# 使用 docker-compose 构建并启动所有服务
cd infra
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 4. 访问应用
- 前端: http://<NAS-IP>:3000
- 后端 API: http://<NAS-IP>:8000
- MinIO 控制台: http://<NAS-IP>:9001 (minioadmin/minioadmin)

## 服务说明

| 服务 | 端口 | 说明 |
|:---|:---|:---|
| backend | 8000 | FastAPI 后端 API |
| frontend | 3000 | Next.js 前端 |
| minio | 9000/9001 | 对象存储 (可选) |
| postgres | 5432 | 数据库 (可选, 默认用 SQLite) |

## 数据持久化

数据存储在 Docker volumes 中:
- `postgres_data/` - 数据库文件
- `minio_data/` - 上传的文件

备份时只需备份这些 volumes。

## 故障排除

### 常见问题

1. **构建失败**: 检查代理设置是否正确
2. **无法连接数据库**: 检查 .env 中的 DATABASE_URL 配置
3. **OCR 不工作**: 检查 SILICONFLOW_API_KEY 是否正确

### 查看日志
```bash
docker-compose logs backend
docker-compose logs frontend
```
