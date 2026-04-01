# 📘 指南：自动化测试交付流水线 (`test-lifecycle`)

本指南介绍如何利用整合后的 AI Agent 工作流（Workflow）自动完成从**需求分析**到**可追溯测试架构设计**、**标准测试用例输出**并经 **Reviewer Agent** 复核收口的全生命周期交付。

---

## 1. 什么是 `test-lifecycle`？

`test-lifecycle` 不是一个单一的提示词，而是一套**智能 SOP (标准作业程序)**。它将五个原子化的 AI 专家技能串联在一起，确保测试设计不漏掉任何深度（如 P3/P5 维度），同时在策略展开前先固定测试骨架，并在正式落盘前完成一次最小扰动复核：

1.  **需求审计 (`requirement-reviewer`)**：负责挑刺，找出逻辑漏洞。
2.  **可追溯测试架构 (`traceability-test-architecture`)**：负责固定 TC 编号体系、`traceability.yaml`、测试分层与统一审计口径。
3.  **全景策略规划 (`test-strategy-planner`)**：负责在既定骨架上建立 P1-P5 全维度矩阵。
4.  **标准用例工厂 (`test-case-factory`)**：负责执行，产出符合 TCS 规约的标准测试用例集 (TCC)。
5.  **最终复核代理 (`reviewer-agent`)**：负责统一检查 QA 工作流编排、测试资产完整性、文档同步性与技能治理合规性；若环境可用，优先结合 `vibe-tools repo` 执行 “Minimalist Refactor” 式复核。

---

## 2. 如何触发？

在与 AI 对话中输入以下指令（Slash Command）：

```bash
/test-lifecycle [你的需求描述或文档路径]
```

---

## 3. 标准操作流程 (5 步流)

### 第一步：需求审计与风险对齐
AI 会自动分析您的需求是否存在歧义或盲区。
- **用户操作**：阅读输出的列表，根据提示补充缺失的业务逻辑。
- **关键指令**：回复 **“继续”**。

### 第二步：可追溯测试架构建模
AI 会先调用 `traceability-test-architecture`，把后续测试活动共用的骨架固定下来。
- **AI 产物**：TC 编号规则、`traceability.yaml` 初始结构、测试分层建议、基于 Python 的分层编排脚本骨架、E2E 编号要求、统一审计和 TDD 门禁建议。
- **用户操作**：核对这套骨架是否符合项目规模和治理要求。
- **关键指令**：回复 **“按这个骨架继续”** 或指出需要裁剪的层级。

### 第三步：全景策略确认 (P1-P5)
AI 会根据 P1（基础）、P2（数据）、P3（基础设施故障）、P4（边界）、P5（交付视角）五个层面输出策略大纲，并与上一步的追溯骨架保持一致。
- **用户操作**：核对策略覆盖面是否符合交付标准。
- **关键指令**：回复 **“生成用例”**。

### 第四步：正式用例挂载
AI 会生成详细的测试用例并自动追加到 `docs/test_specification.md`。
- **用户操作**：无，AI 自动完成文档落盘。
- **边界说明**：如果当前只是补字段级边界值，不应改走 `bva-boundary-value-analysis`；如果目标是储能/电力系统测试计划文档，不应改走 `test-plan-copilot` 替代本主链。

### 第五步：Reviewer Agent 收口复核
AI 会在最终交付前触发 `reviewer-agent` 做一次收口检查。
- **优先组合**：若本机已安装 `vibe-tools`，则优先使用 `vibe-tools repo` 读取整仓上下文，并要求模型只检查 QA 工作流、测试资产、用户文档与技能元数据的一致性。
- **额外约束**：`.repomix-output.txt`、临时仓库快照、调试索引等工具输出不属于正式资产，复核阶段应明确排除在交付和提交范围之外。
- **新增检查点**：必须核对 `traceability.yaml`、TC 编号、测试分层和统一审计口径是否已经和本轮规格、策略、用例同步。
- **用户操作**：阅读“必须修正 / 建议优化 / 可接受风险”摘要；若有阻断项，先修正再进入提交或交付动作。

若需查看这些收口动作背后的共性原则，可参阅：
`docs/user_guides/qa_cleanup_principles_zh.md`

---

## 4. 实战案例：以“OTA 升级功能”为例

### A. 初始输入
> **User**: `/test-lifecycle 我要上线一个基于 HTTP 的 OTA 升级功能，支持在检测完成后自动下载并重启。`

### B. AI 审计 (Step 1)
> **AI**: “审计发现：缺少 P3 风险处理（下载中磁盘写满了怎么办？）、缺少 P5 风险（OTA 包的 md5 校验在二进制打包后是否依然能执行？）。请问需要补充吗？”
>
> **User**: `“全加进去，按照这种异常流来测。”`

### C. 策略展示 (Step 2)
> **AI**: “已为您规划测试矩阵：P1 验证正常升级；P3 验证模拟断网重连；P5 验证交付后的分发包解压权限…… 确认无误请回复生成。”
>
> **User**: `“确认生成。”`

### D. 文档落盘与复核 (Step 3-4)
> **AI**: “已完成可追溯测试骨架和 7 个标准化 OTA 测试用例，相关内容已存入 `test_specification.md`。接下来将调用 `reviewer-agent` 做一次最终一致性复核。”
>
> **AI**: “复核结论：未发现阻断性问题；README 与用户指南已同步四段式流程，当前 P3 断网与 P4 交付验证用例可直接保留。”

---

## 5. 为什么这套流程更专业？

1.  **防过拟合 (Anti-Overfitting)**：每一步都保存中间文件 (`/tmp/`)，强制 AI 仅基于上一步的权威结论工作，隔离环境噪音。
2.  **强制 P5 交付视角**：不同于常规的“代码测试”，该流程强迫您思考最终交付给工厂的 Zip/Binary 制品在裸机上的真实体验。
3.  **标准化资产**：所有生成的用例均符合 TCS 规范并汇编为 TCC，可直接用于自动化回归。
4.  **提交前收口**：通过 `reviewer-agent` 增加一个轻量复核关口，避免工作流文档、README、`traceability.yaml` 与实际编排已经分叉。
5.  **边界稳定**：`test-code-simplifier`、`webapp-testing`、`test-driven-development` 等辅助 Skill 不默认插入主链，避免主工作流再次膨胀。

---

## 6. 工作流治理更新

截至 2026-03-25，本流程已与测试 Skill 治理方案完成对齐：

1. 主链固定为 `requirement-reviewer -> traceability-test-architecture -> test-strategy-planner -> test-case-factory -> reviewer-agent`
2. `bva-boundary-value-analysis`、`test-plan-copilot` 保留为专项工具，不替代主链步骤
3. `test-code-simplifier` 仅在用户明确要求时按需启用
4. 收口阶段继续优先校验工作流与文档口径一致性

---

> **💡 小贴士**：如果您发现 AI 在某一环不够聪明，您可以随时通过手动修改 `.agents/workflows/test-lifecycle.md` 文件来优化这条“流水线”的作业标准。
