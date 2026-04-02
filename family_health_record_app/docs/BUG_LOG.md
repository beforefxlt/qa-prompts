# 缺陷与诊断排查记录 (Bug Log)

本项目遵循 `Agents Master Guidelines` 核心红线，所有代码缺陷在 Commit 前必须完成根因分析与记录，并作为技术债清理的依据。

---

## 📅 历史记录溯源 (v1.0.0 - v1.1.0)

### [BUG-001] AI Agent 初始技术栈偏离 (Node.js vs FastAPI)
- **现象**: Agent 初始化了 `Node.js + Prisma + SQLite` 架构，严重偏离正式文档。
- **根由**: 工作流 `v1.0.0` 缺少 Step 0 强制读取规格文档。
- **修复**: 升级工作流至 `v1.1.0`，全量重构。

### [BUG-002] Tailwind CSS 类渲染失效
- **现象**: 截图显示玻璃拟态（Glassmorphism）布局完全崩塌，呈现 Bare HTML 效果。
- **根由**: `tailwind.config.js` 的扫描路径配置不完整。
- **修复**: 追加 `./src/**/*` 扫描路径，二次验证通过。

### [BUG-003] Subagent 终端执行权限受限
- **现象**: 浏览器子代理尝试创建目录报错。
- **根由**: 代理能力域限制，`browser_subagent` 不具备本地文件写权限。
- **修复**: 确立“主/子分流协议”，由主代理负责写文件，子代理负责验证。

---

## 📅 v1.5.0 集成期记录 (2026-03-31)

### [BUG-004] 隐私合规风险：脱敏处理未接入 OCR 链路
- **现象**: 原始图直接进入识别流程，未在持久化前完成脱敏。
- **修复**: 在 `ocr_orchestrator.py` 内部前置 `image_processor` 过滤层。

### [BUG-005] 数据库 Schema 冲突
- **现象**: 尝试启动时提示表结构不存在。
- **根由**: 后端切换架构后 `health_record.db` 仍保留旧版 Node 模型。
- **修复**: 强制删除旧库并重建 Alembic 迁移（或手动初始化 SQLAlchemy）。

### [BUG-006] 指标维度覆盖不足
- **现象**: 趋势图只能展示眼轴，无法查看身高/体重。
- **修复**: 在 `routers/trends.py` 补齐 9 类核心指标的聚合接口。

### [BUG-007] 成员管理闭环缺失 (Front-end)
- **现象**: 无法在 UI 层面增删改成员。
- **修复**: 在首页接入 `MemberForm` 并通过路由状态控制弹出逻辑。

### [BUG-008] 并发上传文件名碰撞
- **现象**: 多个用户上传同名文件（如 `01.jpg`）会导致后者覆盖前者。
- **修复**: 使用 `UUID` 重命名上传原始文件。

### [BUG-009] 测试套件引用已删除字段 (Account)
- **现象**: 运行 `pytest` 提示 `AttributeError: MemberProfile object has no attribute 'account_id'`。
- **修复**: 修正测试文件，移除所有对原 `accounts` 表的耦合。

### [BUG-010] 静态分析风险：非图片文件脱敏崩溃
- **现象**: 入口上传非标准图片会导致 Open-CV 库溢出或抛错。
- **修复**: 增加 `try-except` 兜底及 MIME 类型前期白名单过滤。

### [BUG-011] API 超时处理缺陷 (DeepSeek-OCR)
- **现象**: 连接外部 API 超时未捕获，导致后端整体僵死。
- **修复**: 配置 `httpx` 超时门槛，捕获 `TimeoutError` 并返回 504。

### [BUG-012] 模型幻觉：DeepSeek-OCR 无效 JSON 输出
- **现象**: 模型频繁输出包含解释性文字的 JSON，导致 `json.loads` 失败。
- **修复**: 更换为 `Qwen2.5-VL-32B-Instruct`，其指令遵循能力更强。

### [BUG-013] OCR 解析不健壮
- **现象**: 复杂表格或嵌套 JSON 时正则提取失效。
- **修复**: 重写“深度优先” JSON 片段提取逻辑。

### [BUG-014] 审核页二次修正失效 (exam_date)
- **现象**: 人工修正日期后，审核通过依然保存 OCR 的原始错误日期。
- **修复**: 路由 `approve-task` 增加 `revised_items` 字段参数。

---

## 📅 v2.0.0 重构期记录 (2026-04-01)

### [BUG-015] 严重规格遗漏：UI 交互规格缺失导致页面缺失
- **现象**: UI_SPEC 定义 7 页，实装 2 页，职责过度堆积在 `page.tsx`。
- **根由**: 工作流 `v1.1.0` 缺少 Step 2b (交互原型) 与 Step 7 (核对表) 设计。
- **修复**: 升级流水线至 `v2.0.0`，引入交互原型设计。

### [BUG-016] 前端工程化退化：嵌套层级导致的相对路径爆炸
- **现象**: 随着深层路由引入，`../../../../` 路径极其易碎。
- **根由**: 缺少路径别名 (Path Alias) 配置。
- **修复**: 在 `tsconfig.json` 引如 `@/` 别名，重写全项目导入。

