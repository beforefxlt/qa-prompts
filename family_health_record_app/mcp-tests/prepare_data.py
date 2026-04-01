import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def create_member(name):
    payload = {
        "name": name,
        "gender": "male",
        "date_of_birth": "2018-01-01",
        "member_type": "child"
    }
    response = requests.post(f"{BASE_URL}/members", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"CREATED:{name}:{data['id']}")
        return data['id']
    else:
        print(f"FAILED:{name}:{response.status_code}:{response.text}")
        return None

if __name__ == "__main__":
    # 创建指标测试成员
    m1 = create_member("指标测试成员")
    # 创建空数据成员
    m2 = create_member("空数据成员")
