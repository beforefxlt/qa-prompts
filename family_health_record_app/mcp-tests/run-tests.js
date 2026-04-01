/**
 * MCP 前端测试执行脚本
 * 使用 Chrome DevTools MCP Server 执行家庭健康记录应用的前端测试
 */

const { spawn } = require('child_process');
const http = require('http');

// 测试配置
const CONFIG = {
  frontendUrl: 'http://127.0.0.1:3001',
  backendUrl: 'http://127.0.0.1:8000',
  chromeDebugPort: 9222,
  testResults: [],
};

// 测试用例定义
const TEST_CASES = [
  {
    id: 'TC-MCP-001',
    name: '空状态引导验证',
    description: '验证首次访问时显示空状态引导页面',
    steps: [
      'navigate_page to http://127.0.0.1:3001',
      'take_screenshot 验证空状态页面',
      'evaluate_script 检查欢迎文案存在',
      'evaluate_script 检查"添加第一位成员"按钮存在',
    ],
    prompt: '导航到 http://127.0.0.1:3001，验证页面显示"欢迎使用家庭检查单管理"和"添加第一位成员"按钮，截图保存为 tc001-empty-state.png',
  },
  {
    id: 'TC-MCP-002',
    name: '成员创建流程',
    description: '验证通过表单创建新成员的完整流程',
    steps: [
      'navigate_page to http://127.0.0.1:3001',
      'click "添加第一位成员" 按钮',
      'fill 表单: 姓名="MCP测试成员", 性别="男", 出生日期="2018-06-15", 类型="儿童"',
      'click "保存" 按钮',
      'take_screenshot 验证成员卡片',
    ],
    prompt: '在首页点击"添加第一位成员"，填写表单：姓名="MCP测试成员"，选择性别"男"，出生日期"2018-06-15"，成员类型选择"儿童"，点击"保存"。验证创建成功后看到成员卡片，截图保存为 tc002-create-member.png',
  },
  {
    id: 'TC-MCP-003',
    name: '成员编辑功能',
    description: '验证可以编辑和修改成员信息',
    steps: [
      'navigate_page to http://127.0.0.1:3001',
      'hover 成员卡片',
      'click "编辑" 按钮',
      'fill 姓名="已编辑成员"',
      'click "保存修改"',
      'take_screenshot 验证更新',
    ],
    prompt: '在成员列表中找到"MCP测试成员"，hover显示编辑按钮，点击编辑，将姓名修改为"已编辑成员"，点击"保存修改"。验证名称已更新，截图保存为 tc003-edit-member.png',
  },
  {
    id: 'TC-MCP-004',
    name: '成员删除功能',
    description: '验证可以软删除成员',
    steps: [
      'navigate_page to http://127.0.0.1:3001',
      'hover 成员卡片',
      'click "删除" 按钮',
      'handle_dialog accept',
      'take_screenshot 验证删除',
    ],
    prompt: '在成员列表中找到成员，hover显示删除按钮，点击删除，在弹出的确认对话框中点击确认。验证成员从列表中消失，截图保存为 tc004-delete-member.png',
  },
  {
    id: 'TC-MCP-005',
    name: '指标切换验证',
    description: '验证Dashboard中各指标切换功能正常',
    steps: [
      'navigate_page to 成员Dashboard',
      'click "眼轴" 按钮',
      'take_screenshot 眼轴图表',
      'click "身高" 按钮',
      'take_screenshot 身高图表',
      'click "体重" 按钮',
      'take_screenshot 体重图表',
    ],
    prompt: '进入成员Dashboard页面，依次点击指标切换按钮：眼轴、身高、体重、血糖。每次切换后验证图表标题正确更新并截图。保存截图为 tc005-metric-switch.png',
  },
  {
    id: 'TC-MCP-006',
    name: '空数据状态',
    description: '验证新成员Dashboard显示空数据提示',
    steps: [
      '创建新成员 (通过API)',
      'navigate_page to 新成员Dashboard',
      'take_screenshot 空数据状态',
    ],
    prompt: '创建一个新成员（无检查数据），进入其Dashboard页面。验证显示"暂无数据"或类似的空状态提示，截图保存为 tc006-empty-data.png',
  },
  {
    id: 'TC-MCP-007',
    name: '审核页面验证',
    description: '验证审核页面可以正常访问和显示',
    steps: [
      'navigate_page to http://127.0.0.1:3001/review',
      'take_screenshot 审核页面',
      'evaluate_script 检查页面标题',
    ],
    prompt: '导航到 http://127.0.0.1:3001/review，验证页面显示"OCR 识别结果审核"标题，截图保存为 tc007-review-page.png',
  },
  {
    id: 'TC-MCP-008',
    name: '页面加载性能',
    description: '验证首页加载性能指标',
    steps: [
      'performance_start_trace',
      'navigate_page to http://127.0.0.1:3001',
      'performance_stop_trace',
      'performance_analyze_insight',
    ],
    prompt: '启动性能追踪，导航到 http://127.0.0.1:3001，停止追踪并分析性能指标。报告 LCP、CLS、FCP 等核心指标。',
  },
];

