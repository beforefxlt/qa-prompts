/**
 * MCP 风格前端测试执行器 v4
 * 简化版：先用API验证核心功能，再测试UI展示
 */

const puppeteer = require('puppeteer');

const CONFIG = {
  frontendUrl: 'http://127.0.0.1:3001',
  backendUrl: 'http://127.0.0.1:8000',
  debugPort: 9222,
  screenshotDir: './screenshots',
};

const results = [];

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function takeScreenshot(page, name) {
  const filePath = `${CONFIG.screenshotDir}/${name}.png`;
  await page.screenshot({ path: filePath, fullPage: true });
  return filePath;
}

async function runTest(id, name, fn) {
  console.log(`\n🧪 [${id}] ${name}`);
  console.log('-'.repeat(50));
  try {
    await fn();
    results.push({ id, name, status: 'PASS', type: null });
    console.log(`✅ PASS`);
  } catch (error) {
    const diagnosis = diagnoseError(error);
    results.push({ id, name, status: 'FAIL', type: diagnosis.type, detail: diagnosis.detail });
    console.log(`❌ FAIL [${diagnosis.label}]`);
    console.log(`   原因: ${diagnosis.detail}`);
  }
}

function diagnoseError(error) {
  const msg = error.message || '';
  if (msg.includes('测试代码') || msg.includes('未找到') || msg.includes('选择器')) {
    return { type: 'test-code', label: '测试代码', detail: msg };
  }
  if (msg.includes('产品Bug') || msg.includes('功能') || msg.includes('UI') || msg.includes('内容')) {
    return { type: 'product-bug', label: '产品Bug', detail: msg };
  }
  if (msg.includes('fetch') || msg.includes('ECONNREFUSED') || msg.includes('network')) {
    return { type: 'environment', label: '环境', detail: msg };
  }
  return { type: 'unknown', label: '待调查', detail: msg };
}

