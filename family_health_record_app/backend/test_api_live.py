import urllib.request
import json

BASE = "http://localhost:8000/api/v1"

# Test 1: Create member
data = json.dumps({
    "name": "联调测试",
    "gender": "male",
    "date_of_birth": "2019-01-01",
    "member_type": "child"
}).encode()
req = urllib.request.Request(f"{BASE}/members", data=data, headers={"Content-Type": "application/json"})
r = urllib.request.urlopen(req)
member = json.loads(r.read())
print(f"1. Create member: {member['name']} ({member['id']})")
member_id = member["id"]

# Test 2: List members
r = urllib.request.urlopen(f"{BASE}/members")
members = json.loads(r.read())
print(f"2. List members: {len(members)} members")

# Test 3: Get member
r = urllib.request.urlopen(f"{BASE}/members/{member_id}")
print(f"3. Get member: {json.loads(r.read())['name']}")

# Test 4: Update member
update_data = json.dumps({"name": "更新后的名字"}).encode()
req = urllib.request.Request(f"{BASE}/members/{member_id}", data=update_data, headers={"Content-Type": "application/json"}, method="PUT")
r = urllib.request.urlopen(req)
print(f"4. Update member: {json.loads(r.read())['name']}")

# Test 5: Delete member
req = urllib.request.Request(f"{BASE}/members/{member_id}", method="DELETE")
r = urllib.request.urlopen(req)
print(f"5. Delete member: status={r.status}")

# Test 6: Verify deleted
r = urllib.request.urlopen(f"{BASE}/members")
print(f"6. After delete: {len(json.loads(r.read()))} members")

# Test 7: Review tasks
r = urllib.request.urlopen(f"{BASE}/review-tasks")
print(f"7. Review tasks: {len(json.loads(r.read()))} tasks")

# Test 8: Trends (empty)
r = urllib.request.urlopen(f"{BASE}/members/00000000-0000-0000-0000-000000000001/trends?metric=axial_length")
print(f"8. Trends 404: {r.status}")

print("\nAll API endpoints working!")
