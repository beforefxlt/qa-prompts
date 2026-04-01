# MCP 前端测试执行指南

> **生成时间**: 2026-04-01 08:50
> **目标应用**: 家庭健康记录管理应用
> **测试框架**: Chrome DevTools MCP Server

---

## 环境状态

| 服务 | 状态 | 地址 |
|:---|:---|:---|
| 后端 (FastAPI) | ✅ 运行中 | http://127.0.0.1:8000 |
| 前端 (Next.js) | ✅ 运行中 | http://127.0.0.1:3001 |
| Chrome (调试) | ✅ 已启动 | ws://127.0.0.1:9222 |
| MCP Server | ✅ 已安装 | chrome-devtools-mcp@latest |

---

## 🔐 数据治理协议 (Data Governance)

为了确保测试的**幂等性**和**结果可靠性**，必须严格执行以下数据库状态管理：

### 1. 测试前置 (Pre-Test)
**必须清空数据库**，确保处于“零成员、零记录”的纯洁状态。执行以下命令：
```bash
cd family_health_record_app/backend
# 此脚本将执行 drop_all 并在内存/本地重建 schema
python rebuild_db.py
```
**预期状态**: 访问首页应看到“TC-MCP-001: 空状态引导页面”。

### 2. 测试后置 (Post-Test)
**禁止保留测试脏数据**。所有用例执行完毕后，必须再次运行清理脚本：
```bash
cd family_health_record_app/backend
python rebuild_db.py
```
**目标**: 确保开发环境不包含“MCP测试成员”等临时数据。

---

## 快速开始

### 方式一：通过 AI Agent 执行 (推荐)

在 Claude Code / Copilot / Cursor 等支持 MCP 的 Agent 中，按顺序发送以下指令：

---

#### 📋 TC-MCP-001: 空状态引导验证
**数据背景**: 数据库已执行重置，成员列表为空。

```
使用 Chrome DevTools MCP 工具执行以下操作：

1. 使用 navigate_page 导航到 http://127.0.0.1:3001
2. 使用 take_screenshot 截图当前页面
3. 使用 evaluate_script 检查页面是否包含"欢迎使用家庭检查单管理"文本
4. 使用 evaluate_script 检查"添加第一位成员"按钮是否存在
5. 报告测试结果

预期结果：空状态页面正常显示欢迎文案和添加按钮
```

---

#### 📋 TC-MCP-002: 成员创建流程
**数据背景**: 数据库为空。测试后将新增 1 条成员记录。

```
使用 Chrome DevTools MCP 工具执行以下操作：

1. 确保在 http://127.0.0.1:3001 页面
2. 使用 click 点击"添加第一位成员"按钮
3. 等待表单出现后，使用 fill 填写：
   - 姓名输入框: "MCP测试成员"
   - 性别选择: "男"
   - 出生日期: "2018-06-15"
   - 成员类型: "儿童"
4. 使用 click 点击"保存"按钮
5. 使用 take_screenshot 截图验证成员创建成功
6. 使用 evaluate_script 检查页面是否包含"MCP测试成员"文本

预期结果：成员创建成功并显示在列表中
```

---

#### 📋 TC-MCP-003: 成员编辑功能

```
使用 Chrome DevTools MCP 工具执行以下操作：

1. 在成员列表页面，使用 hover 悬停在"MCP测试成员"卡片上
2. 等待编辑按钮出现后，使用 click 点击"编辑"按钮
3. 在编辑表单中，使用 fill 将姓名修改为"已编辑成员"
4. 使用 click 点击"保存修改"按钮
5. 使用 take_screenshot 截图验证名称已更新
6. 使用 evaluate_script 检查页面是否包含"已编辑成员"文本

预期结果：成员名称成功更新
```

---

#### 📋 TC-MCP-004: 成员删除功能

```
使用 Chrome DevTools MCP 工具执行以下操作：

1. 在成员列表页面，使用 hover 悬停在成员卡片上
2. 等待删除按钮出现后，使用 click 点击"删除"按钮
3. 使用 handle_dialog 处理确认对话框 (accept)
4. 使用 take_screenshot 截图验证成员已删除
5. 使用 evaluate_script 检查页面是否不再包含被删除成员的文本

预期结果：成员从列表中消失
```

---

#### 📋 TC-MCP-005: 指标切换验证

```
使用 Chrome DevTools MCP 工具执行以下操作：

1. 首先通过 API 创建一个测试成员：
   POST http://127.0.0.1:8000/api/v1/members
   Body: {"name":"指标测试成员","gender":"male","date_of_birth":"2018-01-01","member_type":"child"}
2. 获取成员 ID 后，使用 navigate_page 导航到：
   http://127.0.0.1:3001/?memberId={memberId}&memberName=指标测试成员
3. 使用 take_screenshot 截图默认眼轴图表
4. 依次使用 click 点击指标按钮：身高、体重、血糖
5. 每次点击后使用 take_screenshot 截图
6. 使用 evaluate_script 验证图表标题是否正确更新

预期结果：各指标切换后图表标题正确更新
```

---

#### 📋 TC-MCP-006: 空数据状态

```
使用 Chrome DevTools MCP 工具执行以下操作：

1. 通过 API 创建一个新成员（无检查数据）：
   POST http://127.0.0.1:8000/api/v1/members
   Body: {"name":"空数据成员","gender":"female","date_of_birth":"2019-01-01","member_type":"child"}
2. 获取成员 ID 后，导航到其 Dashboard
3. 使用 take_screenshot 截图
4. 使用 evaluate_script 检查页面是否包含"暂无数据"文本

预期结果：显示空数据提示
```

---

#### 📋 TC-MCP-007: 审核页面验证

