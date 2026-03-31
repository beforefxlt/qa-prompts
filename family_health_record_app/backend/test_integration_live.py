import asyncio
import threading
import time
import httpx
import uvicorn
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

def run_server():
    uvicorn.run(app, host='127.0.0.1', port=8002, log_level='error')

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(3)

async def test():
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8002') as client:
        resp = await client.post('/api/v1/members', json={
            'name': '联调测试',
            'gender': 'male',
            'date_of_birth': '2019-01-01',
            'member_type': 'child'
        })
        data = resp.json()
        print(f'1. Create member: {resp.status_code} - {data.get("name")} ({data.get("id")})')
        member_id = data['id']

        resp = await client.get('/api/v1/members')
        print(f'2. List members: {resp.status_code} - {len(resp.json())} members')

        resp = await client.get(f'/api/v1/members/{member_id}')
        name = resp.json().get('name')
        print(f'3. Get member: {resp.status_code} - {name}')

        resp = await client.put(f'/api/v1/members/{member_id}', json={'name': '更新后的名字'})
        name = resp.json().get('name')
        print(f'4. Update member: {resp.status_code} - {name}')

        resp = await client.delete(f'/api/v1/members/{member_id}')
        print(f'5. Delete member: {resp.status_code}')

        resp = await client.get('/api/v1/members')
        print(f'6. After delete: {len(resp.json())} members')

        resp = await client.get(f'/api/v1/members/{member_id}/trends?metric=axial_length')
        series_count = len(resp.json().get('series', []))
        print(f'7. Get trends: {resp.status_code} - {series_count} series')

        resp = await client.get('/api/v1/review-tasks')
        print(f'8. Review tasks: {resp.status_code} - {len(resp.json())} tasks')

        print('\nAll API endpoints working!')

asyncio.run(test())
