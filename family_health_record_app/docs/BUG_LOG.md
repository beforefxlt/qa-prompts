# 缺陷与诊断排查记录 (Bug Log)

## 记录日期: 2026-03-31
### [BUG-001] AI Agent 初始技术栈偏离 (Node.js vs FastAPI)
- **现象**: Agent 在初期自动生成了 `Node.js + Prisma + SQLite` 架构，严重偏离了正式文档规定的 `FastAPI + PostgreSQL`。
- **根因**: 工作流脚本 (`v1.0.0`) 缺失了“强制宣读真实架构/规格文档” (Pre-flight Check) 步骤，导致 Agent 在 `/tmp/` 生成并采信了草案配置。
- **修复措施**: 
  - 升级工作流至 `v1.1.0`，新增 Step 0 强制读取 `docs/specs/` 中资产。
  - 清理废弃的 node 代码 (`backend_deprecated`, `src/`)。
  - 重新基于 FastAPI 与 SQLAlchemy 实现四层数据架构与 OCR/规则引擎核心。

### [BUG-002] Tailwind CSS 类未生效 (Bare HTML)
- **现象**: 子代理 (Sub-01) 首次渲染页面截图显示，玻璃拟态样式完全失效，页面堆叠展示，呈现典型的“无样式 (Bare HTML)”效果。
- **根因**: `tailwind.config.js` 的 `content` 数组未配置正确的源码扫描路径，导致样式编译器没有捕获和生成 `src/app` 目录下的 Tailwind Class。
- **修复措施**: 在 Tailwind 配置文件中追加 `"./src/**/*.{js,ts,jsx,tsx,mdx}"`，重启服务器后恢复渲染，子代理二次验收通过。

### [BUG-003] Subagent “平行写”能力受限
- **现象**: 尝试使浏览器子代理直接执行终端创建目录及写文件命令，结果报错或静默降级为串行操作。
- **根因**: `browser_subagent` 能力限定为浏览器域（点击、截图、DOM 扫描），它缺少文件执行权限。
- **修复措施**: 梳理并引入了主/子代理的“读写分流框架”：由主代理完成 `py/tsx/md` 的全量开发，然后委派单功能子代理执行“端到端验证”与“视觉审计 (Audit)”。
