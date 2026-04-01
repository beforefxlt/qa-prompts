# 架构规范：AI 增强可观测性 (AI-Centric Observability)

Version: v1.0.0
Date: 2026-04-01

## 1. 背景与目标
为了加速 AI Agent 驱动的自动化测试、诊断与持续交付，项目必须提供透明且结构化的“运行流水”。观测层不仅服务于运维人员，更是 AI 定位故障、防止逻辑偏差的核心信源。

## 2. 后端观测标准 (Backend Trace)

### 2.1 全局请求追踪 (API-TRACE)
所有后端路由必须由 `main.py` 的全局中间件拦截，并输出以下格式的实时日志：
`[API-TRACE] {METHOD} {PATH} -> {STATUS} ({DURATION}s)`

- **目的**：允许 AI 通过终端日志即时判断路径匹配情况。
- **强制性**：所有新增 Router 不得覆盖或关闭此中间件。

## 3. 前端流量监控 (Frontend Flow)

### 3.1 流量标记逻辑 (AI-FLOW)
API 客户端 (`client.ts`) 必须在 `fetch` 周期内输出带有特定标记的前缀日志：
- `>> [AI-FLOW] Requesting: ...`
- `<< [AI-FLOW] Response: ...`
- `!! [AI-FLOW] Error for ...`

- **目的**：使前端自动化测试工具（如 Playwright）能直接从控制台提取 API 交互详情，实现故障的秒级定位。

## 4. AI 测试准入要求
1. **Hydration 防护**：所有交互式组件必须使用 `isMounted` 守卫，严禁 SSR 期间渲染动态数据。
2. **错误降级**：所有 API 异常必须被 UI 捕获并展示友好的错误信息，禁止直接抛出 500。
3. **日志关联**：开发新功能时，必须确保其数据流向在 Console 与 Stdout 均有可观测的足迹。

---
> [!TIP]
> 遵循此规范将使故障修复效率提升 300% 以上。
