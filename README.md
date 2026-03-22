# 测试 Prompt 模板库 (QA Prompts Repository)

> 结构化 Prompt 模板库 — 消除自然语言的模糊性，确保不同经验水平的测试人员都能产出同等质量的 AI 输出

## 📋 目录

- [概述](#概述)
- [模板列表](#模板列表)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [集成方案](#集成方案)
- [贡献指南](#贡献指南)

---

## 概述

本仓库提供标准化的测试用例生成 Prompt 模板，帮助测试团队：

1. **消除模糊性** — 使用结构化 RCTF 架构 (Role-Context-Task-Constraint)
2. **保证一致性** — 不同经验水平的测试人员产出同等质量的 AI 输出
3. **提升效率** — 模板化调用，减少重复劳动
4. **持续迭代** — 版本化控制，基于效果评估持续优化

### 核心设计理念

```
┌─────────────────────────────────────────────────────────────┐
│                    结构化 Prompt 架构                        │
├─────────────────────────────────────────────────────────────┤
│  Role     → 定义 AI 角色 (如：高级软件测试架构师)              │
│  Context  → 提供业务背景和测试场景                           │
│  Input    → 明确的变量输入 (字段名、类型、约束等)             │
│  Task     → 清晰的输出任务描述                               │
│  Constraints → 强制约束条件 (覆盖范围、格式要求等)            │
│  Output   → 标准化输出格式 (表格、Mermaid 图等)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 模板列表

### 已发布模板

| 模板编号 | 名称 | 适用场景 | 文件路径 |
| :--- | :--- | :--- | :--- |
| **REQ-001** | 需求可测试性与歧义审查 | 需求评审、PRD 审计 | `templates/requirement-review-shift-left.md` |
| **BVA-001** | 边界值分析生成器 | UI 输入框、API 参数校验 | `templates/bva-boundary-value-analysis.md` |
| **STM-001** | 状态机流转生成器 | 订单系统、审批工作流 | `templates/state-transition-machine.md` |
| **API-001** | API 契约与业务逻辑测试 | RESTful 接口测试 | `templates/api-contract-testing.md` |
| **EXP-001** | 五边形人格探索性测试 | Monkey Testing、Charter-based | `templates/exploratory-testing-persona.md` |

### 计划中模板

| 模板编号 | 名称 | 适用场景 | 状态 |
| :--- | :--- | :--- | :--- |
| **EQ-001** | 等价类划分生成器 | 输入条件分类测试 | 📋 规划中 |
| **DT-001** | 决策表生成器 | 多条件组合业务规则 | 📋 规划中 |
| **ORT-001** | 正交阵列生成器 | 多因素组合测试 | 📋 规划中 |
| **USET-001** | 用户场景测试生成器 |端到端业务流程 | 📋 规划中 |

---

## 快速开始

### 方式一：直接复制模板

1. 进入 `templates/` 目录
2. 选择适合的模板文件
3. 复制模板内容到 AI 对话框
4. 替换 `{{变量名}}` 为实际值

### 方式二：使用示例作为参考

每个模板文件都包含实际示例，可直接参考修改：

```bash
# 查看 BVA 模板及示例
cat templates/bva-boundary-value-analysis.md

# 查看状态机模板及示例
cat templates/state-transition-machine.md
```

### 方式三：IDE 插件集成 (推荐团队使用)

使用 VS Code 或 IntelliJ 插件，快速调用模板：

1. 安装支持 snippet 的插件
2. 导入 `docs/snippets.json` (待创建)
3. 输入快捷词触发模板

---

## 使用指南

### 模板变量说明

| 变量名 | 说明 | 示例 |
| :--- | :--- | :--- |
| `{{project_name}}` | 项目名称 | 退休返聘系统 |
| `{{field_name}}` | 目标字段名 | 用户年龄 |
| `{{data_type}}` | 数据类型 | int, string, date |
| `{{constraints}}` | 约束范围 | 18-65, 长度 5-20 |
| `{{business_logic}}` | 业务逻辑备注 | 退休返聘，非此区间无法注册 |
| `{{module_name}}` | 模块名称 | 订单管理系统 |
| `{{state_list}}` | 状态列表 | 待支付，已支付，已完成 |
| `{{action_list}}` | 动作列表 | 用户支付，系统超时 |
| `{{requirement_text}}` | 需求原文 | PRD/用户故事完整文本 |
| `{{api_spec}}` | API 规范 | Swagger/JSON 格式 |
| `{{business_rules}}` | 业务规则列表 | Token 有效期、积分规则等 |
| `{{testing_goal}}` | 测试目标 | 探索性测试的 charter |

### 输出质量检查

使用 AI 生成测试用例后，请进行以下检查：

- [ ] 边界值是否完整覆盖 (min, min-1, min+1, max, max-1, max+1)
- [ ] 非法值检测是否充分
- [ ] 预期结果描述是否明确
- [ ] 优先级分配是否合理
- [ ] 错误提示语是否符合产品规范

---

## 集成方案

### 低级：Git 仓库托管

测试人员通过 IDE 或脚本快速检索 `.md` 模板。

```bash
# 搜索模板
grep -r "边界值" templates/

# 快速查看模板
cat templates/bva-boundary-value-analysis.md
```

### 中级：Coze/Dify 变量化封装

在 Dify 中创建 Workflow：
1. 将模板中的 `{{变量}}` 设为输入框
2. 测试人员只需填写关键参数
3. 点击"运行"获得标准化输出

### 高级：IDE 插件集成

开发 VS Code/IntelliJ 插件：
1. 选中需求文档中的文字
2. 右键点击"生成边界值用例"
3. 插件自动拼接 Prompt 并调用 LLM 接口

---

## 效果评估

记录 AI 生成用例的质量指标，作为模板迭代依据：

| 指标 | 计算方式 | 目标值 |
| :--- | :--- | :--- |
| 用例采纳率 | (被采纳用例数 / 生成总数) × 100% | ≥ 85% |
| 无效用例率 | (标记无效用例数 / 生成总数) × 100% | ≤ 10% |
| 逻辑错误率 | (逻辑错误用例数 / 生成总数) × 100% | ≤ 5% |

---

## 贡献指南

### 提交新模板

1. 在 `templates/` 目录创建新模板文件
2. 遵循命名规范：`{类型}-{场景}.md`
3. 包含完整示例和变更记录
4. 提交 PR 进行团队评审

### 模板版本规范

```
v{主版本}.{次版本}.{修订号}

例如：
v1.0.0 - 初始版本
v1.1.0 - 新增示例
v1.0.1 - 修复 typo
```

### 评审检查清单

- [ ] 模板结构符合 RCTF 架构
- [ ] 变量定义清晰明确
- [ ] 约束条件完整
- [ ] 输出格式标准化
- [ ] 至少包含 2 个实际示例

---

## 目录结构

```
qa-prompts/
├── templates/                  # 模板文件
│   ├── bva-boundary-value-analysis.md    # BVA 边界值分析
│   ├── state-transition-machine.md       # 状态机流转
│   ├── requirement-review-shift-left.md  # 需求审查
│   ├── api-contract-testing.md           # API 契约测试
│   └── exploratory-testing-persona.md    # 探索性测试
├── examples/                   # 使用示例
│   └── (待添加)
├── docs/                       # 文档
│   └── engineering-guide.md    # 工程化管理指南
├── README.md                   # 本文件
└── .gitignore
```

---

## 许可

内部使用，请勿外传。

---

## 联系方式

有问题或建议？请联系 QA 团队。