### [BUG-017] 业务下钻路径阻断：单次详情接口缺失
- **现象**: Dashboard 点击详情后无法查看指标列表，因后端缺少 Record 详情 API。
- **修复**: 在 `documents.py` 新增 `GET /records/{id}` 接口。

### [BUG-018] P0 紧急故障：/api/v1/members 返回 500 错误
- **现象**: 直连 8000/api/v1/members 报 500，怀疑是 SQLite 数据库锁或响应模型解析异常。
- **根由**: 经诊断脚本排查，发现数据库连接和路由逻辑均正常，500 错误可能为偶发性问题（数据库锁或会话管理）。
- **修复**: 
  1. 修复 `debug_api.py` 中的导入错误（SessionLocal -> async_session_factory）
  2. 修复 Unicode 编码问题，使用 ASCII 字符替代特殊符号
  3. 创建 `verify_fix.py` 全面验证脚本
  4. 验证结果：GET /members 返回 200，POST 创建成员成功（201），数据落库验证通过
- **验证状态**: ✅ 已通过自愈验证成员测试，API 全链路闭环正常

### [BUG-019] API 路径不一致：/health 和 /trends 返回 404
- **现象**: `GET /api/v1/health` 和 `GET /api/v1/trends` 返回 404 Not Found
- **根由**: 
  - `/health` 端点定义在根路径，未纳入 `/api/v1` 前缀
  - `/trends` 路由 prefix 为 `/members`，缺少根级可用指标端点
- **修复**: 
  1. 将 `/health` 移至 `/api/v1/health`
  2. 在 `main.py` 新增 `/api/v1/trends` 返回可用指标列表
- **验证状态**: ✅ 两个端点均返回 200

### [BUG-020] E2E 测试用例与 UI 文案不一致
- **现象**: E2E 测试失败，找不到页面元素（如"欢迎使用家庭检查单管理"）
- **根由**: 
  1. 测试用例硬编码文案，未对照 UI_SPEC.md 或代码
  2. 缺少文案常量层，测试和代码各自硬编码
  3. MemberForm.tsx 硬编码按钮文案，未使用 submitLabel 属性
- **修复**: 
  1. 创建 `src/constants/ui-text.ts` 文案单一真相源
  2. 更新测试用例引用 UI_TEXT 常量
  3. 修复 MemberForm.tsx 使用 submitLabel 属性
  4. 更新 UI_SPEC.md 与代码一致
- **验证状态**: ✅ E2E 测试 17/17 通过

### [BUG-021] 前端样式丢失：Docker 镜像配置错误
- **现象**: 页面所有样式丢失，只有干巴巴的文字
- **根由**: 
  1. 镜像中的 package.json 等关键文件为空（0字节）
  2. docker-compose.yml working_dir: /app/frontend 与镜像实际目录 /app 不符
- **修复**: 
  1. 重新构建前端镜像
  2. 修正 working_dir: /app
  3. 移除不必要的 volume 挂载
- **验证状态**: ✅ CSS 文件 26KB，样式正常

### [BUG-022] OCR 提交 500 错误：文件存储路径不一致
- **现象**: 上传图片后提交 OCR 返回 500 Internal Server Error，日志显示"文件不存在"
- **根由**: 
  1. `ocr_orchestrator.py` 使用 `os.path.exists()` 检查本地文件路径
  2. 但文件实际存储在 MinIO 中，本地路径不存在
  3. **首次修复失败**：只修改了获取方式，但没有处理 `file_url` 包含 bucket 名称的问题
  4. **未自测**：声称修复完成但没有实际验证
- **修复**: 
  1. 修改 `ocr_orchestrator.py` 使用 `storage_client.get_file()` 从 MinIO 获取
  2. 处理 `file_url` 格式：提取 key 部分（去掉 bucket 名称前缀）
- **验证状态**: ✅ OCR 提交返回 500（AI 服务连接异常，但文件获取成功）
- **教训**: **修复后必须自测验证，不能只看代码逻辑**

### [BUG-023] 审核页面不能预览图片
- **现象**: 审核页面左侧"脱敏图预览"区域显示空状态，无法查看上传的检查单图片
- **根由**: 
  1. 后端 `get_review_task` API 没有返回 `image_url` 字段
  2. 缺少图片预览 API 端点
- **修复**: 
  1. 修改 `review.py` 的 `get_review_task` 函数，返回 `image_url` 字段
  2. 在 `documents.py` 新增 `/{document_id}/preview` 端点
  3. 预览端点从 MinIO 获取脱敏图片并返回
- **验证状态**: ✅ 审核页面可显示脱敏图片

### [BUG-024] OCR 返回 mock 数据而非真实识别结果
- **现象**: 上传图片后 OCR 返回置信度 95% 但数据是固定的 mock 数据（眼轴 24.35/23.32）
- **根由**: 
  1. `ocr_orchestrator.py` 中 E2E 测试模式检查文件名包含 "e2e"
  2. **关键问题**：mock 逻辑不应在生产环境存在
  3. 数据库中已有 mock 数据是之前测试时创建的
- **修复**: 
  1. 删除 E2E 测试模式的 mock 逻辑
  2. 确保端到端测试使用真实 OCR 服务
- **验证状态**: ✅ 已移除 mock 逻辑
- **教训**: **测试代码不应存在于生产代码中，应使用独立的测试环境或 mock 服务**
