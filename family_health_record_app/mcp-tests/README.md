# MCP 测试工具箱 (Test Utilities)

本目录包含了用于“家庭健康记录管理应用”前端功能验证的所有自动化测试资产。

## 🧪 核心脚本说明

### 1. 数据库重置 (Database Reset)
*   **位置**: `../../backend/rebuild_db.py`
*   **用途**: 清空数据库中所有成员与记录，并根据最新 Schema 重新生成纯净环境。
*   **执行**: `python ../backend/rebuild_db.py`

### 2. 批量数据灌入 (Data Seeding)
*   **位置**: `./seed_data.py`
*   **用途**: 为特定测试成员（如“指标测试成员”）快速注入历史趋势数据（身高、体重、血糖），用于验证 Dashboard 图表的渲染与指标切换逻辑。
*   **特性**: 自动创建虚拟检查单记录并关联 3 个月内的观测值。
*   **执行**: `python seed_data.py`

### 3. API 基础数据准备 (API Prepper)
*   **位置**: `./prepare_data.py`
*   **用途**: 通过 HTTP API 接口创建空的测试成员，用于验证“首页空状态引导”和“新用户创建”流程。
*   **执行**: `python prepare_data.py`

### 4. 自动化测试驱动 (Test Runners)
*   **JavaScript Runner**: `./mcp-runner.js` (使用 MCP SDK 连接调试端口执行用例)
*   **Wait & Run**: `./run-tests.js` (包含等待服务就绪逻辑的执行器)

## 🛠️ 使用场景

### 场景 A：端到端全量回归
1.  执行 `python ../backend/rebuild_db.py` (环境归零)。
2.  执行 `python seed_data.py` (注入趋势数据)。
3.  在支持 MCP 的 Agent 中运行 `TC-MCP-001` ~ `008`。

### 场景 B：前端性能测试
1.  确保负载均衡或后端响应稳定。
2.  执行 `node mcp-runner.js --case=TC-MCP-008`。

## 📂 结果输出
*   **截图**: 测试过程中的 UI 截图将自动保存至 `./screenshots/` 文件夹（或根据 AI Agent 环境输出到 artifacts）。

---
> **最后维护时间**: 2026-04-01 13:29
