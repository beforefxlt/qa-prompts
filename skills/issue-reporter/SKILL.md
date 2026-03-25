---
name: issue-reporter
version: v1.0.1
last_updated: 2026-03-25
description: 为软件测试场景生成结构化问题单。当用户希望报告缺陷、问题或测试结果，或已经提供复现步骤与实际结果并需要正式问题单时触发。
---

# 问题单生成 (Issue Reporting Skill)

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

## 输出要求 (Output Format)

1. **严格读取模板**：你的输出格式必须完全参照项目根目录下的 `templates/defect-report-template.md` 的规范。
2. 依据用户提供的信息，准确填充模板中的各项字段（包括新老问题分类、增量操作、测试用例链接等）。
