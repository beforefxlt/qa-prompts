# StudyInspire 测试架构文档

> 从测试架构师视角，系统阐述本项目的 CI/CD 架构、技术栈、测试分层策略及设计理念。

---

## 1. 架构概览

### 1.1 CI/CD 流水线架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           StudyInspire CI/CD Pipeline                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │   Git Push   │───▶│ GitHub       │───▶│   Build &    │───▶│  Deploy   │ │
│  │              │    │ Actions (CI) │    │   Test       │    │  (CD)     │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └───────────┘ │
│         │                   │                    │                   │       │
│         │                   │                    │                   │       │
│         ▼                   ▼                    ▼                   ▼       │
│    本地代码            自动触发            单元测试 + E2E        手动触发    │
│    提交变更            云端执行            构建 Artifact         服务器部署  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 层级 | 技术选型 | 选型理由 |
|------|----------|----------|
| **CI 平台** | GitHub Actions | 免费、与 GitHub 深度集成、配置即代码 |
| **构建语言** | Go 1.21 | 高性能、跨平台编译、单一二进制部署 |
| **前端框架** | Vanilla JS + Tailwind CSS | 轻量、无构建依赖、适合嵌入式场景 |
| **E2E 测试** | Playwright | 跨浏览器、强大的自动等待、调试体验好 |
| **接口测试** | Python + Requests | 灵活、丰富的断言库、易于编写 |
| **部署方式** | SSH + SCP | 简单可靠、无额外依赖、适合小型项目 |

### 1.3 环境矩阵

| 环境 | 用途 | Mock 策略 | API Key |
|------|------|-----------|---------|
| **本地开发** | 日常开发调试 | 禁止 Mock | 从 .env 读取 |
| **本地测试** | 回归验证 | 禁止 Mock | 从 .env 读取 |
| **CI 环境** | 自动化验证 | 允许 Mock | 从 Secrets 读取 |
| **生产环境** | 真实服务 | 禁止 Mock | 编译时注入 |

---

## 2. 测试分层策略

### 2.1 测试金字塔

```
                    ┌─────────────────┐
                    │    E2E Tests    │  ← L4: 用户场景 + 路径完整性
                    │   (Playwright)  │     执行: 慢
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │    Contract Tests       │  ← L3: API 契约校验 (Schema)
                │    Integration Tests    │  ← L2: 接口回归相关
                │      (Python API)       │     执行: 中
                └────────────┬────────────┘
                             │
           ┌─────────────────┴─────────────────┐
           │          Unit Tests               │  ← L1: 单元测试
           │ (Go Testing + Jest / JSDOM)       │     执行: 快
           └───────────────────────────────────┘
```

### 2.2 各层测试详解

#### L1: 单元测试 (Unit Tests)

**工具**: Go `testing` 包, Jest + JSDOM (前端)

**覆盖范围**:
| 测试文件 | 测试内容 | Mock 策略 |
|----------|----------|-----------|
| `main_test.go` | 路由配置、中间件 | 允许 Mock |
| `web_test.go` | 静态资源完整性 | 无需 Mock |
| `config_test.go` | 配置解析逻辑 | 允许 Mock |
| `sanitizer_test.go` | LaTeX 清洗逻辑 | 无需 Mock |
| `client_test.go` | 底层 API 行为 (重试、兜底) | 劫持/协议仿真 |
| `service_test.go` | 业务降级 (Fallback) 路径 | 注入 Mock 配置 |
| `app.test.js` | **[前端]** DOM 渲染、Timeout 处理、错误 UI 降级 | 允许 Mock (Fetch) |
| `fault_injection_test.go` | 级联顺位验证 (SF -> NV -> ZP) | 隔离流量监控 |

**设计理念**:
- **快速反馈**：总耗时应控制在秒级，是 CI/CD 的第一道生命线。
- **三位一体覆盖**：每个 API 调用必须覆盖 Happy Path、Logic Error 和 Transport Error。
- **协议仿真**：使用 `httptest` 进行 URL 劫持，在不触碰真实网络的情况下验证底层解析逻辑。
- **防御性要求**：Wait-Check-Access 模式的实操检验。

**执行命令**:
```bash
go test -v ./...
```

#### L2: 接口回归测试 (Integration Tests)

**工具**: Python + `test_utils.APIClient`

**设计理念**:
- **DRY 原则**: 统一通过 `APIClient` 调用，不再于脚本中重复定义 URL/Key。
- **真实 API**: 验证端到端链路。
- **自动报告**: 生成 `regression.json` 细节报告。

