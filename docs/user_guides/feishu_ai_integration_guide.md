# 飞书知识库 + AI IDE 集成操作指引 (SOP)

**文档编号**: SOP-FEISHU-AI-001
**版本**: v1.1
**最后更新**: 2026-03-29

---

## 概述

本指引面向具体执行人员，旨在建立飞书知识库与本地 AI IDE 的读写闭环。架构采用**"数据仓 + 逻辑仓 + Agent Skills"三层设计**：

- **数据仓** (`feishu-docs-sync`)：通过 Jenkins 定时拉取飞书知识库，转化为 Markdown 文件。
- **逻辑仓** (`qa-prompts`)：维护测试标准、AI Prompt、工作流与模板。
- **Agent Skills**：通过飞书官方的 19 个 Lark Skills，使 AI 直接调用飞书 API（多维表格、消息、文档、知识库等），无需传统 CLI 中间层。

```text
飞书知识库
    |
    v  (Jenkins + feishu2md, 每日凌晨同步)
feishu-docs-sync (数据仓, Git)
    |
    +--- qa-prompts (逻辑仓, Git)
    |         |
    v         v
    MCP Filesystem Server (读取本地知识)
         |
         v
    AI IDE (Cursor / Antigravity / VS Code)
         |
         v  (Lark Agent Skills, 直接 API 调用)
    飞书多维表格 / 群消息 / 文档 / 知识库
```

> [!NOTE]
> **与传统 CLI 方案的区别**：飞书官方提供的不是传统命令行工具，而是一套 **Agent Skills**（共 19 个），安装后直接嵌入 AI IDE 的能力体系中。AI 无需通过终端执行命令，而是通过 skills 机制以自然语言驱动飞书 API。

---

## 阶段一：自动化知识拉取（后台静默机制）

**目标**：建立无人值守的 Jenkins 流水线，每日将指定的飞书知识库拉取为 Markdown 并同步至专门的 Git 仓库。

> [!IMPORTANT]
> **设计决策：为什么阶段一不使用 Lark Skills？**
>
> Lark Skills 是 **Agent Skills**，必须由 AI 大模型驱动。若阶段一也用 Skills 模式，Jenkins 不仅需要飞书凭据，还需额外配置大模型 API Key，并且每次同步都会消耗推理 token。
>
> 阶段一是一个**确定性的数据搬运任务**（固定知识库 → 固定 Git 仓库），不需要 AI 的理解和判断能力。使用 `feishu2md` 直连飞书 REST API 更稳定、更便宜、更安全。
>
> **分工原则**：确定性管道用脚本（阶段一），需要判断和灵活决策的场景用 AI + Skills（阶段二）。


### Step 1.1：配置飞书应用与权限

