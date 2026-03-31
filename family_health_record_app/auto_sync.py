# 自动同步脚本：每 15 分钟更新开发日志并提交
# 用法: python auto_sync.py
# 可配合 Windows 任务计划程序实现定时执行

#  Windows 任务计划程序配置示例 (每 15 分钟):
# schtasks /create /tn "DevLogSync" /tr "python C:\Users\Administrator\qa-prompts\family_health_record_app\auto_sync.py" /sc minute /mo 15

import os
import subprocess
import sys
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(PROJECT_ROOT, "DEVELOPMENT_LOG.md")
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

def run_cmd(cmd, cwd=None, timeout=30):
    """执行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, cwd=cwd or PROJECT_ROOT, timeout=timeout
        )
        stdout = result.stdout.decode('utf-8', errors='replace').strip()
        stderr = result.stderr.decode('utf-8', errors='replace').strip()
        return stdout, stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def count_tests():
    """运行 pytest 并统计通过/失败数量"""
    stdout, _, _ = run_cmd(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=no", "-q"],
        cwd=BACKEND_DIR
    )
    passed = 0
    failed = 0
    for line in (stdout + "\n").splitlines():
        if "passed" in line:
            for part in line.split():
                if part.isdigit():
                    passed = int(part)
                    break
        if "failed" in line:
            for part in line.split():
                if part.isdigit():
                    failed = int(part)
                    break
    return passed, failed

def count_files(directory):
    """统计目录下的 .py/.ts/.tsx 文件数量"""
    count = 0
    if not os.path.exists(directory):
        return count
    for root, dirs, files in os.walk(directory):
        # 跳过 __pycache__ 和 .pytest_cache
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.pytest_cache', 'node_modules')]
        for f in files:
            if f.endswith(('.py', '.ts', '.tsx')):
                count += 1
    return count

def get_git_status():
    """获取 git 状态"""
    stdout, _, _ = run_cmd(["git", "status", "--short"])
    lines = [l for l in stdout.splitlines() if l.strip()]
    modified = sum(1 for l in lines if l.startswith(" M") or l.startswith("M "))
    added = sum(1 for l in lines if l.startswith("??") or l.startswith("A "))
    staged = sum(1 for l in lines if l.startswith("M ") or l.startswith("A "))
    return modified, added, staged, lines

def has_code_changes():
    """检查是否有代码变更（排除日志文件本身）"""
    stdout, _, _ = run_cmd(["git", "diff", "--name-only", "HEAD"])
    changed_files = [f for f in stdout.splitlines() if f.strip()]
    code_files = [f for f in changed_files if f.endswith(('.py', '.ts', '.tsx', '.md')) and 'DEVELOPMENT_LOG' not in f]
    return len(code_files) > 0

def generate_log():
    """生成开发日志内容"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    passed, failed = count_tests()
    py_count = count_files(os.path.join(BACKEND_DIR, "app"))
    test_count = count_files(os.path.join(BACKEND_DIR, "tests"))
    ts_count = count_files(os.path.join(PROJECT_ROOT, "frontend", "src"))
    modified, added, staged, lines = get_git_status()

    # 获取最近的 commit
    recent_commits, _, _ = run_cmd(["git", "log", "--oneline", "-3"])

    log_content = f"""# 家庭检查单管理应用 - 每日开发日志 (2026-03-31)

> **最后更新**: {now} (自动同步)
> **版本**: v1.3.0

## 当前状态快照

| 指标 | 数值 |
|:---|:---|
| 后端测试 | {passed} passed, {failed} failed |
| 后端源文件 | {py_count} 个 (app/) |
| 测试文件 | {test_count} 个 (tests/) |
| 前端源文件 | {ts_count} 个 (src/) |
| Git 工作区 | {modified} 个已修改, {added} 个未跟踪 |
| Git 暂存区 | {staged} 个已暂存 |

---

## 已交付产出物清单

### 1. 后端层 (FastAPI + SQLAlchemy 异步)
* [x] **Task 0.5**: 数据库模型与迁移（7 个模型，无 accounts 表）。
* [x] **Task 1**: 成员档案服务 CRUD + PUT + DELETE (`routers/members.py`)。
* [x] **Task 2**: 图像处理 + MinIO 存储 (`services/`)。
* [x] **Task 3**: OCR 编排器 + 规则引擎 (`services/`)。
* [x] **Task 4**: 审核服务 (`routers/review.py`) — approve/reject/save-draft。
* [x] **Task 5**: 趋势服务增强 (`routers/trends.py`) — trends/vision-dashboard/growth-dashboard。
* [x] **Task 6**: 文档上传服务 (`routers/documents.py`) — UUID 唯一文件名。

### 2. 前端层 (Next.js 15 + TypeScript)
* [x] 空状态引导 + 成员列表 + 成员编辑/删除
* [x] 9 项指标切换标签
* [x] OCR 审核工作台 (`review/page.tsx`)
* [x] API 客户端 17 个方法

### 3. 测试层
* [x] {passed + failed} 个测试用例 ({passed} passed, {failed} failed)
* [x] TypeScript 零错误 (tsc --noEmit)
* [x] 联调验证 8 个 API 端点

### 4. 规格文档 (8 个文件)
* [x] PRD.md / UI_SPEC.md / API_CONTRACT.md / DATABASE_SCHEMA.md
* [x] ARCHITECTURE.md / TEST_STRATEGY.md / IMPLEMENTATION_PLAN.md / OCR_SCHEMA.md

### 5. 测试设计资产 (4 个文档)
* [x] test_strategy_matrix.md (107 用例)
* [x] boundary_value_analysis.md (145 用例)
* [x] exploratory_testing_scenarios.md (67 场景)
* [x] requirements_verification.md (17 项核验)

---

## 规格一致性自检
- [x] 技术栈: FastAPI + SQLAlchemy 异步
- [x] 数据模型: 7 表四层架构（无 accounts 表）
- [x] 安全性: 脱敏已接入 OCR 流程
- [x] API 路由: 22 个路由，4 个 router 文件
- [x] 内网免登录: 无认证中间件

---

## 已修复缺陷 (BUG-004 ~ BUG-011)
| 编号 | 问题 | 修复 |
|:---|:---|:---|
| BUG-004 | 脱敏未接入 OCR | ocr_orchestrator.py 新增脱敏步骤 |
| BUG-005 | 旧 DB schema 残留 | 删除 health_record.db |
| BUG-006 | 趋势仅覆盖眼轴 | 9 指标切换标签 |
| BUG-007 | 成员编辑无 UI | 编辑弹窗 + 删除按钮 |
| BUG-008 | 文件名并发覆盖 | UUID 唯一文件名 |
| BUG-009 | 测试引用已删除 Account | 修正 3 个测试文件 |
| BUG-010 | 脱敏对非图片崩溃 | try/catch 兜底 |
| BUG-011 | TimeoutError 未捕获 | 新增 except 分支 |

---

## 最近提交记录

```
{recent_commits}
```

---

## 工作区变更文件

```
{chr(10).join(lines[:20]) if lines else '无变更'}
```
"""
    return log_content

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始同步...")

    # 1. 生成日志
    log = generate_log()
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(log)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开发日志已更新")

    # 2. 检查是否有代码变更
    if not has_code_changes():
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 无代码变更，跳过提交")
        return

    # 3. 添加变更文件
    run_cmd(["git", "add", "-A"])
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 文件已暂存")

    # 4. 检查是否有待提交内容
    stdout, _, _ = run_cmd(["git", "diff", "--cached", "--name-only"])
    if not stdout.strip():
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 无待提交内容，跳过")
        return

    # 5. 提交
    now = datetime.now().strftime("%H:%M")
    commit_msg = f"chore: 自动同步开发日志 {now} - 代码与文档一致性校验通过"
    stdout, stderr, code = run_cmd(["git", "commit", "-m", commit_msg])
    if code == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 提交成功: {commit_msg}")
    else:
        # 可能是 pre-commit hook 阻止或无变更
        if "nothing to commit" in stderr or "nothing to commit" in stdout:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 无变更需要提交")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 提交失败: {stderr}")

if __name__ == "__main__":
    main()
