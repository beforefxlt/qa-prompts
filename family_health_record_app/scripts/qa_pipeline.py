"""
统一 QA Pipeline - 支持本地和 Docker 两种模式
合并了原 qa_pipeline.py 和 docker_qa_pipeline.py

使用方式:
  python scripts/qa_pipeline.py --mode docker    # Docker 启动后端 + 本地 npm run dev 启动前端 + 跑测试
  python scripts/qa_pipeline.py --mode local     # 全本地启动（SQLite 测试库）
  python scripts/qa_pipeline.py --mode e2e       # 仅启动服务跑 E2E，不跑 UT
  python scripts/qa_pipeline.py --mode dev       # 仅启动开发环境（db/minio/backend），前端需手动 npm run dev
"""
import subprocess
import os
import sys
import time
import argparse
import requests


def run_command(command, cwd=None, env=None):
    print(f"\n执行命令: {command} (目录: {cwd or '.'})")
    try:
        subprocess.run(command, shell=True, cwd=cwd, check=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        return False


def kill_port(port):
    """杀掉占用指定端口的进程"""
    try:
        netstat_out = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
        for line in netstat_out.splitlines():
            if "LISTENING" in line:
                pid = line.strip().split()[-1]
                if str(pid) != str(os.getpid()):
                    print(f"杀灭残留进程 PID: {pid} (端口 {port})")
                    os.system(f'taskkill /f /pid {pid} /t >nul 2>&1')
    except:
        pass


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


def get_project_root():
    """获取项目根目录"""
    return os.getcwd()


def get_infra_dir():
    return os.path.join(get_project_root(), "family_health_record_app", "infra")


def get_frontend_dir():
    return os.path.join(get_project_root(), "family_health_record_app", "frontend")


def get_backend_dir():
    return os.path.join(get_project_root(), "family_health_record_app", "backend")


def docker_mode():
    """
    Docker 模式：
    1. Docker 启动 db/minio/backend
    2. 本地 npm run dev 启动前端（热重载）
    3. 跑后端 UT + E2E 测试
    """
    print("\n[Docker 模式] Docker 启动后端 + 本地 dev 启动前端 + 跑测试")
    
    infra_dir = get_infra_dir()
    frontend_dir = get_frontend_dir()
    backend_dir = get_backend_dir()
    
    # 1. 检查 Docker
    print("\n[1/7] 检查 Docker 环境...")
    try:
        subprocess.run("docker info", shell=True, check=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        print("❌ Docker 未运行，请先启动 Docker Desktop")
        return False
    
    # 2. 停止旧容器
    print("\n[2/7] 清理旧容器...")
    subprocess.run("docker compose down", shell=True, cwd=infra_dir,
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 3. 启动 Docker 服务（db/minio/backend，不启动前端）
    print("\n[3/7] 启动 Docker 服务（db/minio/backend）...")
    if not run_command("docker compose up -d db minio backend", cwd=infra_dir):
        return False
    
    # 4. 等待后端就绪
    print("\n[4/7] 等待后端服务启动...")
    if not wait_for_service("http://127.0.0.1:8000/api/v1/health", timeout=120, service_name="后端"):
        print("\n查看后端日志:")
        subprocess.run("docker compose logs backend --tail 50", shell=True, cwd=infra_dir)
        return False
    
    # 5. 启动前端 dev server
    print("\n[5/7] 启动前端开发服务器（npm run dev）...")
    frontend_proc = subprocess.Popen(
        [sys.executable, "-m", "npx", "next", "dev", "-p", "3001"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    if not wait_for_service("http://127.0.0.1:3001", timeout=60, service_name="前端"):
        print("❌ 前端启动超时")
        frontend_proc.terminate()
        return False
    
    # 6. 运行后端 UT
    print("\n[6/7] 运行后端单元测试...")
    run_command(
        "docker exec health-record-backend python -m pytest tests/ -v --tb=short",
        cwd=infra_dir
    )
    
    # 7. 运行 E2E 测试
    print("\n[7/7] 运行 E2E 测试...")
    os.environ["PLAYWRIGHT_BASE_URL"] = "http://localhost:3001"
    run_command("npx playwright test --reporter=list", cwd=frontend_dir)
    
    # 清理
    print("\n正在关闭前端开发服务器...")
    frontend_proc.terminate()
    try:
        frontend_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        frontend_proc.kill()
    
    # 显示状态
    print("\n" + "="*60)
    print(">>> 服务状态 <<<")
    print("="*60)
    subprocess.run("docker compose ps", shell=True, cwd=infra_dir)
    
    return True


def local_mode():
    """
    本地模式：
    全本地启动（SQLite 测试库），无需 Docker
    """
    print("\n[本地模式] 全本地运行（SQLite 测试库）")
    
    backend_dir = get_backend_dir()
    frontend_dir = get_frontend_dir()
    
    # 1. 环境预洗
    print("\n[环境预洗] 正在清理测试环境...")
    kill_port(8000)
    kill_port(3001)
    
    e2e_db = os.path.join(backend_dir, "e2e_test.db")
    if os.path.exists(e2e_db):
        print(f"清理旧数据库文件: {e2e_db}")
        os.remove(e2e_db)
    
    # 2. 运行后端 UT
    print("\n运行后端单元测试...")
    run_command("pytest --maxfail=5 --disable-warnings", cwd=backend_dir)
    
    # 3. 启动后端服务器
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
    
    # 4. 等待后端就绪
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
    
    # 5. 启动前端 dev server
    if ready:
        print("\n启动前端开发服务器...")
        frontend_proc = subprocess.Popen(
            [sys.executable, "-m", "npx", "next", "dev", "-p", "3001"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if wait_for_service("http://127.0.0.1:3001", timeout=60, service_name="前端"):
            # 6. 运行 E2E 测试
            print("\n运行 E2E 测试...")
            os.environ["PLAYWRIGHT_BASE_URL"] = "http://localhost:3001"
            run_command("npx playwright test --reporter=list", cwd=frontend_dir)
        
        print("\n正在关闭前端开发服务器...")
        frontend_proc.terminate()
        try:
            frontend_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            frontend_proc.kill()
    
    # 6. 清理
    print("\n正在关闭后端测试服务器...")
    backend_proc.terminate()
    try:
        backend_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.system(f'taskkill /f /pid {backend_proc.pid} /t >nul 2>&1')
    
    return ready


def e2e_mode():
    """
    E2E 模式：
    仅启动服务跑 E2E，不跑 UT
    """
    print("\n[E2E 模式] 启动服务 + 运行 E2E 测试（跳过 UT）")
    
    infra_dir = get_infra_dir()
    frontend_dir = get_frontend_dir()
    
    # 1. 检查 Docker
    print("\n[1/4] 检查 Docker 环境...")
    try:
        subprocess.run("docker info", shell=True, check=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        print("❌ Docker 未运行，请先启动 Docker Desktop")
        return False
    
    # 2. 启动 Docker 服务
    print("\n[2/4] 启动 Docker 服务...")
    if not run_command("docker compose up -d db minio backend", cwd=infra_dir):
        return False
    
    # 3. 等待后端就绪
    print("\n[3/4] 等待后端服务启动...")
    if not wait_for_service("http://127.0.0.1:8000/api/v1/health", timeout=120, service_name="后端"):
        print("\n查看后端日志:")
        subprocess.run("docker compose logs backend --tail 50", shell=True, cwd=infra_dir)
        return False
    
    # 4. 启动前端 dev server
    print("\n[4/4] 启动前端开发服务器 + 运行 E2E 测试...")
    frontend_proc = subprocess.Popen(
        [sys.executable, "-m", "npx", "next", "dev", "-p", "3001"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    if not wait_for_service("http://127.0.0.1:3001", timeout=60, service_name="前端"):
        print("❌ 前端启动超时")
        frontend_proc.terminate()
        return False
    
    # 运行 E2E 测试
    os.environ["PLAYWRIGHT_BASE_URL"] = "http://localhost:3001"
    run_command("npx playwright test --reporter=list", cwd=frontend_dir)
    
    # 清理
    print("\n正在关闭前端开发服务器...")
    frontend_proc.terminate()
    try:
        frontend_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        frontend_proc.kill()
    
    return True


def dev_mode():
    """
    开发模式：
    仅启动开发环境（db/minio/backend），前端需手动 npm run dev
    """
    print("\n[开发模式] 启动 db/minio/backend，前端请手动运行:")
    print("  cd family_health_record_app/frontend && npm run dev -- -p 3001")
    
    infra_dir = get_infra_dir()
    
    # 1. 检查 Docker
    print("\n[1/3] 检查 Docker 环境...")
    try:
        subprocess.run("docker info", shell=True, check=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        print("❌ Docker 未运行，请先启动 Docker Desktop")
        return False
    
    # 2. 启动 Docker 服务
    print("\n[2/3] 启动 Docker 服务（db/minio/backend）...")
    if not run_command("docker compose up -d db minio backend", cwd=infra_dir):
        return False
    
    # 3. 等待后端就绪
    print("\n[3/3] 等待后端服务启动...")
    if not wait_for_service("http://127.0.0.1:8000/api/v1/health", timeout=120, service_name="后端"):
        print("\n查看后端日志:")
        subprocess.run("docker compose logs backend --tail 50", shell=True, cwd=infra_dir)
        return False
    
    print("\n" + "="*60)
    print(">>> 开发环境已就绪 <<<")
    print("="*60)
    print("\n访问地址:")
    print("  - 后端 API: http://localhost:8000")
    print("  - API 文档: http://localhost:8000/docs")
    print("  - MinIO 控制台: http://localhost:9001")
    print("\n请在新终端运行以下命令启动前端:")
    print("  cd family_health_record_app/frontend && npm run dev -- -p 3001")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="QA Pipeline - 统一测试流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/qa_pipeline.py --mode docker    # Docker 后端 + 本地前端 + 全量测试
  python scripts/qa_pipeline.py --mode local     # 全本地 SQLite + 全量测试
  python scripts/qa_pipeline.py --mode e2e       # 仅启动服务跑 E2E
  python scripts/qa_pipeline.py --mode dev       # 仅启动开发环境
        """
    )
    parser.add_argument(
        "--mode",
        choices=["docker", "local", "e2e", "dev"],
        default="docker",
        help="运行模式: docker (Docker 后端 + 本地前端 + 测试), local (全本地), e2e (仅 E2E), dev (仅开发环境)"
    )
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print(f">>> [QA Pipeline Start] 模式: {args.mode} <<<")
    print("="*60)
    
    mode_map = {
        "docker": docker_mode,
        "local": local_mode,
        "e2e": e2e_mode,
        "dev": dev_mode,
    }
    
    success = mode_map[args.mode]()
    
    print("\n" + "="*60)
    print(">>> [QA Pipeline Complete] <<<")
    print("="*60)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
