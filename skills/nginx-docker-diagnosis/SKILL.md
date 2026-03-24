---
name: nginx-docker-diagnosis
version: v1.0.0
last_updated: 2026-03-24
description: 诊断 Docker 环境下 Nginx Web 页面无法访问的问题（404、白屏、资源加载失败等）。当用户报告 Docker 部署的 Nginx Web 服务出现页面打不开、404 Not Found、CSS/JS 加载失败、白屏等问题时触发。通过逐步收集配置文件和日志，系统化地定位根因并给出修复建议。
---

# Nginx Docker 诊断工作流

诊断 Docker + Nginx Web 部署问题的交互式流程。按顺序执行以下阶段，每个阶段可能需要向用户索取信息。

## 诊断流程总览

```
阶段 1: 收集症状 → 阶段 2: 收集配置 → 阶段 3: 端口与路由分析
→ 阶段 4: 容器内文件验证 → 阶段 5: 根因定位 → 阶段 6: 给出修复方案
```

## 阶段 1: 收集症状

向用户确认以下信息（如未提供）：
- 具体的报错 URL（完整 URL，包含端口和路径）
- HTTP 状态码（404 / 502 / 503 / 白屏等）
- 浏览器 Network 面板截图（如有白屏情况）

关键：记录每个报错 URL 的**端口**和**路径**，这两个信息决定后续分析方向。

## 阶段 2: 收集配置文件

向用户索取以下文件内容：

1. **docker-compose.yml**（Nginx 容器定义）— 关注：
   - `ports` 映射（宿主机端口 → 容器端口）
   - `volumes` 挂载（配置文件和静态文件）
   - `networks`（与后端服务的网络连通性）

2. **nginx.conf**（主配置）— 关注：
   - `upstream` 定义（后端服务名称和端口）

3. **default.conf / server 配置**（站点配置）— 关注：
   - `listen` 端口
   - `root` / `alias` 静态文件路径
   - `location` 路由规则
   - `proxy_pass` 后端代理目标
   - `try_files` 回退规则

4. **后端服务的 docker-compose**（如有多个 yml 文件）— 关注：
   - 后端服务的端口映射（是否直接暴露了端口绕过 Nginx）
   - 服务名称是否与 `upstream` 定义一致

## 阶段 3: 端口与路由分析

拿到配置后，对每个报错 URL 执行分析：

### 3.1 端口分析
```
报错 URL 的端口 → 这个端口属于哪个容器？
  ├─ 是 Nginx 容器的映射端口 → 进入路由分析（3.2）
  └─ 是后端服务直接暴露的端口 → ⚠️ 请求绕过了 Nginx
      └─ 根因：用户通过错误端口访问，应使用 Nginx 端口
```

### 3.2 路由分析
```
URL 路径 → 匹配 default.conf 的哪个 location？
  ├─ 匹配到 proxy_pass → 检查 upstream 是否可达
  ├─ 匹配到 alias/root → 检查容器内文件路径（阶段 4）
  └─ 无匹配 → 落入默认 location / 的 try_files → 可能 404
```

### 3.3 常见端口问题检查清单
- [ ] 后端服务是否直接暴露端口（绕过 Nginx）
- [ ] Nginx `listen` 端口与 docker-compose `ports` 映射是否一致
- [ ] upstream 服务名称与 docker-compose 中的 `container_name` / `service_name` 是否一致

## 阶段 4: 容器内文件验证

向用户索取以下命令的输出（这是定位根因的关键步骤）：

```bash
# 1. 检查静态文件根目录结构（注意区分文件和目录）
docker exec <nginx容器名> ls -la <root路径>/

# 2. 检查各子应用目录
docker exec <nginx容器名> ls -la <root路径>/<子应用>/

# 3. 搜索特定资源文件的实际位置
docker exec <nginx容器名> find / -name "<报错文件名>" 2>/dev/null

# 4. 如果发现异常文件（预期是目录但实际是文件），查看其内容
docker exec <nginx容器名> cat <异常文件路径>

# 5. 验证 Nginx 配置是否正确加载
docker exec <nginx容器名> nginx -T

# 6. 检查 Nginx 错误日志
docker exec <nginx容器名> tail -50 /var/log/nginx/error.log
```

### 关键检查项
- [ ] `root`/`alias` 指向的路径在容器内是否存在
- [ ] 路径是**目录**还是**文件**（macOS 构建镜像常出现 `._` 元数据文件问题）
- [ ] 前端打包文件（`umi.*.css`, `umi.*.js`, `index.html` 等）是否存在
- [ ] 各子应用是否放在了正确的目录下

## 阶段 5: 根因定位

基于阶段 3-4 的分析结果，对照以下常见根因模式：

### 模式 A: 端口直连后端
**症状**：通过后端服务端口访问，返回 404
**根因**：请求绕过了 Nginx，直接到后端 API 服务（不提供静态文件）
**修复**：通过 Nginx 端口访问

### 模式 B: 静态文件目录不存在或结构异常
**症状**：通过 Nginx 端口访问，静态资源 404
**根因**：Docker 镜像构建时未正确 COPY 前端文件，或 macOS `._` 文件污染
**特征**：`ls -la` 显示预期的目录实际是小文件（`com.apple.provenance`）
**修复**：重新构建镜像，macOS 环境设置 `COPYFILE_DISABLE=1`

### 模式 C: 前端 publicPath 与 Nginx 路由不匹配
**症状**：`index.html` 能返回，但 CSS/JS 404，页面白屏
**检查**：查看 `index.html` 中引用的资源路径是否与 Nginx location 配置一致
**特征**：`<title>` 或资源路径暴露应用身份错误（如 AGC 目录下的 index.html 标题是 AVC）
**根因**：前端打包配置的 `publicPath` / `base` 路径错误，或文件放错了目录
**修复**：修正前端构建配置或将文件移到正确目录

### 模式 D: Nginx location 配置错误
**症状**：路径不匹配任何 location
**典型问题**：
- `alias` 路径末尾缺少 `/`
- `location /app` 与 `location /app/` 的区别
- `try_files` 回退路径不正确
**修复**：修正 Nginx location 配置

### 模式 E: volumes 挂载覆盖镜像内文件
**症状**：镜像内有文件，但容器内为空
**根因**：docker-compose volumes 挂载了空目录，覆盖了镜像内的文件
**修复**：移除多余的 volume 挂载或确保挂载源有内容

### 模式 F: 网络不通
**症状**：502 Bad Gateway
**根因**：Nginx 与后端服务不在同一 Docker network
**修复**：确保 docker-compose 中 networks 配置正确

## 阶段 6: 输出诊断报告

以结构化格式输出：
1. **症状总结**：列出报错的 URL 和状态码
2. **根因**：明确指出属于哪个模式（A-F）
3. **证据**：引用具体的配置行号或命令输出
4. **修复方案**：给出具体操作步骤
5. **预防建议**：如何避免再次出现同类问题
