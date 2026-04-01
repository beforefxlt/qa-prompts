import re
import yaml
import os
from pathlib import Path

traceability_file = "family_health_record_app/traceability.yaml"
backend_test_dir = "family_health_record_app/backend/tests"
frontend_test_dir = "family_health_record_app/frontend/e2e"

def load_traceability():
    if not os.path.exists(traceability_file):
        return []
    with open(traceability_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def scan_tests():
    tc_found = {} # tc_id -> [files]
    
    # 扫描后端
    for p in Path(backend_test_dir).rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            matches = re.findall(r"TC-P[1-5]-\d{3}", content)
            for m in set(matches):
                tc_found.setdefault(m, []).append(str(p))
        except:
            pass

    # 扫描前端
    for p in Path(frontend_test_dir).rglob("*.ts"):
        try:
            content = p.read_text(encoding="utf-8")
            matches = re.findall(r"TC-P[1-5]-\d{3}", content)
            for m in set(matches):
                tc_found.setdefault(m, []).append(str(p))
        except:
            pass
            
    return tc_found

def audit():
    repo_data = load_traceability()
    found_tcs = scan_tests()
    
    total_expected = len(repo_data)
    expected_ids = {item['tc_id'] for item in repo_data}
    
    automated = []
    missing = []
    orphaned = []
    
    for item in repo_data:
        tc_id = item['tc_id']
        if tc_id in found_tcs:
            automated.append(tc_id)
        else:
            missing.append(tc_id)
            
    for tc_id in found_tcs:
        if tc_id not in expected_ids:
            orphaned.append(tc_id)
            
    print("="*40)
    print("QA Traceability & Coverage Audit")
    print("="*40)
    print(f"总 TC 数 (Specs): {total_expected}")
    print(f"已自动覆盖 (Code): {len(automated)}")
    print(f"覆盖缺口 (Missing): {len(missing)}")
    print(f"游离测试 (Orphaned): {len(orphaned)}")
    print("="*40)
    
    if missing:
        print("\n[缺失清单]")
        for m in missing[:10]: # 仅展示前10项
            print(f" - {m}")
        if len(missing) > 10:
            print(f" ... 还有 {len(missing)-10} 项")
            
    if orphaned:
        print("\n[游离/未定义清单 - 请在规格中补充]")
        for o in orphaned:
            print(f" - {o} Found in: {found_tcs[o]}")

    # 返回状态：如果有缺失或游离，可以作为门禁依据
    return len(missing) == 0 and len(orphaned) == 0

if __name__ == "__main__":
    audit()
