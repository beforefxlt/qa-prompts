# v2.0.0 前端重构工作日志 (2026-04-01)

## 1. 重构背景与动因

在 v1.5.0 交付评审中发现，虽然核心业务逻辑（后端/OCR）已跑通，但前端呈现存在严重的“名实不符”：
- **职责过载**: `src/app/page.tsx` 膨胀至 32KB，包含了 5 个逻辑异构页面的实现，导致维护成本呈指数级增长。
- **规格遗漏**: 缺失 Dashboard、下钻详情及趋势分析等官方 UI 规格定义的 70% 页面。
- **业务孤岛**: 后端推出的视觉/生长发育仪表盘 API 无前端调用，属于开发浪费。

## 2. 核心技术决策

### 2.1 路由架构：从 Query-Param 到物理目录 (App Router)
- **决策**: 弃用 `?mode=edit` 这类状态模拟，强制迁移到标准的 Next.js App Router 物理目录结构。
- **理由**: 提高 URL 的语义化，并允许利用 Next.js 的页面级 `loading.tsx` 和缓存优化，为后续 P5 测试提供稳定的路径锚点。

### 2.2 组件策略：原子化提取
- **决策**: 从旧 `page.tsx` 中提取 `TrendChart` (图表封装)、`MemberForm` (表单封装) 和 `UploadOverlay` (上传图层)。
- **理由**: 确保 Dashboard、趋势页和单次详情页使用完全一致的 UI 语言（HSL 配色、玻璃拟态阴影），减少重复代码。

### 2.3 工程化：配置路径别名 `@/`
- **决策**: 修改 `tsconfig.json` 引入 `@/` 映射到 `src/`。
- **理由**: 解决嵌套路由深达 5 级（如 `records/[recordId]`）时相对路径极其易碎的问题，提升代码重构的容错率。

## 3. 遇到的技术挑战与修复

### 3.1 导入路径爆炸 (BUG-016)
重构初期，由于目录深度的剧烈变化，导致 80% 的页面无法通过编译。通过路径别名（Path Alias）统一了导入基准，消除了这一风险。

### 3.2 下钻路径缺失 (BUG-017)
在实现“单次详情页”时，发现后端虽然有 Document 列表，但没有“单次检查结果详情”的闭环接口。通过紧急在 `documents.py` 补充 `GET /records/{id}` 接口并预加载 `observations` 解决了此问题。

## 4. 验证与交付结论

本次重构通过了以下刚性核查：
- **页面完整性**: 对照 `UI_SPEC.md` 100% 覆盖。
- **类型安全**: `npx tsc --noEmit` 零错误。
- **资产一致性**: `BUG_LOG.md` 已完成 BUG-001 到 BUG-017 的全量治理。

---
**执行代理**: Antigravity
**交付版本**: v2.0.0
**时间**: 2026-04-01

---

# v2.7.0 移动端动态配置与脏数据治理 (2026-04-05)

## 1. 工作背景

v2.6.0 交付后，移动端 APK 存在硬编码 API 地址问题，真机无法访问；同时数据库积累了 53 条脏数据，影响用户体验和测试准确性。

## 2. 核心工作

### 2.1 移动端动态服务器配置
- 新增 `serverConfig.ts` — AsyncStorage 持久化服务器 Host
- 新增 `settings.tsx` — 服务器配置页面（输入/测试连接/保存）
- 重构 `client.ts` / `services/index.ts` — 移除硬编码 URL
- 修复 Metro 导入路径错误（`../../config` → `../config`）
- 修复 Android cleartext 拦截问题（`usesCleartextTraffic="true"`）

### 2.2 脏数据治理
- 新增 `admin.py` 路由器 — POST /api/v1/admin/reset 一键清空
- 新增 `check_dirty_data.py` — 部署前脏数据检查脚本
- 修复 E2E fixtures — cleanDatabase 扩展清理范围
- 修复 review-workflow.spec.ts — 改用 fixtures
- 集成到 qa_pipeline.py — 部署前自动检查
- 新增 AGENTS.md NP-08 — 测试后必须清理数据库

## 3. 技术挑战

### 3.1 Metro bundler 严格模式
APK 构建时 Metro 严格验证模块路径，与开发模式容错行为不同。`src/app/` 下导入 `src/config/` 应使用 `../config/` 而非 `../../config/`。

### 3.2 Android cleartext 静默拦截
Android 9+ 默认禁止 HTTP 明文流量，`fetch()` 被系统静默拦截，无日志输出。需在 `AndroidManifest.xml` 设置 `usesCleartextTraffic="true"`。

### 3.3 E2E auto fixture 不生效
Playwright 的 `auto: true` fixture 需要在测试中引用才会触发。`cleanDb` 定义了但没人调用，导致测试数据残留。

## 4. 验证结论
- 后端 pytest: 154 passed
- 移动端 Jest: 365 passed
- APK 构建: 57.4 MB (release)
- 数据库: 已清空
- 部署前检查: 脚本正常工作

---
**执行代理**: opencode
**交付版本**: v2.7.0
**时间**: 2026-04-05