**执行命令**:
```bash
# 启动测试服务进程
.\scripts\start.ps1

# 使用统一测试入口运行回归 (不再单独使用旧脚本)
python scripts/utils/run_tests.py
```

#### L3: 契约测试 (Contract Testing - 新增)

**工具**: Python + `jsonschema` + `api_schema.py`

**设计理念**:
- **单一事实来源**: 在 `api_schema.py` 中定义 API 契约，与 Go 模型严格对应。
- **结构校验**: 验证 JSON 字段类型、必填项、结构层级。
- **语义惩罚**: 额外检查禁止的 LaTeX 命令（如 `\div`）和业务规则（如练习题数量）。

**执行命令**:
```bash
python scripts/test/contract_test.py
```

#### L4: 格式审计测试 (Stability Checks)

**工具**: Python + `test_utils.Assertions`

**测试目的**: 验证 AI 回复的稳定性（如禁止字符、多余包裹等）。

**执行命令**:
```bash
python scripts/test/analyze_prob.py
```

#### L5: E2E 场景测试 (E2E Tests)

**工具**: Playwright + Python/Node.js

**执行命令**:
```bash
# 模拟用户真实拍照过程
python tests/e2e/test_real_scenario.py

# 验证页面加载与路径完整性
node scripts/test/e2e_web_test.js
```

---

## 3. 深度思考：单元测试（UT）的灵魂与金字塔哲学

### 3.1 金字塔的底层经济学
测试金字塔的核心在于**成本与置信度的平衡**。
- **置信度递增**：E2E 测试最接近用户体验，但其维护成本极高，且无法定位精密逻辑。
- **稳定性递减**：底层 UT 是最稳定的，它不随网络波动、模型随机性或 UI 调整而失效。
- **结论**：如果一个逻辑可以在底层用 UT 测清楚（如 Latex 转换），绝不推到 L2 或 L3 去测。

### 3.2 纯函数的穷举美学
对于 `sanitizer` 等工具类，我们推崇**“穷举测试”**。
- **思想**：将函数视为数学映射（Inputs -> Outputs）。由于不涉及外部状态，测试成本接近零。
- **目标**：100% 覆盖所有的正则表达式分支、边界字符和嵌套深度。

### 3.3 协议仿真的边界：不穿墙的测试
很多开发者认为 API 调用无法做 UT。我们的实践证明：**通过 `httptest` 进行“协议仿真”是关键**。
- **劫持而非 Mock**：我们不 Mock 一个“模拟对象”，而是劫持底层的 HTTP 通讯。这迫使我们的生产代码必须正确解析每一个 Header 和 Body 字段。
- **不穿墙原则**：UT 绝对不能产生真实的 HTTP 出站请求。任何“穿透墙壁”的测试都属于 L2 集成测试。

### 3.4 UT 作为“可复用文档”
单元测试应被视为一份**“永不过时的活文档”**：
- 它告诉新成员：系统的报错边界在哪里？重试次数是多少？
- 它为重构提供了“防弹衣”：只要 UT 通过，底层的结构性修改就不会引发逻辑碎裂。

---

## 4. CI/CD 流水线详解

### 3.1 GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: StudyInspire CI/CD

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Set up Go 1.21
      - Set up Node.js 20
      - Install dependencies
      - Run Unit Tests (Mock mode)
      - Run Integration Tests
      - Build Linux Binary
      - Upload Build Artifact
