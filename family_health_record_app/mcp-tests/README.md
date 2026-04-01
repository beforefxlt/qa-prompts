# 家庭健康记录应用 - MCP 前端测试方案

> **版本**: v1.0.0
> **创建日期**: 2026-04-01
> **测试框架**: Chrome DevTools MCP Server

---

## 一、方案概述

本方案使用 Chrome DevTools MCP Server 替代传统 Playwright E2E 测试，利用 AI Agent 的"视觉"能力直接观察和操作浏览器，实现更智能、更鲁棒的前端测试。

### 核心优势

| 维度 | Playwright (传统) | Chrome DevTools MCP (新方案) |
|:---|:---|:---|
| 定位器 | 需要精确 CSS/XPath | 自然语言描述，AI 自动识别 |
| UI 变更适应 | 选择器失效需手动修复 | AI 语义理解，自动适应 |
| 视觉验证 | 需额外截图对比工具 | 原生截图 + AI 判断 |
| 性能测试 | 需额外配置 Lighthouse | 内置 Trace 分析 |
| 调试效率 | 看日志/截图推断 | Agent 直接"看"页面 |

---

## 二、环境配置

### 2.1 安装依赖

```bash
# 已安装
npm install -g chrome-devtools-mcp@latest
```

### 2.2 启动 Chrome (带远程调试)

**Windows**:
```powershell
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-mcp-profile"
```

### 2.3 MCP 配置

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest",
        "--browser-url=http://127.0.0.1:9222"
      ]
    }
  }
}
```

---

## 三、测试用例设计

### 3.1 成员管理测试 (Member Management)

#### TC-MCP-001: 空状态引导验证
**步骤**:
1. 导航到 `http://127.0.0.1:3001/`
2. 验证页面显示"欢迎使用家庭检查单管理"
3. 验证"添加第一位成员"按钮可见
4. 截图保存空状态页面

**MCP 工具调用**:
- `navigate_page` → URL
- `take_screenshot` → 验证空状态
- `evaluate_script` → 检查 DOM 元素存在性

#### TC-MCP-002: 成员创建流程
**步骤**:
1. 点击"添加第一位成员"按钮
2. 填写表单：姓名="测试成员", 性别="男", 出生日期="2018-01-01", 类型="儿童"
3. 点击"保存"
4. 验证成员卡片出现在列表中

**MCP 工具调用**:
- `click` → 按钮
- `fill` → 表单字段
- `take_screenshot` → 验证结果

#### TC-MCP-003: 成员编辑功能
**步骤**:
1. Hover 成员卡片显示编辑按钮
2. 点击编辑按钮
3. 修改姓名为"已编辑成员"
4. 点击"保存修改"
5. 验证名称已更新

#### TC-MCP-004: 成员删除功能
**步骤**:
1. Hover 成员卡片显示删除按钮
2. 点击删除按钮
3. 确认删除对话框
4. 验证成员从列表中消失

### 3.2 Dashboard 测试

#### TC-MCP-005: 指标切换验证
**步骤**:
1. 进入成员 Dashboard
2. 依次点击：眼轴 → 身高 → 体重 → 血糖
3. 验证每个指标切换后图表标题正确更新
4. 截图每个指标状态

#### TC-MCP-006: 空数据状态
**步骤**:
1. 创建新成员（无检查数据）
2. 进入 Dashboard
3. 验证显示"暂无数据"提示

### 3.3 审核流程测试

#### TC-MCP-007: 审核页面验证
**步骤**:
1. 导航到 `/review`
2. 验证页面标题"OCR 识别结果审核"
3. 验证空状态或任务列表显示

### 3.4 性能测试

#### TC-MCP-008: 页面加载性能
**步骤**:
1. 启动性能 Trace
2. 导航到首页
3. 停止 Trace 并分析
4. 验证 LCP < 2.5s, CLS < 0.1

**MCP 工具调用**:
- `performance_start_trace`
- `performance_stop_trace`
- `performance_analyze_insight`

---

## 四、执行方式

### 4.1 手动执行 (Agent 驱动)

1. 启动前后端服务
2. 启动 Chrome (带调试端口)
3. 在 AI Agent 中输入测试指令，例如：
   ```
   导航到 http://127.0.0.1:3001，验证空状态页面显示正确，截图保存
   ```

### 4.2 自动化执行 (脚本驱动)

创建测试脚本 `mcp-tests/run-tests.js`，使用 MCP SDK 自动执行测试流程。

---

## 五、可用 MCP 工具清单

### 输入自动化 (9 个)
- `click` - 点击元素
- `drag` - 拖拽
- `fill` - 填写表单
- `fill_form` - 批量填写表单
- `handle_dialog` - 处理对话框
- `hover` - 悬停
- `press_key` - 按键
- `type_text` - 输入文本
- `upload_file` - 上传文件

### 导航自动化 (6 个)
- `close_page` - 关闭页面
- `list_pages` - 列出页面
- `navigate_page` - 导航
- `new_page` - 新建页面
- `select_page` - 选择页面
- `wait_for` - 等待条件

### 调试 (6 个)
- `evaluate_script` - 执行 JS
- `get_console_message` - 获取控制台消息
- `lighthouse_audit` - Lighthouse 审计
- `list_console_messages` - 列出控制台消息
- `take_screenshot` - 截图
- `take_snapshot` - DOM 快照

### 性能 (4 个)
- `performance_analyze_insight` - 分析性能
- `performance_start_trace` - 开始追踪
- `performance_stop_trace` - 停止追踪
- `take_memory_snapshot` - 内存快照

### 网络 (2 个)
- `get_network_request` - 获取网络请求
- `list_network_requests` - 列出网络请求

---

## 六、与 Playwright 方案对比

| 项目 | Playwright | MCP |
|:---|:---|:---|
| 测试文件 | 5 个 spec.ts | 待创建 |
| 用例数 | 18 | 8 (核心场景) |
| 执行时间 | ~70s | 待测量 |
| 维护成本 | 高 (选择器敏感) | 低 (语义化) |
| 视觉验证 | 需额外配置 | 原生支持 |
| 性能分析 | 需额外工具 | 内置 |

---

## 七、下一步行动

1. ✅ 安装 Chrome DevTools MCP Server
2. ⏳ 启动前后端服务
3. ⏳ 启动 Chrome (带调试端口)
4. ⏳ 执行 TC-MCP-001 ~ TC-MCP-008
5. ⏳ 收集测试结果和截图
6. ⏳ 生成测试报告
