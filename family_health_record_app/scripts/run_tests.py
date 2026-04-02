"""
Docker 测试脚本 - 完整测试流程
1. 清理环境
2. 启动服务（使用空数据库）
3. 运行后端测试
4. 运行 E2E 测试（每个测试自动清理数据）
5. 输出测试报告
"""
import subprocess
import os
import sys
import time
import requests

INFRA_DIR = os.path.join(os.path.dirname(__file__), '..', 'infra')
API_BASE = "http://127.0.0.1:8000/api/v1"

def run_cmd(cmd, cwd=None, check=True):
    print(f"\n>>> {cmd}")
    return subprocess.run(cmd, shell=True, cwd=cwd or INFRA_DIR, check=check)

def wait_for_service(url, name, timeout=120):
    print(f"等待 {name} 启动: {url}")
    for i in range(timeout):
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print(f"✅ {name} 已就绪")
                return True
        except:
            pass
        if i % 10 == 0 and i > 0:
            print(f"  等待中... ({i}s)")
        time.sleep(1)
    print(f"❌ {name} 启动超时")
    return False

def clean_database():
    """清理数据库所有数据"""
    try:
        res = requests.get(f"{API_BASE}/members")
        if res.ok:
            members = res.json()
            for m in members:
                requests.delete(f"{API_BASE}/members/{m['id']}")
            print(f"✅ 已清理 {len(members)} 条成员数据")
    except Exception as e:
        print(f"⚠️ 清理数据库失败: {e}")

def main():
    print("\n" + "="*60)
    print(">>> Docker 完整测试流程 <<<")
    print("="*60)
    
    # 1. 停止旧容器
    print("\n[1/6] 清理旧容器...")
    run_cmd("docker compose down", check=False)
    
    # 2. 启动服务
    print("\n[2/6] 启动服务...")
    run_cmd("docker compose up -d")
    
    # 3. 等待后端就绪
    print("\n[3/6] 等待服务就绪...")
    if not wait_for_service(f"{API_BASE}/health", "后端", timeout=60):
        print("\n查看后端日志:")
        run_cmd("docker compose logs backend --tail 50", check=False)
        return False
    
    # 等待前端构建
    print("\n等待前端构建（约 60-120 秒）...")
    time.sleep(60)
    if not wait_for_service("http://127.0.0.1:3001", "前端", timeout=120):
        print("\n查看前端日志:")
        run_cmd("docker compose logs frontend --tail 50", check=False)
    
    # 4. 清理数据库（确保空状态）
    print("\n[4/6] 清理数据库...")
    clean_database()
    
    # 5. 运行后端测试
    print("\n[5/6] 运行后端单元测试...")
    result = run_cmd(
        "docker exec health-record-backend python -m pytest tests/ -v --tb=short",
        check=False
    )
    backend_passed = result.returncode == 0
    
    # 6. 运行 E2E 测试
    print("\n[6/6] 运行 E2E 测试...")
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    os.environ["PLAYWRIGHT_BASE_URL"] = "http://localhost:3001"
    result = run_cmd(
        "npx playwright test --reporter=list",
        cwd=frontend_dir,
        check=False
    )
    e2e_passed = result.returncode == 0
    
    # 输出结果
    print("\n" + "="*60)
    print(">>> 测试结果汇总 <<<")
    print("="*60)
    print(f"后端测试: {'✅ 通过' if backend_passed else '❌ 失败'}")
    print(f"E2E 测试: {'✅ 通过' if e2e_passed else '❌ 失败'}")
    
    # 服务状态
    print("\n服务状态:")
    run_cmd("docker compose ps", check=False)
    
    print("\n访问地址:")
    print("  - 前端: http://localhost:3001")
    print("  - 后端: http://localhost:8000")
    print("  - API 文档: http://localhost:8000/docs")
    
    return backend_passed and e2e_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