```

### 3.2 流水线阶段

| 阶段 | 触发条件 | 执行内容 | 失败处理 |
|------|----------|----------|----------|
| **Checkout** | 自动 | 拉取代码 | 重试 |
| **Setup** | 自动 | 安装 Go/Node/Python | 失败终止 |
| **Unit Tests** | 自动 | `go test ./...` | 失败终止 |
| **Integration Tests** | 自动 | 回归 + E2E | 失败终止 |
| **Build** | 测试通过 | 交叉编译 | 失败终止 |
| **Artifact** | 构建成功 | 上传 Release 包 | - |

---

## 4. 测试工程化治理 (Test Engineering)

### 4.1 基础工具层 (Test Utilities)
位于 `scripts/test/test_utils.py`，为所有测试提供支持。

| 模块 | 职责 |
|------|------|
| **APIClient** | 统一请求封装、鉴权注入、自动重试、NO_PROXY 设置 |
| **Fixtures** | 测试资源 (图片) 统一管理、Base64 自动转换 |
| **Assertions** | 业务特定断言 (如 `no_forbidden_latex`) |
| **Reporting** | 统一度量标准 (ReportEntry/TestSuiteReport) |

### 4.2 报告聚合 (Reporting Aggregation)
本项目实现了跨语言、全层级的报告聚合：
1. **子报告生成**: 接口测试产生各自的 `regression.json`, `contract.json` 等。
2. **顶层聚合**: `run_tests.py` 执行完成后，汇总所有 JSON 生成统一的 `test-reports/summary.json`。

---

## 5. 设计理念与原则

### 5.1 核心原则

| 原则 | 说明 | 实践 |
|------|------|------|
| **DRY 原则** | 测试代码也是代码，禁止硬编码重复逻辑 | 建立 `test_utils.py` 工具层 |
| **快速反馈** | 问题越早发现，修复成本越低 | L1 单元测试毫秒级执行 |
| **分层防御** | 不同层级验证不同维度 | 金字塔测试策略 (L1-L5) |
| **契约优先** | 接口契约是前后端协作的基准 | L3 契约测试 (Schema 强校验) |
| **可观测性** | 测试结果必须数据化、可视化 | 统一 JSON 聚合报告 |

### 4.2 AI 时代的测试挑战

| 挑战 | 解决方案 |
|------|----------|
| **输出不确定性** | 概率分析 + Sanitizer 后处理 |
| **API 依赖** | Mock 模式 + 重试机制 |
| **网络不稳定** | 超时配置 + 降级策略 |
| **环境配置** | 编译时注入 + .env 文件 |

### 4.3 测试数据管理

```
tests/
├── fixtures/           # 测试图片
│   ├── regression_1.png
│   ├── regression_2.png
│   └── demo_question.jpg
├── e2e/               # E2E 测试脚本
│   └── test_real_scenario.py
└── maestro/           # Android UI 测试
    └── config.yaml
```

---

## 5. 质量门禁

### 5.1 本地门禁

| 门禁 | 触发时机 | 检查内容 |
|------|----------|----------|
| **pre-push hook** | git push 前 | 单元测试通过 |
| **本地回归** | 提交 PR 前 | 全量测试通过 |

### 5.2 CI 门禁

| 门禁 | 触发时机 | 检查内容 |
|------|----------|----------|
| **Unit Tests** | 每次 push | 单元测试通过 |
| **Integration Tests** | 每次 push | 回归测试通过 |
| **Build** | 测试通过后 | 编译成功 |

### 5.3 发布门禁

| 门禁 | 触发时机 | 检查内容 |
|------|----------|----------|
| **CI 通过** | 部署前 | GitHub Actions 绿色 |
| **服务健康** | 部署后 | /ping 接口响应 |

---

## 6. 监控与告警

### 6.1 服务监控

| 指标 | 检查方式 | 告警阈值 |
|------|----------|----------|
| **服务存活** | /ping 接口 | 无响应 > 30s |
| **API 延迟** | 日志分析 | P99 > 10s |
| **错误率** | 日志分析 | > 5% |

### 6.2 日志管理

```bash
# 服务器日志位置
/root/release/server.log

