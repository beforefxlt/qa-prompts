import sqlite3
import json

conn = sqlite3.connect('C:/Users/Administrator/qa-prompts/family_health_record_app/backend/health_record.db')
cur = conn.cursor()
cur.execute('SELECT processed_items FROM ocr_extraction_results WHERE document_id = ?', ('cfeccc25-383a-4de7-9a23-1e9c95c1de75',))
result = cur.fetchone()
if result:
    data = json.loads(result[0])
    print('Exam Date:', data.get('exam_date'))
    print('Institution:', data.get('institution'))
    print('Observations:')
    for obs in data.get('observations', []):
        print(f"  {obs.get('metric_code')}: {obs.get('value_numeric')} {obs.get('unit')} ({obs.get('side')})")
else:
    print('No result found')