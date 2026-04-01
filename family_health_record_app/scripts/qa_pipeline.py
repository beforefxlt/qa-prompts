import subprocess
import os
import sys
import time

def run_command(command, cwd=None, env=None):
    print(f"\n执行命令: {command} (目录: {cwd or '.'})")
    try:
        subprocess.run(command, shell=True, cwd=cwd, check=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        return False

def main():
    print("\n" + "="*50)
    print(">>> [QA Pipeline Start] <<<")
    print("="*50)

    # 1. 环境预洗
    print("\n[环境预洗] 正在清理测试环境...")
    try:
        # 杀掉占用 8000 端口的进程，确保后端重启
        netstat_out = subprocess.check_output('netstat -ano | findstr :8000', shell=True).decode()
        for line in netstat_out.splitlines():
            if "LISTENING" in line:
                pid = line.strip().split()[-1]
                if str(pid) != str(os.getpid()):
                    print(f"杀灭残留后端进程 PID: {pid}")
                    os.system(f'taskkill /f /pid {pid} /t >nul 2>&1')
    except:
        pass

    e2e_db = "family_health_record_app/backend/e2e_test.db"
    if os.path.exists(e2e_db):
        print(f"清理旧数据库文件: {e2e_db}")
        os.remove(e2e_db)

    # 2. 同步契约
    run_command("python family_health_record_app/scripts/sync_traceability.py")

    # 3. 运行后端测试 (Pytest)
    backend_dir = os.path.join(os.getcwd(), "family_health_record_app", "backend")
    run_command("pytest --maxfail=5 --disable-warnings", cwd=backend_dir)

    # 4. 启动后端 E2E 服务器
    print("\n[E2E] 启动后端测试服务器...")
    env = os.environ.copy()
    # [核心修复] 使用异步驱动 aiosqlite 以适配后端的 create_async_engine
    env["DATABASE_URL"] = "sqlite+aiosqlite:///e2e_test.db"
    env["PYTHONPATH"] = backend_dir 
    
    # 使用 sys.executable -m uvicorn 规避 Windows 的命令查找问题
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000", "--host", "127.0.0.1"],
        cwd=backend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # 5. 等待健康检查
    import requests
    ready = False
    print("正在等待后端服务响应 (http://127.0.0.1:8000/api/v1/health)...")
    for i in range(15):
        try:
            r = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=1)
            if r.status_code == 200:
                print("后端服务已在线，开始运行 E2E...")
                ready = True
                break
        except:
            pass
        # 轮询期间检查进程是否已崩
        if backend_proc.poll() is not None:
            _, err = backend_proc.communicate()
            print(f"错误：后端进程意外退出。错误详情:\n{err.decode()}")
            break
        time.sleep(1)

    try:
        if ready:
            frontend_dir = os.path.join(os.getcwd(), "family_health_record_app", "frontend")
            # 运行 Playwright
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

    print("\n" + "="*50)
    print(">>> [QA Pipeline Complete] <<<")
    print("="*50)

if __name__ == "__main__":
    main()