async function apiCall(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${CONFIG.backendUrl}${path}`, opts);
  return res.json();
}

async function cleanupMembers() {
  const members = await apiCall('GET', '/api/v1/members');
  for (const m of members) {
    await apiCall('DELETE', `/api/v1/members/${m.id}`);
  }
  console.log(`🧹 清理了 ${members.length} 个成员`);
}

async function main() {
  console.log('🚀 MCP 前端测试执行器 v4 (简化版)');
  console.log('========================================');

  const fs = require('fs');
  if (!fs.existsSync(CONFIG.screenshotDir)) {
    fs.mkdirSync(CONFIG.screenshotDir, { recursive: true });
  }

  await cleanupMembers();
  await sleep(500);

  const browser = await puppeteer.connect({
    browserURL: `http://127.0.0.1:${CONFIG.debugPort}`,
    defaultViewport: { width: 1280, height: 800 },
  });
  console.log(`✅ Chrome: ${await browser.version()}`);

  const pages = await browser.pages();
  for (const p of pages) await p.close();
  const page = await browser.newPage();

  // 捕获控制台日志
  const consoleLogs = [];
  page.on('console', msg => consoleLogs.push({ type: msg.type(), text: msg.text() }));

  // ========== TC-MCP-001: 空状态引导 ==========
  await runTest('TC-MCP-001', '空状态引导验证', async () => {
    await page.goto(CONFIG.frontendUrl, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(1000);
    await takeScreenshot(page, 'tc001-empty-state');

    const text = await page.evaluate(() => document.body.innerText);
    console.log(`  页面标题: ${text.split('\n').slice(0, 3).join(' | ')}`);
    
    if (!text.includes('欢迎使用家庭检查单管理')) {
      if (text.includes('家庭成员')) throw new Error('产品Bug: 页面显示成员列表而非空状态');
      throw new Error('产品Bug: 缺少欢迎文案');
    }
    if (!text.includes('添加')) throw new Error('产品Bug: 缺少添加按钮');
  });

  // ========== TC-MCP-002: API成员创建 + 前端显示 ==========
  await runTest('TC-MCP-002', 'API创建成员 + 前端显示', async () => {
    // 通过API创建成员
    const member = await apiCall('POST', '/api/v1/members', {
      name: 'API测试成员', gender: 'male',
      date_of_birth: '2018-06-15', member_type: 'child',
    });
    console.log(`  API创建成员: ${member.id} (${member.name})`);

    if (!member.id) throw new Error('产品Bug: API创建成员失败');

    // 导航到成员详情页
    const url = `${CONFIG.frontendUrl}/?memberId=${member.id}&memberName=${encodeURIComponent('API测试成员')}`;
    console.log(`  导航到: ${url}`);
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(2000);
    await takeScreenshot(page, 'tc002-member-detail');

    const text = await page.evaluate(() => document.body.innerText);
    console.log(`  页面内容: ${text.split('\n').slice(0, 5).join(' | ')}`);

    if (!text.includes('API测试成员')) {
      throw new Error('产品Bug: 成员详情页未显示成员名称');
    }
    if (!text.includes('儿童眼轴') && !text.includes('Axial') && !text.includes('暂无数据')) {
      throw new Error('产品Bug: 成员详情页缺少图表或空状态');
    }
  });

  // ========== TC-MCP-003: 指标切换验证 ==========
  await runTest('TC-MCP-003', '指标切换验证', async () => {
    const member = await apiCall('POST', '/api/v1/members', {
      name: '指标成员', gender: 'male',
      date_of_birth: '2018-01-01', member_type: 'child',
    });

    await page.goto(
      `${CONFIG.frontendUrl}/?memberId=${member.id}&memberName=${encodeURIComponent('指标成员')}`,
      { waitUntil: 'networkidle0', timeout: 15000 }
    );
    await sleep(1500);
    await takeScreenshot(page, 'tc003-default');

    let text = await page.evaluate(() => document.body.innerText);
    console.log(`  默认指标: ${text.split('\n').slice(0, 3).join(' | ')}`);

    // 获取可用指标按钮
    const metrics = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('button'))
        .map(b => b.innerText.trim())
        .filter(t => ['眼轴', '身高', '体重', '血糖', '视力'].includes(t));
    });
    console.log(`  可用指标: [${metrics.join(', ')}]`);

    if (!metrics.includes('身高')) throw new Error('产品Bug: 缺少身高指标按钮');

    // 点击身高
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find(b => b.innerText.trim() === '身高');
      if (btn) btn.click();
    });
    await sleep(800);
    await takeScreenshot(page, 'tc003-height');

    text = await page.evaluate(() => document.body.innerText);
    if (!text.includes('身高') && !text.includes('Height')) {
      throw new Error('产品Bug: 切换到身高后标题未更新');
    }
  });

  // ========== TC-MCP-004: 审核页面验证 ==========
  await runTest('TC-MCP-004', '审核页面验证', async () => {
    await page.goto(`${CONFIG.frontendUrl}/review`, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(1000);
    await takeScreenshot(page, 'tc004-review');

    const text = await page.evaluate(() => document.body.innerText);
    console.log(`  审核页面: ${text.split('\n').slice(0, 3).join(' | ')}`);
    
    if (!text.includes('OCR 识别结果审核')) {
      throw new Error('产品Bug: 审核页面标题不正确');
    }
  });

  // ========== TC-MCP-005: 空数据状态 ==========
  await runTest('TC-MCP-005', '空数据状态', async () => {
    const member = await apiCall('POST', '/api/v1/members', {
      name: '空数据成员', gender: 'female',
      date_of_birth: '2019-01-01', member_type: 'child',
    });

    await page.goto(
      `${CONFIG.frontendUrl}/?memberId=${member.id}&memberName=${encodeURIComponent('空数据成员')}`,
      { waitUntil: 'networkidle0', timeout: 15000 }
    );
    await sleep(1500);
    await takeScreenshot(page, 'tc005-empty');

    const text = await page.evaluate(() => document.body.innerText);
    console.log(`  空数据页面: ${text.split('\n').slice(0, 3).join(' | ')}`);
    
    if (!text.includes('暂无数据') && !text.includes('上传检查单')) {
      throw new Error('产品Bug: 未显示空状态提示');
    }
  });

  // ========== TC-MCP-006: 前端表单交互 ==========
  await runTest('TC-MCP-006', '前端表单交互（简化）', async () => {
    await page.goto(CONFIG.frontendUrl, { waitUntil: 'networkidle0', timeout: 15000 });
    await sleep(1000);

    // 点击添加成员
    const clicked = await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find(b => b.innerText.includes('添加'));
      if (btn) { btn.click(); return true; }
      return false;
    });
    if (!clicked) throw new Error('测试代码问题: 未找到添加按钮');
    await sleep(800);
    await takeScreenshot(page, 'tc006-form-open');

    // 检查表单元素
    const formInfo = await page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('input'));
      const selects = Array.from(document.querySelectorAll('select'));
      return {
        inputCount: inputs.length,
        selectCount: selects.length,
        inputs: inputs.map(i => ({ type: i.type, placeholder: i.placeholder })),
      };
    });
    console.log(`  表单: ${formInfo.inputCount} inputs, ${formInfo.selectCount} selects`);
    console.log(`  Inputs: ${JSON.stringify(formInfo.inputs)}`);

    if (formInfo.inputCount < 2) throw new Error('产品Bug: 表单缺少输入框');
    if (formInfo.selectCount < 2) throw new Error('产品Bug: 表单缺少选择框');
  });

  // ========== 结果汇总 ==========
  console.log('\n========================================');
  console.log('📊 测试结果汇总');
  console.log('========================================');
  
  let pass = 0, fail = 0, testBug = 0, prodBug = 0, envBug = 0;
  for (const r of results) {
    const icon = r.status === 'PASS' ? '✅' : '❌';
    const typeTag = r.type ? `[${r.type === 'test-code' ? '测试代码' : r.type === 'product-bug' ? '产品Bug' : r.type === 'environment' ? '环境' : '待调查'}]` : '';
    console.log(`${icon} ${r.id}: ${r.name} - ${r.status} ${typeTag}`);
    if (r.status === 'PASS') pass++;
    else {
      fail++;
      if (r.type === 'test-code') testBug++;
      else if (r.type === 'product-bug') prodBug++;
      else if (r.type === 'environment') envBug++;
    }
  }
  
  console.log('\n----------------------------------------');
  console.log(`总计: ${results.length} | 通过: ${pass} ✅ | 失败: ${fail} ❌`);
  console.log(`失败分类:`);
  console.log(`  - 测试代码问题: ${testBug}`);
  console.log(`  - 产品Bug: ${prodBug}`);
  console.log(`  - 环境问题: ${envBug}`);
  console.log(`通过率: ${((pass / results.length) * 100).toFixed(1)}%`);
  console.log(`截图: ${CONFIG.screenshotDir}/`);

  browser.disconnect();
}

main().catch(err => { console.error('错误:', err); process.exit(1); });