/**
 * 检查服务是否可用
 */
function checkService(url, name) {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error(`${name} 服务启动超时: ${url}`));
    }, 30000);

    const check = () => {
      http.get(url, (res) => {
        clearTimeout(timeout);
        console.log(`✅ ${name} 服务可用: ${url} (状态码: ${res.statusCode})`);
        resolve(true);
      }).on('error', () => {
        setTimeout(check, 1000);
      });
    };

    check();
  });
}

/**
 * 生成测试执行指南
 */
function generateTestGuide() {
  const guide = `
# MCP 前端测试执行指南

## 前置条件

1. 确保后端服务运行在 http://127.0.0.1:8000
2. 确保前端服务运行在 http://127.0.0.1:3001
3. 启动 Chrome (带远程调试端口 9222):
   \`\`\`
   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\\chrome-mcp-profile"
   \`\`\`

## 执行测试

在 AI Agent (Claude Code / Copilot 等) 中依次执行以下指令：

### TC-MCP-001: 空状态引导验证
\`\`\`
导航到 http://127.0.0.1:3001，验证页面显示"欢迎使用家庭检查单管理"和"添加第一位成员"按钮，截图保存为 tc001-empty-state.png
\`\`\`

### TC-MCP-002: 成员创建流程
\`\`\`
在首页点击"添加第一位成员"，填写表单：姓名="MCP测试成员"，选择性别"男"，出生日期"2018-06-15"，成员类型选择"儿童"，点击"保存"。验证创建成功后看到成员卡片，截图保存为 tc002-create-member.png
\`\`\`

### TC-MCP-003: 成员编辑功能
\`\`\`
在成员列表中找到"MCP测试成员"，hover显示编辑按钮，点击编辑，将姓名修改为"已编辑成员"，点击"保存修改"。验证名称已更新，截图保存为 tc003-edit-member.png
\`\`\`

### TC-MCP-004: 成员删除功能
\`\`\`
在成员列表中找到成员，hover显示删除按钮，点击删除，在弹出的确认对话框中点击确认。验证成员从列表中消失，截图保存为 tc004-delete-member.png
\`\`\`

### TC-MCP-005: 指标切换验证
\`\`\`
进入成员Dashboard页面，依次点击指标切换按钮：眼轴、身高、体重、血糖。每次切换后验证图表标题正确更新并截图。保存截图为 tc005-metric-switch.png
\`\`\`

### TC-MCP-006: 空数据状态
\`\`\`
创建一个新成员（无检查数据），进入其Dashboard页面。验证显示"暂无数据"或类似的空状态提示，截图保存为 tc006-empty-data.png
\`\`\`

### TC-MCP-007: 审核页面验证
\`\`\`
导航到 http://127.0.0.1:3001/review，验证页面显示"OCR 识别结果审核"标题，截图保存为 tc007-review-page.png
\`\`\`

### TC-MCP-008: 页面加载性能
\`\`\`
启动性能追踪，导航到 http://127.0.0.1:3001，停止追踪并分析性能指标。报告 LCP、CLS、FCP 等核心指标。
\`\`\`

## 预期结果

| 用例 | 预期结果 |
|:---|:---|
| TC-MCP-001 | 空状态页面显示欢迎文案和添加按钮 |
| TC-MCP-002 | 成功创建成员并显示在列表中 |
| TC-MCP-003 | 成员名称成功更新 |
| TC-MCP-004 | 成员从列表中消失 |
| TC-MCP-005 | 各指标切换后图表标题正确更新 |
| TC-MCP-006 | 显示空数据提示 |
| TC-MCP-007 | 审核页面正常显示 |
| TC-MCP-008 | LCP < 2.5s, CLS < 0.1 |
`;

  return guide;
}

// 主函数
async function main() {
  console.log('🚀 MCP 前端测试准备中...\n');

  // 检查服务
  try {
    await checkService(`${CONFIG.backendUrl}/api/v1/health`, '后端');
    await checkService(CONFIG.frontendUrl, '前端');
  } catch (error) {
    console.error(`❌ ${error.message}`);
    console.log('\n请确保前后端服务已启动：');
    console.log('  后端: cd family_health_record_app/backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000');
    console.log('  前端: cd family_health_record_app/frontend && npm run dev');
    process.exit(1);
  }

  // 生成测试指南
  const guide = generateTestGuide();
  console.log(guide);

  // 保存测试指南到文件
  const fs = require('fs');
  const path = require('path');
  const guidePath = path.join(__dirname, 'TEST_GUIDE.md');
  fs.writeFileSync(guidePath, guide, 'utf-8');
  console.log(`\n📄 测试指南已保存到: ${guidePath}`);
}

main().catch(console.error);