# 查看最近日志
tail -f /root/release/server.log
```

---

## 7. 持续改进

### 7.1 测试覆盖率目标

| 指标 | 当前 | 目标 |
|------|------|------|
| 单元测试覆盖率 | 60% | 80% |
| 接口测试覆盖率 | 70% | 90% |
| E2E 测试覆盖率 | 50% | 70% |

### 7.2 技术债务

| 项目 | 优先级 | 计划 |
|------|--------|------|
| 增加 API 性能测试 | P1 | 下个迭代 |
| 增加安全测试 | P1 | 下个迭代 |
| 增加兼容性测试 | P2 | 待规划 |

---

## 9. 附录

### 8.1 测试命令速查

| 操作 | 命令 |
|------|------|
| **启动调试服务 (推荐 -Background 模式)** | `.\scripts\start.ps1 -Background` |
| **杀除残留进程 (释放8080)** | `Stop-Process -Name "go" -Force -ErrorAction SilentlyContinue` |
| **查询探活可用的 API 模型列表** | `python scripts/utils/list_models.py --provider nvidia` |
| 统一回归与契约测试入口 (含自动流程清理) | `python scripts/utils/run_tests.py` |
| 格式分析 | `python scripts/test/analyze_prob.py` |
| Web E2E (Node) | `node scripts/test/e2e_web_test.js` |
| 场景 E2E (Python) | `python tests/e2e/test_real_scenario.py` |

### 8.2 相关文档

| 文档 | 路径 |
|------|------|
| 契约测试指南 | `docs/CONTRACT_TESTING_GUIDE.md` |
| 工程化治理指南 | `docs/TEST_ENGINEERING_GOVERNANCE.md` |
| 测试经验总结 | `docs/TEST_LESSONS_LEARNED.md` |
| 开发与测试守则 | `docs/DEVELOPMENT_TESTING_RULES.md` |
| 开发日志 | `docs/development_log.md` |

---

## 10. 实战反思：从 Panic 中学习 (Case Study)

### 9.1 事件复盘：500 Panic 的诞生
在一次针对 `nvidia.Client` 的重构中，由于在检查 `error` 之前访问了可能为 `nil` 的 `Response` 对象，导致后端服务发生 `nil pointer dereference` 崩溃（Panic）。

**失败原因分析**：
- **测试盲区**：现有的单元测试（L1）主要 Mock 了 Service 层。虽然这能加快速度，但也导致了底层的“肮脏细节”（HTTP 状态处理、空指针风险）被完全屏蔽在安全网之外。
- **调试代码泄露**：为了排查 401 报错而临时注入的 `fmt.Println(resp.Status())` 在极端网络/配置报错下（resp 为空）触发了崩溃。

### 9.2 防御性测试模型 (Defensive Testing Model)

为了防止此类问题再次发生，我们引入以下测试知识总结：

#### A. 颗粒度下沉 (Granular Mocking)
不要只在接口（Interface）层 Mock。
- **方法**：针对底层 `Client`，模拟传输层错误（如 DNS 失败、连接超时）。
- **原则**：测试必须要能运行到“访问 `resp` 之前的所有逻辑分支”。

#### B. 强制性错误路径 (Mandatory Error Paths)
定义“所有 API 调用必须具备”的三个 UT 用例：
1. **Happy Path**：返回 200 及预期数据。
2. **Logic Error**：返回 4xx/5xx 等有状态码的错误。
3. **Transport Error**：返回 `nil response`，验证代码是否会 Panic。

#### C. 防御性编程：Wait-Check-Access 模式
代码层面必须遵守的“黄金法则”：
1. **Wait**：发起异步或外部请求。
2. **Check**：第一时间检查 `err`。
3. **Guard**：访问对象前确认指针非空（`if resp != nil`）。
4. **Access**：最后才读取数据字段。

---

## 11. 2026-02-24 专项治理反思：弹性级联与解析鲁棒性

### 11.1 架构顺位的“单一事实来源” (SSOT)
**事件**：在重构过程中发现，代码实现与 PRD 描述的降级顺位（Aliyun 还是 SiliconFlow 为主力）出现偏离。
**教训**：
- **一致性审计**：在调整生产顺位前，必须先更新 PRD 文档。文档不是过期的附件，而是代码行为的“法律依据”。
- **测试用例先行**：通过编写 `fault_injection_test.go` 来强制锚定级联顺序（SF -> NV -> ZP），使架构设计变为“编译时校验”的可测试资产。

### 11.2 处理 AI 脏数据的“解耦哲学”
**事件**：AI 频繁在 JSON 中包裹 Markdown 围栏或输出非法的特殊转义字符（如 `\÷`），导致 Unmarshal 崩溃。
**解决方案**：
- **JSON 提纯 (Pure Extraction)**：不再依赖正则暴力截断，而是使用“最外层括号定位”算法，支持从复杂的 AI 废话中精准剥离 JSON。
- **职责解耦**：将 LaTeX 符号转换与 JSON 解析解构。必须先确保 JSON 物理结构正确（Unmarshal），再进行业务层面的文本清洗（Sanitize）。
- **教训**：解析管道必须对 AI 输出风格的波动做出“零信任”假设。

### 11.3 故障仿真：变“被动感知”为“主动防御”
**动作**：引入了精准的流量隔离测试。
**价值**：
- 传统的测试只测“成功”，故障仿真强迫在本地模拟“主力节点持续 401/503”的情况。
- 这种“主动扎针”的测试策略，使我们能在不触碰生产环境的情况下，验证跨 Provider 降级的时间戳抖动和重试间隔是否符合预期。

---

*文档版本: 1.2*
*最后更新: 2026-02-24*
*反思记录人: Antigravity*
