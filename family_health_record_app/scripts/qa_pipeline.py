"""
QA Pipeline - 支持本地和 Docker 两种模式
"""
import subprocess
import os
import sys
import time
import argparse

def run_command(command, cwd=None, env=None):
    print(f"\n执行命令: {command} (目录: {cwd or '.'})")
    try:
        subprocess.run(command, shell=True, cwd=cwd, check=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        return False

def kill_port_8000():
    """杀掉占用 8000 端口的进程"""
    try:
        netstat_out = subprocess.check_output('netstat -ano | findstr :8000', shell=True).decode()
        for line in netstat_out.splitlines():
            if "LISTENING" in line:
                pid = line.strip().split()[-1]
                if str(pid) != str(os.getpid()):
                    print(f"杀灭残留后端进程 PID: {pid}")
                    os.system(f'taskkill /f /pid {pid} /t >nul 2>&1')
    except:
        pass

def docker_mode():
    """Docker 模式：使用预构建镜像"""
    print("\n[Docker 模式] 使用预构建镜像运行测试...")
    
    infra_dir = os.path.join(os.getcwd(), "family_health_record_app", "infra")
    
    # 检查 Docker
    try:
        subprocess.run("docker info", shell=True, check=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        print("❌ Docker 未运行，请先启动 Docker Desktop")
        return False
    
    # 停止旧容器
    subprocess.run("docker compose down", shell=True, cwd=infra_dir,
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 启动服务
    print("\n启动 Docker 服务...")
    if not run_command("docker compose up -d", cwd=infra_dir):
        return False
    
    # 等待后端就绪
    import requests
    print("\n等待后端服务启动...")
    time.sleep(10)
    
    for i in range(60):
        try:
            r = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=2)
            if r.status_code == 200:
                print("✅ 后端已就绪")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("❌ 后端启动超时")
        subprocess.run("docker compose logs backend --tail 30", shell=True, cwd=infra_dir)
        return False
    
    # 运行后端测试
    print("\n运行后端单元测试...")
    run_command(
        "docker exec health-record-backend python -m pytest tests/ -v --tb=short",
        cwd=infra_dir
    )
    
    # 等待前端构建
    print("\n等待前端构建...")
    time.sleep(60)
    
    # 运行 E2E 测试
    print("\n运行 E2E 测试...")
    frontend_dir = os.path.join(os.getcwd(), "family_health_record_app", "frontend")
    os.environ["PLAYWRIGHT_BASE_URL"] = "http://localhost:3001"
    run_command("npx playwright test --reporter=list", cwd=frontend_dir)
    
    # 显示状态
    print("\n服务状态:")
    subprocess.run("docker compose ps", shell=True, cwd=infra_dir)
    
    return True

def local_mode():
    """本地模式：直接启动后端服务器"""
    print("\n[本地模式] 直接运行测试...")
    
    import requests
    
    # 1. 环境预洗
    print("\n[环境预洗] 正在清理测试环境...")
    kill_port_8000()
    
    e2e_db = "family_health_record_app/backend/e2e_test.db"
    if os.path.exists(e2e_db):
        print(f"清理旧数据库文件: {e2e_db}")
        os.remove(e2e_db)
    
    # 2. 同步契约
    run_command("python family_health_record_app/scripts/sync_traceability.py")
    
    # 3. 运行后端测试
    backend_dir = os.path.join(os.getcwd(), "family_health_record_app", "backend")
    run_command("pytest --maxfail=5 --disable-warnings", cwd=backend_dir)
    
    # 4. 启动后端服务器
    print("\n[E2E] 启动后端测试服务器...")
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite+aiosqlite:///./e2e_test.db"
    env["PYTHONPATH"] = backend_dir
    
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000", "--host", "127.0.0.1"],
        cwd=backend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 5. 等待健康检查
    ready = False
    print("正在等待后端服务响应...")
    for i in range(30):
        try:
            r = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=2)
            if r.status_code == 200:
                print("✅ 后端服务已在线")
                ready = True
                break
        except Exception as e:
            print(f"健康检查异常 (尝试 {i+1}/30): {e}")
        if backend_proc.poll() is not None:
            _, err = backend_proc.communicate()
            print(f"错误：后端进程意外退出。\n{err.decode()}")
            break
        time.sleep(1)
    
    try:
        if ready:
            frontend_dir = os.path.join(os.getcwd(), "family_health_record_app", "frontend")
            run_command("npx playwright test", cwd=frontend_dir)
        else:
            print("错误：后端启动超时。")
    finally:
        print("\n正在收割测试服务器...")
        backend_proc.terminate()
        try:
            backend_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.system(f'taskkill /f /pid {backend_proc.pid} /t >nul 2>&1')
    
    return ready

def main():
    parser = argparse.ArgumentParser(description="QA Pipeline - 支持本地和 Docker 模式")
    parser.add_argument("--mode", choices=["docker", "local"], default="docker",
                       help="运行模式: docker (使用预构建镜像) 或 local (本地直接运行)")
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print(f">>> [QA Pipeline Start] 模式: {args.mode} <<<")
    print("="*60)
    
    if args.mode == "docker":
        success = docker_mode()
    else:
        success = local_mode()
    
    print("\n" + "="*60)
    print(">>> [QA Pipeline Complete] <<<")
    print("="*60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
