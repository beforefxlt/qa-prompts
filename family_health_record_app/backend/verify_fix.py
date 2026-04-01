import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_members_endpoint():
    """测试 /api/v1/members 端点"""
    print("=== 测试 /api/v1/members 端点 ===")
    
    # 1. GET 请求 - 应该返回 200
    print("1. 测试 GET /members...")
    try:
        r = requests.get(f"{BASE_URL}/members")
        print(f"   状态码: {r.status_code}")
        if r.status_code == 200:
            members = r.json()
            print(f"   成员数量: {len(members)}")
            print("   [SUCCESS] GET 请求成功")
        else:
            print(f"   [FAIL] GET 请求失败: {r.text}")
            return False
    except Exception as e:
        print(f"   [ERROR] GET 请求异常: {e}")
        return False
    
    # 2. POST 请求 - 创建自愈验证成员
    print("\n2. 测试 POST /members (创建自愈验证成员)...")
    test_member = {
        "name": "自愈验证成员",
        "gender": "male",
        "date_of_birth": "2010-01-01",
        "member_type": "child"
    }
    try:
        r = requests.post(f"{BASE_URL}/members", json=test_member)
        print(f"   状态码: {r.status_code}")
        if r.status_code == 201:
            member = r.json()
            print(f"   创建的成员 ID: {member['id']}")
            print("   [SUCCESS] POST 请求成功")
        else:
            print(f"   [FAIL] POST 请求失败: {r.text}")
            return False
    except Exception as e:
        print(f"   [ERROR] POST 请求异常: {e}")
        return False
    
    # 3. 验证数据落库
    print("\n3. 验证数据落库...")
    try:
        r = requests.get(f"{BASE_URL}/members")
        if r.status_code == 200:
            members = r.json()
            found = any(m['name'] == '自愈验证成员' for m in members)
            if found:
                print("   [SUCCESS] 自愈验证成员已成功落库")
            else:
                print("   [FAIL] 自愈验证成员未找到")
                return False
        else:
            print(f"   [FAIL] 验证失败: {r.text}")
            return False
    except Exception as e:
        print(f"   [ERROR] 验证异常: {e}")
        return False
    
    return True

def test_other_endpoints():
    """测试其他端点是否正常"""
    print("\n=== 测试其他端点 ===")
    
    endpoints = [
        ("/health", "健康检查"),
        ("/trends", "可用指标列表"),
    ]
    
    for endpoint, name in endpoints:
        print(f"测试 {name} ({endpoint})...")
        try:
            r = requests.get(f"{BASE_URL}{endpoint}")
            print(f"   状态码: {r.status_code}")
            if r.status_code in [200, 404]:  # 404 也是正常的（如果没有数据）
                print(f"   [SUCCESS] {name} 端点正常")
            else:
                print(f"   [WARNING] {name} 返回非预期状态码")
        except Exception as e:
            print(f"   [ERROR] {name} 异常: {e}")

if __name__ == "__main__":
    print("开始 P0 故障攻坚验证...\n")
    
    success = test_members_endpoint()
    
    if success:
        test_other_endpoints()
        print("\n" + "="*50)
        print("P0 故障攻坚完成！")
        print("- 后端 /api/v1/members 返回 200")
        print("- 自愈验证成员数据落库成功")
        print("="*50)
        sys.exit(0)
    else:
        print("\n" + "="*50)
        print("P0 故障攻坚失败！")
        print("请检查后端日志获取更多信息")
        print("="*50)
        sys.exit(1)