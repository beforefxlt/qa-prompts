---
name: issue-reporter
description: Generate a structured issue report for software testing. Use this skill when the user wants to report a bug, issue, or test result, or when they provide test steps and results and need a formal report.
---

# Issue Reporting Skill (问题单生成)

This skill generates a structured issue report in Chinese based on the provided details.

## Instructions

1.  **Gather Information**: Analyze the user's input to extract issue details. If critical information is missing, ask the user, but prefer generating a draft first.
    *   **Critical Fields**: Title, Description, Steps to Reproduce, Expected Result, Actual Result.
2.  **Format Output**: strictly follow the template below.
3.  **Language**: The *descriptive content* (Steps, Description, Analysis) must be in Chinese (`zh-CN`).
    - **Translate**: User narratives, test steps, explanations, and analysis.
    - **Do NOT Translate**: Technical logs, error messages, code snippets, variable names, and file paths. Keep these in their original language (usually English).
4.  **Log Citations**: When mentioning or citing logs (especially in "Actual Result" or "Analysis"), **ALWAYS include the original timestamp** from the log entry. If applicable, also include **Trace ID, Request ID, or Device ID** to help locate logs in distributed systems. This is critical for developers to locate the logs.
5.  **问题描述 vs 预期结果**: "问题描述"只概括当前异常现象（做了什么、看到了什么），不描述预期行为。"预期行为"由"预期结果"字段专门承载，避免内容重复。

## Report Template

```markdown
# 问题单 (Issue Report)

### 1. 基本信息
- **标题**: [简明扼要的问题描述]
- **软件版本**: [版本号/Commit hash/分支名]
- **测试环境**: [如：QA / Staging / 生产环境；Docker / 裸机部署；操作系统及版本]
- **设备/网络信息**: [如适用，填写硬件型号、网络环境等]
- **发生时间**: [日期和时间]

### 2. 问题详情
- **问题描述**: [纯测试现象描述。只概括当前观察到的异常：操作了什么、看到了什么。不应包含预期行为（由"预期结果"承载），也不应包含代码层面的分析（由"分析与证据"承载）。]
- **复现概率**: [必现 (100%), 偶现 (约 %), 一次性]
- **严重程度**: [致命, 严重, 一般, 轻微]
- **优先级**: [高, 中, 低]

### 3. 前置条件
- [复现此问题所需的环境状态、账号权限、数据条件等。例如：设备已激活且在线、Redis 缓存中存在历史数据、MQTT Broker 可达。]

### 4. 测试步骤
1. [步骤 1]
2. [步骤 2]
3. [步骤 3]
...

### 5. 结果
- **预期结果**: [应该发生什么]
- **实际结果**: [实际发生了什么]

### 6. 分析与证据
- **测试人员分析**: [对根本原因的初步分析, 行为观察, 代码走读结论]
- **日志存储路径**: [相关日志的路径]
- **关联标识**: [如适用，提供 Trace ID / Request ID / Device ID 等，便于在分布式系统中定位]
- **截图/附件**: [证据描述或链接]
```
