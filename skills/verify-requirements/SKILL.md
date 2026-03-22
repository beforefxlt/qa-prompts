---
name: verify-requirements
description: Verify if software requirements are implemented by analyzing the codebase. Use when the user asks to check if a specific feature, requirement, or document section is implemented in the code.
metadata:
  short-description: Verify requirement implementation
---

# Verify Requirements Skill

This skill helps you verify if specific software requirements are implemented in the codebase. It emphasizes **strict compliance**, **evidence-based verification**, and **precise reporting**.

## Workflow

### Phase 1: Requirement Extraction (Crucial)
**Before searching code, you MUST establish the checklist.**
1.  **Verbatim Extraction**: Copy the user's requirements *word-for-word* into a numbered list.
    *   *Rule*: If the user provides a list of 11 items, your checklist MUST have 11 items. Do not merge them.
    *   *Formatting*: Assign a unique ID to each item if not provided (e.g., [5.6.1.1], [5.6.1.2]).
2.  **Decomposition**: If a single requirement contains multiple distinct technical assertions (e.g., "Must support TCP AND UDP"), verify both parts.

### Phase 2: Targeted Code Search
Perform targeted searches based on the *type* of requirement:

*   **Business Logic / Control**:
    *   Look in `service/` or `app/`.
    *   Search for "check", "limit", "lock", "alarm" keywords.
*   **Data Storage / History**:
    *   Look in `dao/` (Data Access Objects) or `model/` (Struct definitions).
    *   Search for "History", "Record", "Save", "DB".
*   **Interface / HMI / Permission**:
    *   Look in `router/` (API definitions) or `handler/`.
    *   Search for "Register", "API", "User", "Auth".
*   **Communication / Protocol**:
    *   Look in `pb/` (Protocol Buffers) or `protocol/`.
    *   Search for "IEC", "104", "Modbus", "Send", "Receive".

**Advanced Tip: IEC 61850 Logical Nodes**
For power systems, a "Device" often aggregates multiple Logical Nodes (LNs):
*   **Control**: `DPCS`, `DBAT`.
*   **Measurements**: `MMXU` (look here for Voltage, Current, Power).
*   **Metering**: `MMTR`.
*   **Status**: `GGIO`.

### Phase 3: Evidence-Based Verification
For each item in your checklist, determine its status based on **code evidence**:

| Status | Symbol | Definition |
| :--- | :--- | :--- |
| **Confirmed** | ✅ | Code explicitly implements the logic. You can point to the File + Function. |
| **Partial** | ⚠️ | Logic exists but is incomplete, disabled, or relies on frontend/manual steps not in backend. |
| **Missing** | ❌ | No code found. Search for specific keywords returned 0 results. |
| **Uncertain** | ❓ | Logic is too complex to verify statically, or depends on external systems (OS/Gateway). |

### Phase 4: Standardized Reporting
Generate a report using the **Strict Compliance Table** format.

#### Format Template:
```markdown
### Section [X.Y] [Title] ([N] Items)

| ID | Requirement | Status | Evidence / Gap Analysis |
| :--- | :--- | :--- | :--- |
| 5.1.1 | [Requirement Text] | ✅ | `file.go`: `FunctionName` checks condition X. |
| 5.1.2 | [Requirement Text] | ❌ | **Missing**. Search for "Keyword" returned no results in `service/`. |
| 5.1.3 | [Requirement Text] | ⚠️ | **Partial**. Logic exists in `period_check.go` for locking so-and-so, but **no event record** is written to DB. |
```

#### Risk Summary
After the tables, summarize critical gaps:
*   **Missing Safety Features**: (e.g., No emergency lock).
*   **Missing Persistence**: (e.g., Logs not saved).
*   **Missing Interfaces**: (e.g., No User Mgmt API).

## Tips
-   **Do not guess**. If you can't find it, mark it ❓/❌ and explain what you searched for.
-   **Check for TODOs**. Sometimes requirements are present as comments only.
-   **Verify "Negative" Logic**. If a requirement says "Do NOT do X", check if the code *avoids* doing X (e.g., `if !remote { return }`).
