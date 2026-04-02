"""
Docker 环境测试脚本
基于预构建镜像运行完整的测试流程
"""
import subprocess
import os
import sys
import time
import requests

def run_command(command, cwd=None):
    print(f"\n执行命令: {command}")
    try:
        subprocess.run(command, shell=True, cwd=cwd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        return False

def check_docker_running():
    """检查 Docker 是否运行"""
    try:
        subprocess.run("docker info", shell=True, check=True, 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def wait_for_service(url, timeout=60, service_name="服务"):
    """等待服务启动"""
    print(f"等待 {service_name} 启动: {url}")
    for i in range(timeout):
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print(f"✅ {service_name} 已就绪")
                return True
        except:
            pass
        time.sleep(1)
    print(f"❌ {service_name} 启动超时")
    return False

def main():
    print("\n" + "="*60)
    print(">>> [Docker QA Pipeline Start] <<<")
    print("="*60)
    
    infra_dir = os.path.join(os.getcwd(), "family_health_record_app", "infra")
    
    # 1. 检查 Docker
    print("\n[1/6] 检查 Docker 环境...")
    if not check_docker_running():
        print("❌ Docker 未运行，请先启动 Docker Desktop")
        return False
    
    # 2. 停止旧容器
    print("\n[2/6] 清理旧容器...")
    subprocess.run("docker compose down", shell=True, cwd=infra_dir, 
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 3. 启动服务
    print("\n[3/6] 启动 Docker 服务...")
    if not run_command("docker compose up -d", cwd=infra_dir):
        return False
    
    # 4. 等待服务就绪
    print("\n[4/6] 等待服务启动...")
    time.sleep(5)  # 给容器初始化时间
    
    backend_ready = wait_for_service(
        "http://127.0.0.1:8000/api/v1/health",
        timeout=120,
        service_name="后端"
    )
    
    if not backend_ready:
        print("\n查看后端日志:")
        subprocess.run("docker compose logs backend --tail 50", shell=True, cwd=infra_dir)
        return False
    
    # 等待前端构建
    print("\n等待前端构建完成（可能需要 1-2 分钟）...")
    time.sleep(60)
    
    frontend_ready = wait_for_service(
        "http://127.0.0.1:3001",
        timeout=120,
        service_name="前端"
    )
    
    if not frontend_ready:
        print("\n查看前端日志:")
        subprocess.run("docker compose logs frontend --tail 50", shell=True, cwd=infra_dir)
    
    # 5. 运行后端测试
    print("\n[5/6] 运行后端单元测试...")
    run_command(
        "docker exec health-record-backend python -m pytest tests/ -v --tb=short",
        cwd=infra_dir
    )
    
    # 6. 运行 E2E 测试
    print("\n[6/6] 运行 E2E 测试...")
    frontend_dir = os.path.join(os.getcwd(), "family_health_record_app", "frontend")
    
    # 设置 Playwright baseURL
    os.environ["PLAYWRIGHT_BASE_URL"] = "http://localhost:3001"
    
    run_command("npx playwright test --reporter=list", cwd=frontend_dir)
    
    # 显示服务状态
    print("\n" + "="*60)
    print(">>> 服务状态 <<<")
    print("="*60)
    subprocess.run("docker compose ps", shell=True, cwd=infra_dir)
    
    print("\n" + "="*60)
    print(">>> [Docker QA Pipeline Complete] <<<")
    print("="*60)
    print("\n访问地址:")
    print("  - 前端: http://localhost:3001")
    print("  - 后端: http://localhost:8000")
    print("  - API 文档: http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