```
使用 Chrome DevTools MCP 工具执行以下操作：

1. 使用 navigate_page 导航到 http://127.0.0.1:3001/review
2. 使用 take_screenshot 截图审核页面
3. 使用 evaluate_script 检查页面是否包含"OCR 识别结果审核"文本
4. 使用 list_console_messages 检查是否有 JavaScript 错误

预期结果：审核页面正常显示，无控制台错误
```

---

#### 📋 TC-MCP-008: 页面加载性能

```
使用 Chrome DevTools MCP 工具执行以下操作：

1. 使用 performance_start_trace 开始性能追踪
2. 使用 navigate_page 导航到 http://127.0.0.1:3001
3. 等待页面加载完成后，使用 performance_stop_trace 停止追踪
4. 使用 performance_analyze_insight 分析性能指标
5. 报告以下核心指标：
   - LCP (Largest Contentful Paint)
   - CLS (Cumulative Layout Shift)
   - FCP (First Contentful Paint)
   - TBT (Total Blocking Time)

预期结果：LCP < 2.5s, CLS < 0.1, FCP < 1.8s
```

---

### 方式二：通过 MCP SDK 自动化执行

创建 Node.js 脚本直接调用 MCP 工具：

```javascript
// mcp-tests/automated-runner.js
const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');

async function runTests() {
  // 连接到 MCP Server
  const transport = new StdioClientTransport({
    command: 'npx',
    args: ['-y', 'chrome-devtools-mcp@latest', '--browser-url=http://127.0.0.1:9222'],
  });
  
  const client = new Client({
    name: 'test-runner',
    version: '1.0.0',
  }, { capabilities: {} });
  
  await client.connect(transport);
  
  // 执行测试用例
  for (const testCase of TEST_CASES) {
    console.log(`\n🧪 执行: ${testCase.id} - ${testCase.name}`);
    
    // 导航
    await client.callTool({
      name: 'navigate_page',
      arguments: { url: testCase.url },
    });
    
    // 截图
    const screenshot = await client.callTool({
      name: 'take_screenshot',
      arguments: {},
    });
    
    // 验证
    const result = await client.callTool({
      name: 'evaluate_script',
      arguments: { expression: testCase.assertion },
    });
    
    console.log(`✅ ${testCase.id}: ${result.passed ? 'PASS' : 'FAIL'}`);
  }
}
```

---

## MCP 工具速查表

| 工具名 | 用途 | 示例 |
|:---|:---|:---|
| `navigate_page` | 导航到 URL | `{url: "http://..."}` |
| `click` | 点击元素 | `{element: "按钮文本"}` |
| `fill` | 填写表单 | `{element: "输入框", value: "文本"}` |
| `hover` | 悬停元素 | `{element: "卡片"}` |
| `take_screenshot` | 截图 | `{}` |
| `evaluate_script` | 执行 JS | `{expression: "document.title"}` |
| `handle_dialog` | 处理对话框 | `{action: "accept"}` |
| `list_console_messages` | 控制台消息 | `{}` |
| `performance_start_trace` | 开始性能追踪 | `{}` |
| `performance_stop_trace` | 停止性能追踪 | `{}` |
| `performance_analyze_insight` | 分析性能 | `{}` |

---

## 测试结果记录

| 用例 | 状态 | 截图 | 备注 |
|:---|:---|:---|:---|
| TC-MCP-001 | ⏳ 待执行 | - | 空状态引导 |
| TC-MCP-002 | ⏳ 待执行 | - | 成员创建 |
| TC-MCP-003 | ⏳ 待执行 | - | 成员编辑 |
| TC-MCP-004 | ⏳ 待执行 | - | 成员删除 |
| TC-MCP-005 | ⏳ 待执行 | - | 指标切换 |
| TC-MCP-006 | ⏳ 待执行 | - | 空数据状态 |
| TC-MCP-007 | ⏳ 待执行 | - | 审核页面 |
| TC-MCP-008 | ⏳ 待执行 | - | 性能测试 |

---

## 故障排查

### Chrome 连接失败
```bash
# 检查 Chrome 调试端口
curl http://127.0.0.1:9222/json/version

# 如果无响应，重启 Chrome
taskkill /F /IM chrome.exe
start chrome --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-mcp-profile"
```

### MCP 工具不可用
```bash
# 验证 MCP Server 安装
npx chrome-devtools-mcp@latest --help

# 重新安装
npm install -g chrome-devtools-mcp@latest
```

### 前端页面加载慢
```bash
# 检查 Next.js 编译状态
# 查看前端终端输出，等待 "Ready in Xms"
```

---

# 📚 测试资源清单 (Resource Catalog)

| 资源名 | 类型 | 位置 | 用途描述 |
|:---|:---|:---|:---|
| `rebuild_db.py` | 🛠️ 清理工具 | `backend/rebuild_db.py` | 归零测试环境，删除所有脏数据并重建 schema。 |
| `seed_data.py` | 🧬 数据资产 | `mcp-tests/seed_data.py` | 灌入历史观测值（身高/体重等），验证图表渲染。 |
| `prepare_data.py` | 🧪 原子接口 | `mcp-tests/prepare_data.py` | 使用 API 模拟原子级成员创建。 |
| `mcp-runner.js` | 🏃 执行器 | `mcp-tests/mcp-runner.js` | 核心 MCP 测试驱动逻辑。 |

---

## 👨‍💻 维护者注记
1.  **资产化执行**: 以上脚本均已纳入版本控制，请勿随意更改 ID 或 URL。
2.  **清理规范**: 每次全量测试 (TC-MCP-001 ~ 008) 运行前后，均需执行 `rebuild_db.py` 保证测试的幂等性。