1. 登录 [飞书开放平台](https://open.feishu.cn)，点击"创建企业自建应用"，命名为 `QA-Docs-Sync`。
2. 进入应用后台，左侧导航栏选择 **开发配置 > 权限管理**。
3. 搜索并开通以下核心权限：

| 权限标识 | 说明 | 用途 |
|:---|:---|:---|
| `docx:document:readonly` | 读取及下载文档 | 拉取文档正文内容 |
| `drive:drive:readonly` | 查看、下载云文档 | 访问云空间中的文件 |
| `wiki:wiki:readonly` | 查看知识库 | 访问知识库节点列表与内容 |

> [!WARNING]
> **权限缺失是最常见的失败原因**。如果目标文档存放在"知识库"而非普通"云文档"中，缺少 `wiki:wiki:readonly` 权限会导致 API 返回 `Permission Denied`。

4. 左侧导航栏选择 **应用发布 > 版本管理与发布**，创建一个版本并申请发布（需企业管理员审批）。
5. 应用发布后，进入 **添加应用能力**，开启"机器人"能力。

> [!IMPORTANT]
> **必须将应用添加为目标知识库的协作者**。
> 飞书的权限模型是：`最终权限 = API 权限 ∩ 资源授权`。即使应用有 API 权限，也必须在目标知识库的"成员管理"中，将应用的机器人账号添加为"可阅读"协作者，否则无法访问具体文档。
>
> **操作路径**：飞书知识库 > 设置 > 成员管理 > 添加成员 > 搜索应用机器人名称 > 授予"可阅读"权限。

6. 在 **凭证与基础信息** 页面，记录 `App ID` 和 `App Secret`。

### Step 1.2：初始化数据同步专用 Git 仓库

1. 在代码托管平台（如 GitLab/GitHub）创建一个全新的**私有**仓库，命名为 `feishu-docs-sync`。
2. 为该仓库生成一个具备读写权限的 **Personal Access Token (PAT)**，用于 Jenkins 自动化推送代码。
3. 记录仓库的 Clone URL 和 PAT。

### Step 1.3：获取飞书知识库/文件夹 Token

> [!NOTE]
> **如何获取 Token**：在飞书中打开目标知识库或文件夹，查看浏览器地址栏 URL。
> - 知识库 URL 格式：`https://xxx.feishu.cn/wiki/<space_id>`
> - 文件夹 URL 格式：`https://xxx.feishu.cn/drive/folder/<folder_token>`
>
> 其中 `<space_id>` 或 `<folder_token>` 即为需要的 Token。

### Step 1.4：配置 Jenkins 定时流水线

1. 在 Jenkins 中新建一个 Pipeline 任务，命名为 `Daily-Feishu-Docs-Sync`。
2. 设置 **Build Triggers (构建触发器)**，勾选 `Build periodically`，输入 `H 2 * * *`（每天凌晨 2 点左右执行）。
3. 在 **Jenkins 凭据管理 (Credentials)** 中，将 App ID、App Secret 和 Git PAT 配置为全局凭证（Secret Text 类型）。

> [!WARNING]
> **安全规范**：禁止在脚本中硬编码凭据。必须通过 Jenkins Credentials 注入，脚本中使用 `${APP_ID}` 等变量引用。

4. 编写流水线脚本。以 [feishu2md](https://github.com/Wsine/feishu2md)（Go 二进制）或 [feishu-docx](https://github.com/leemysw/feishu-docx)（Python pip）为例：

```bash
# === feishu2md 方案（Go 二进制，推荐用于纯 Markdown 导出） ===

# 1. 设置环境变量供鉴权使用（由 Jenkins Credentials 注入）
export FEISHU_APP_ID="${APP_ID}"
export FEISHU_APP_SECRET="${APP_SECRET}"

# 2. 克隆数据仓（使用 PAT 鉴权）
git clone https://oauth2:${GIT_PAT}@gitlab.company.com/qa/feishu-docs-sync.git workspace
cd workspace

# 3. 清理旧数据并执行全量同步
rm -rf ./docs/*
feishu2md download <Feishu_Space_or_Folder_Token> --output ./docs

# 4. 提交并推送
git config user.name "Jenkins Sync Bot"
git config user.email "bot@company.com"
git add .
git commit -m "chore: daily sync feishu docs $(date +'%Y-%m-%d')" || echo "No changes"
git push origin main
```

> [!NOTE]
> **全量 vs 增量**：当前脚本采用全量同步策略（先删后拉）。对于大型知识库（>500 篇），建议评估增量方案（如基于文件修改时间戳过滤）以降低同步耗时。

---

## 阶段二：本地 AI 业务逻辑控制（Agent Skills 赋能）

**目标**：在测试工程师的本地环境安装飞书 Agent Skills，打通 AI IDE 与飞书的读写闭环。

### Step 2.1：安装飞书 Agent Skills

确保本地已安装 **Node.js (推荐 v18+)** 和 **npx**。

执行全局安装命令：

```bash
npx skills add larksuite/cli
```

该命令会从 `github.com/larksuite/cli` 拉取并安装 **19 个飞书 Agent Skills**，自动适配已安装的 AI IDE（Antigravity、Cursor、Claude Code 等）。

安装完成后，skills 被部署到 `~/.agents/skills/lark-*` 目录下：

| Skill 名称 | 能力 |
|:---|:---|
| `lark-base` | 多维表格的增删改查 |
| `lark-im` | 消息发送、群组管理 |
| `lark-doc` | 文档创建与编辑 |
| `lark-wiki` | 知识库节点读写 |
| `lark-drive` | 云空间文件操作 |
| `lark-sheets` | 电子表格操作 |
| `lark-calendar` | 日历与日程管理 |
| `lark-task` | 任务管理 |
| `lark-contact` | 通讯录查询 |
| `lark-event` | 事件订阅 |
| 其他 9 个 | 邮件、会议、白板、工作流等 |

> [!IMPORTANT]
> **安全风险评估**：安装过程会自动展示每个 skill 的安全审计结果（Gen/Socket/Snyk）。`lark-base`、`lark-doc`、`lark-drive`、`lark-sheets`、`lark-whiteboard` 被标记为 `High Risk`（因其具备写入能力）。请确保仅在可信环境中授权写操作。

### Step 2.2：初始化 QA 逻辑专属仓库

1. 拉取团队的逻辑仓库：

```bash
git clone <qa-prompts 仓库地址>
```

2. 确认仓库中已维护的测试标准与 AI Prompt：

| 目录/文件 | 用途 |
|:---|:---|
| `templates/defect-report-template.md` | 缺陷单必备字段定义 |
| `skills/bug-triage-rules/SKILL.md` | 缺陷定级的判断依据 |
| `skills/8d-qm-analysis/SKILL.md` | 8D 分析的标准结构要求 |
| `.agents/workflows/bug-diagnostic-flow.md` | 缺陷诊断工作流 |

### Step 2.3：配置 IDE 的 MCP 接入（数据仓读取）

确保本地同时 clone 了 `feishu-docs-sync`（数据仓）和 `qa-prompts`（逻辑仓）。

#### Cursor 配置

打开 Cursor，进入 **Settings -> Features -> MCP Servers**，添加新 Server：

| 字段 | 值 |
|:---|:---|
| Type | `command` |
| Name | `QA-Knowledge-Base` |
| Command | `npx` |
| Args | `-y @modelcontextprotocol/server-filesystem <feishu-docs-sync 绝对路径> <qa-prompts 绝对路径>` |

保存并验证 Server 状态显示为绿色连通。

#### 其他 IDE（Antigravity / VS Code + Cline 等）

各 IDE 的 MCP 配置方式可能不同，但核心原理一致：将两个仓库的绝对路径作为 `@modelcontextprotocol/server-filesystem` 的参数传入即可。

> [!NOTE]
> **能力分工**：
> - **MCP Filesystem Server**：负责读取本地 Git 仓库中的 Markdown 文件（数据仓 + 逻辑仓）。
> - **Lark Agent Skills**：负责直接调用飞书 API（写多维表格、发消息、建文档等）。
>
> 两者互补：MCP 提供"读本地知识"的能力，Lark Skills 提供"写飞书"的能力。

---

## 阶段三：端到端业务执行演示

环境配置完成后，测试工程师可按以下方式执行标准业务流：

### 触发场景

测试过程中发现系统出现报错日志，需要进行缺陷分析并建单。

### AI 对话交互示例

```
"请根据 qa-prompts 中的缺陷分析规范，结合当前报错日志和 feishu-docs-sync 中的
《支付接口重试机制设计文档》，生成一份原因排查报告。确认无误后，将问题摘要
和排查报告插入到飞书的 [质量追踪多维表格ID] 中，并向测试群 [群组ID] 发送
一条通知卡片。"
```

### 底层执行流

```text
1. AI 通过 MCP 读取逻辑仓 → 获取排查报告的字段规范
2. AI 通过 MCP 读取数据仓 → 获取该接口的正确设计逻辑
3. AI 在 IDE 中生成分析报告 → 供工程师 Review
4. AI 通过 Lark Skills 直接操作飞书 → 完成业务闭环
   - lark-base skill → 写入多维表格记录
   - lark-im skill   → 发送群消息通知卡片
```

---

## 变更记录

| 版本 | 日期 | 作者 | 变更说明 |
|:---|:---|:---|:---|
| v1.1 | 2026-03-29 | QA Team | 架构性修正：阶段二从传统 CLI 方案改为飞书官方 Agent Skills 方案（19 个 skills），AI 通过 skills 直接调用飞书 API，不再依赖终端命令。 |
| v1.0 | 2026-03-29 | QA Team | 初始版本。基于原始方案补充了知识库权限、协作者授权、Token 获取、安全规范和能力边界等细节。 |

