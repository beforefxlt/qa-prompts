import sqlite3
import json

def check_db():
    try:
        conn = sqlite3.connect("health_record.db")
        cursor = conn.cursor()
        
        # 1. 检查 OCR 结果
        cursor.execute("SELECT raw_json, created_at FROM ocr_extraction_results ORDER BY created_at DESC LIMIT 1;")
        row = cursor.fetchone()
        if row:
            print("\n--- Latest OCR Raw Result ---")
            print(f"Created At: {row[1]}")
            print(row[0])
        else:
            print("No OCR results found.")
            
        # 2. 检查生成的测量值
        cursor.execute("SELECT metric_code, value_numeric, side, exam_date FROM observations ORDER BY created_at DESC LIMIT 2;")
        rows = cursor.fetchall()
        print("\n--- Latest Observations ---")
        for r in rows:
            print(f"Date: {r[3]}, Metric: {r[0]}, Value: {r[1]}, Side: {r[2]}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
