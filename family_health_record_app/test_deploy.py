import requests
import json
import sys

def test_e2e():
    print('=== E2E Test Start ===')
    
    # 1. Check backend health
    r = requests.get('http://localhost:8001/health')
    print(f'[1] Backend Health: {r.json()}')
    
    # 2. Get existing members
    r = requests.get('http://localhost:8001/api/v1/members')
    members = r.json()
    print(f'[2] Existing Members: {len(members)}')
    
    # 3. Create a test member
    member_data = {
        'name': '测试用户',
        'gender': 'male',
        'date_of_birth': '2020-01-01',
        'member_type': 'child'
    }
    r = requests.post('http://localhost:8001/api/v1/members', json=member_data)
    if r.status_code == 201:
        member = r.json()
        print(f'[3] Created Member: {member["id"]} ({member["name"]})')
        member_id = member['id']
    else:
        print(f'[3] Create Member Failed: {r.status_code} {r.text}')
        return False
    
    # 4. Upload a test image
    test_image = 'C:/Users/Administrator/qa-prompts/family_health_record_app/tests/01.jpg'
    try:
        with open(test_image, 'rb') as f:
            files = {'file': ('test.jpg', f, 'image/jpeg')}
            data = {'member_id': member_id}
            r = requests.post('http://localhost:8001/api/v1/documents/upload', data=data, files=files)
        if r.status_code == 201:
            doc = r.json()
            print(f'[4] Uploaded Document: {doc["document_id"]}')
            doc_id = doc['document_id']
        else:
            print(f'[4] Upload Failed: {r.status_code} {r.text}')
            return False
    except Exception as e:
        print(f'[4] Upload Error: {e}')
        return False
    
    # 5. Trigger OCR
    print('[5] Triggering OCR (this may take 30+ seconds)...')
    r = requests.post(f'http://localhost:8001/api/v1/documents/{doc_id}/submit-ocr', timeout=120)
    if r.status_code == 200:
        ocr_result = r.json()
        print(f'[5] OCR Result: {ocr_result["status"]}')
    else:
        print(f'[5] OCR Failed: {r.status_code} {r.text}')
        return False
    
    # 6. Get review tasks
    r = requests.get('http://localhost:8001/api/v1/review-tasks')
    tasks = r.json()
    print(f'[6] Review Tasks: {len(tasks)}')
    
    if len(tasks) > 0:
        task_id = tasks[0]['id']
        
        # 7. Approve the task
        r = requests.post(f'http://localhost:8001/api/v1/review-tasks/{task_id}/approve', json={
            'revised_items': [
                {'metric_code': 'exam_date', 'value': '2026-03-31'},
                {'metric_code': 'axial_length', 'value_numeric': 24.35, 'unit': 'mm', 'side': 'right'},
                {'metric_code': 'axial_length', 'value_numeric': 23.32, 'unit': 'mm', 'side': 'left'}
            ]
        })
        if r.status_code == 200:
            approve_result = r.json()
            print(f'[7] Approve Result: {approve_result["status"]}')
        else:
            print(f'[7] Approve Failed: {r.status_code} {r.text}')
    
    # 8. Get trends
    r = requests.get(f'http://localhost:8001/api/v1/members/{member_id}/trends?metric=axial_length')
    if r.status_code == 200:
        trends = r.json()
        print(f'[8] Trends Data Points: {len(trends["series"])}')
        for point in trends['series']:
            print(f'    - {point["date"]}: {point["value"]}mm ({point["side"]})')
    else:
        print(f'[8] Trends Failed: {r.status_code}')
    
    print('=== E2E Test Complete ===')
    return True

if __name__ == '__main__':
    success = test_e2e()
    sys.exit(0 if success else 1)
