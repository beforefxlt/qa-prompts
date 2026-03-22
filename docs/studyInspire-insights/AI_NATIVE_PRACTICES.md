# AI Native 时代研发与测试实践复盘 (AI-Native Dev & Test Practices)

本文档基于 `StudyInspire` 项目的实战经验，总结了在 AI 辅助编程时代（Copilot/Agent）下，研发与测试策略的演进与最佳实践。供后续项目规划与复盘参考。

---

## 1. 核心认知转变：为什么 "Day 1 CI" 至关重要？

### 传统观念 vs. AI 时代现状
*   **传统观念**：MVP 阶段代码变动剧烈，维护自动化测试成本高，应推迟引入 CI/CD。
*   **AI 时代现状**：
    *   **代码生成速度极快**：AI 可能在几秒钟内重构整个模块，带来意想不到的副作用（如 Prompt 微调导致 LaTeX 格式崩溃）。
    *   **测试生成成本极低**：代码变了，使用 AI 同步更新测试脚本的边际成本趋近于零。
    *   **结论**：**代码生成越快，越需要自动化守门员。CI/CD 应在 Day 1 引入，作为 AI 的“安全围栏”。**

### 实践教训
我们在 `StudyInspire` 早期未引入 CI，导致 LaTeX 渲染问题反复出现（Regression）。引入 `scripts/utils/run_tests.py` 后，任何 prompt 的修改都能被立即验证，极大地提升了重构信心。

---

## 2. 测试策略的演进 (Testing Strategy Evolution)

在 AI 辅助下，测试经理的关注点应从“编写用例”转向“定义验收标准”和“维护黄金数据集”。

### 2.1 分层测试策略
1.  **Level 1: 语法与编译 (Build & Lint)**
    *   **AI 作用**：确保生成的代码符合语法规范，无低级错误。
    *   **CI 动作**：Push 即触发 `go build` / `npm build`。

2.  **Level 2: 黄金路径接口测试 (Golden Path API Test)**
    *   **核心策略**：不要追求 100% 覆盖率，只测 1-2 个核心业务死穴。
    *   **实战案例**：`scripts/regression_test.py` 仅使用两张典型图片作为输入，却守住了 OCR -> 判卷 -> 格式化 的全链路。
    *   **优势**：接口契约比 UI 稳定，且 AI 容易生成针对接口的校验脚本。

3.  **Level 3: E2E 与 UI 测试**
    *   **引入时机**：产品 UI 稳定后（Ver 1.0+）。
    *   **AI 作用**：使用 AI 解析 HTML 结构，自动生成 Playwright/Selenium 脚本。

### 2.2 测试资产的转变
*   **过去**：Excel 测试用例表格。
*   **现在**：
    *   **Prompt 即规约**：System Prompt 中的约束（如“必须返回标准 JSON”）即是需求文档。
    *   **数据即用例**：积累一套“黄金数据集”（Corner Case 图片集），作为 AI 模型的“考卷”。
    *   **契约即护栏**：通过 JSON Schema (`api_schema.py`) 定义前后端契约，自动校验数据结构变更。

---

## 3. "AI 幻觉" 防御体系 (Anti-Hallucination Engineering)

AI 并非确定的函数，它会产生幻觉。工程上必须建立多层防御。

### Layer 1: Prompt 约束 (事前)
*   使用 Few-shot（少样本）提示，明确告知 AI “什么是对的”。
*   *案例*：在 Prompt 中展示正确的 LaTeX 格式 `\( ... \)`，防止输出 `$$ ... $$`。

### Layer 2: 后端清洗 (Code-level Sanitizer) (事后)
*   不信任 AI 的输出，必须有确定性的代码逻辑进行清洗。
*   *案例*：`internal/utils/sanitizer.go` 递归剥离多余的符号，作为兜底。

### Layer 3: 概率性回归测试 (监控)
*   AI 的错误可能是概率性的。测试脚本应支持多次迭代（Iterations）。
*   *案例*：`scripts/analyze_prob.py` 连续请求 10 次，统计格式错误的概率。

---

## 4. 给测试经理的行动指南 (Actionable Advice)

1.  **环境先行**：项目第一周就通过 Docker 或 Shell 脚本（`setup_ubuntu.sh`）固化运行环境和 Key 配置。环境问题是 AI 开发最大的干扰源。
2.  **文档即指令**：编写高质量的 Markdown 文档。AI 读取文档后，能更准确地生成代码和测试。文档不再是摆设，而是 Agent 的上下文。
3.  **拥抱不确定性**：接受 AI 输出的不稳定性，通过工程手段（重试、清洗、校验）将不确定性收敛为确定性。

---

> **总结**：在 AI Native 时代，CI/CD 是基础设施，测试代码是业务代码的伴生体。测试人员应进化为“AI 训练师”和“验收标准制定者”。

### 延伸阅读与深度复盘
关于项目整体目录治理、CI/CD 竞态逻辑、多 Provider 编排带来的详细架构教训，请参阅：
- [项目复盘与架构教训](PROJECT_RETROSPECTIVE.md)

---
*总结：AI 带来的提速必须由更严谨的工程结构来对冲，否则代码生成的“快”会变成坏账堆积的“灾”。*
