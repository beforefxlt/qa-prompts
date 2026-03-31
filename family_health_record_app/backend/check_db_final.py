import sqlite3
import json

def check_db_final():
    try:
        conn = sqlite3.connect("health_record.db")
        cursor = conn.cursor()
        
        # 1. 检查最新的 OCR 原始 JSON (确认正则提取结果)
        cursor.execute("SELECT raw_json, created_at FROM ocr_extraction_results ORDER BY created_at DESC LIMIT 1;")
        row = cursor.fetchone()
        if row:
            print("\n--- [SUCCESS] Latest AI OCR Data Found ---")
            print(f"Time: {row[1]}")
            # 美化输出 JSON
            data = json.loads(row[0])
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("No OCR results found.")
            
        # 2. 检查最近插入的侧量物理指标 (由于表名是 observations, 我们查 metric_code 和 value)
        cursor.execute("SELECT metric_code, value_numeric, side, created_at FROM observations ORDER BY created_at DESC LIMIT 4;")
        rows = cursor.fetchall()
        print("\n--- Latest Database Indicators ---")
        for r in rows:
            print(f"Time: {r[3]}, Metric: {r[0]}, Value: {r[1]}, Side: {r[2]}")
            
        conn.close()
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    check_db_final()
