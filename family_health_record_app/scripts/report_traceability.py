import re
import yaml
import os
from pathlib import Path

# 配置路径
PROJECT_ROOT = Path("family_health_record_app")
TRACEABILITY_FILE = PROJECT_ROOT / "traceability.yaml"
BACKEND_TEST_DIR = PROJECT_ROOT / "backend/tests"
FRONTEND_TEST_DIR = PROJECT_ROOT / "frontend/e2e"

def load_yaml(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def scan_implemented_tcs():
    """扫描代码中已标记的测试用例"""
    implemented = {} # tc_id -> {file, name}
    
    # 统一扫描路径
    search_dirs = [BACKEND_TEST_DIR, FRONTEND_TEST_DIR]
    
    # 支持的正则表达式：[TC-P1-001] 或 TC-P1-001
    pattern = re.compile(r"TC-P[1-5]-\d{3}")

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        for p in search_dir.rglob("*"):
            if p.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
                
            try:
                content = p.read_text(encoding="utf-8")
                matches = pattern.findall(content)
                for tc_id in set(matches):
                    # 如果该 TC 尚未记录，或当前文件更具代表性
                    if tc_id not in implemented:
                        implemented[tc_id] = {
                            "test_file": str(p.relative_to(PROJECT_ROOT.parent)).replace("\\", "/"),
                            "status": "automated"
                        }
            except Exception as e:
                print(f"警告: 无法读取文件 {p}: {e}")
            
    return implemented

def sync():
    print(f"正在读取 {TRACEABILITY_FILE}...")
    traceability_data = load_yaml(TRACEABILITY_FILE)
    if not traceability_data:
        print("❌ 错误: 找不到可追溯性数据。请先运行 sync_traceability.py")
        return

    print("正在扫描代码库...")
    implemented = scan_implemented_tcs()
    print(f"找到 {len(implemented)} 个已实现的测试标识。")

    updated_count = 0
    for item in traceability_data:
        tc_id = item['tc_id']
        if tc_id in implemented:
            # 更新状态为 automated (如果当前是 pending)
            if item.get('status') == 'pending':
                item['status'] = 'automated'
                item['test_file'] = implemented[tc_id]['test_file']
                updated_count += 1
        else:
            # 如果没找到，且当前是 automated，重置为 pending
            if item.get('status') == 'automated':
                item['status'] = 'pending'
                item['test_file'] = ''
                updated_count += 1

    if updated_count > 0:
        save_yaml(TRACEABILITY_FILE, traceability_data)
        print(f"✅ 成功! 已更新 {updated_count} 条测试状态到 {TRACEABILITY_FILE}")
    else:
        print("ℹ️ 无需更新，状态已对齐。")

if __name__ == "__main__":
    sync()
