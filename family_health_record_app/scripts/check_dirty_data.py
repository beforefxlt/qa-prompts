#!/usr/bin/env python3
"""
部署前脏数据检查脚本 (Pre-Deploy Dirty Data Check)
用法:
  python scripts/check_dirty_data.py              # 检查模式（只报告）
  python scripts/check_dirty_data.py --clean      # 清理模式（自动清空）
  python scripts/check_dirty_data.py --via-admin  # 通过 admin/reset 端点清理（推荐）

集成到部署流程：
  - 在 build_docker.py / qa_pipeline.py 的 deploy 阶段前调用
  - 检查模式返回非零退出码时阻断部署
"""
import sys
import os
import json
import subprocess

DB_CONFIG = {
    "user": "health_record",
    "password": "health_record_password",
    "dbname": "health_record",
    "container": "health-record-db",
}

BUSINESS_TABLES = [
    "derived_metrics",
    "observations",
    "exam_records",
    "ocr_extraction_results",
    "review_tasks",
    "document_records",
    "member_profiles",
]

DIRTY_DATA_THRESHOLD = 0


def run_psql(query):
    cmd = "docker exec " + DB_CONFIG["container"] + " psql -U " + DB_CONFIG["user"] + " -d " + DB_CONFIG["dbname"] + " -c \"" + query + "\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return None, result.stderr.strip()
    return result.stdout.strip(), None


def check_dirty_data():
    sep = "=" * 60
    print(sep)
    print(">>> 部署前脏数据检查 <<<")
    print(sep)

    status = subprocess.run(
        "docker inspect -f '{{.State.Running}}' " + DB_CONFIG["container"],
        shell=True, capture_output=True, text=True
    )
    if "true" not in status.stdout.strip().lower():
        print("[WARN] 数据库容器 " + DB_CONFIG["container"] + " 未运行，跳过检查")
        return True

    total_dirty = 0
    table_counts = {}

    for table in BUSINESS_TABLES:
        query = "SELECT count(*) FROM " + table
        output, err = run_psql(query)
        if err:
            print("[ERROR] 查询 " + table + " 失败: " + err)
            return False
        count = int(output.strip()) if output.strip().isdigit() else 0
        table_counts[table] = count
        total_dirty += count

    print()
    header = "{:<30} {:>8}".format("表名", "记录数")
    print(header)
    print("-" * 40)
    for table, count in table_counts.items():
        icon = "OK" if count == 0 else "FAIL"
        row = "[{}] {:<25} {:>8}".format(icon, table, count)
        print(row)

    print("-" * 40)
    total_icon = "OK" if total_dirty == 0 else "FAIL"
    total_row = "[{}] {:<25} {:>8}".format(total_icon, "总计", total_dirty)
    print(total_row)
    print()

    if total_dirty > DIRTY_DATA_THRESHOLD:
        print("[FAIL] 发现 " + str(total_dirty) + " 条脏数据，阻断部署！")
        print()
        print("处理建议:")
        print("  1. 清理脏数据: python scripts/check_dirty_data.py --clean")
        print("  2. 通过 admin 端点清理: python scripts/check_dirty_data.py --via-admin")
        print()
        return False

    print("[PASS] 数据库干净，可以部署")
    return True


def clean_via_psql():
    print(">>> 通过 psql 清理脏数据 <<<")
    for table in BUSINESS_TABLES:
        query = "DELETE FROM " + table
        output, err = run_psql(query)
        if err:
            print("[ERROR] 清理 " + table + " 失败: " + err)
            return False
        count = output.strip() if output.strip().isdigit() else "0"
        print("  清理 " + table + ": " + count + " 条")
    print("[PASS] 所有表已清空")
    return True


def clean_via_admin():
    print(">>> 通过 admin/reset 端点清理 <<<")
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/admin/reset",
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("status") == "ok":
                print("[PASS] " + data.get("message", "清理成功"))
                return True
            print("[FAIL] 清理失败: " + str(data))
            return False
    except Exception as e:
        print("[ERROR] 调用 admin/reset 失败: " + str(e))
        print("  请确认后端服务正在运行 (http://localhost:8000)")
        return False


def main():
    args = sys.argv[1:]
    clean_mode = "--clean" in args
    via_admin = "--via-admin" in args

    if clean_mode:
        success = clean_via_psql()
    elif via_admin:
        success = clean_via_admin()
    else:
        success = check_dirty_data()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
