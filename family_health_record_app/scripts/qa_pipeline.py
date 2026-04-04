"""
统一 QA Pipeline - 支持本地和 Docker 两种模式，支持用例分类筛选

使用方式:
  python scripts/qa_pipeline.py --mode docker    # Docker 启动后端 + 本地前端 + 全量测试
  python scripts/qa_pipeline.py --mode local     # 全本地启动（SQLite 测试库）
  python scripts/qa_pipeline.py --mode e2e       # 仅启动服务跑 E2E，不跑 UT
  python scripts/qa_pipeline.py --mode dev       # 仅启动开发环境（db/minio/backend），前端需手动 npm run dev

用例筛选:
  python scripts/qa_pipeline.py --mode e2e --tags critical          # 仅跑 E2E 核心链路
  python scripts/qa_pipeline.py --mode e2e --tags smoke             # 仅跑冒烟测试
  python scripts/qa_pipeline.py --mode e2e --tags regression        # 仅跑回归测试
  python scripts/qa_pipeline.py --mode local --run-ut               # 仅跑 UT
  python scripts/qa_pipeline.py --mode local --exclude "ux"         # 排除 UX 测试
  python scripts/qa_pipeline.py --mode e2e --spec "upload*"         # 仅跑上传相关

测试分类标签:
  critical   - 核心链路（上传→OCR→审核→仪表盘）
  smoke      - 冒烟测试
  regression - 回归测试
  ut         - 单元测试（后端 + 移动端）
"""
import subprocess
import os
import sys
import time
import argparse
import requests
import fnmatch


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
    return os.path.join(get_project_root(), "infra")


def get_frontend_dir():
    return os.path.join(get_project_root(), "frontend")


def get_backend_dir():
    return os.path.join(get_project_root(), "backend")


def get_mobile_dir():
    return os.path.join(get_project_root(), "mobile_app")


def build_e2e_command(tags=None, spec=None, exclude=None):
    """构建 Playwright 测试命令"""
    cmd = "npx playwright test --reporter=list"
    
    if tags:
        tag_list = tags.split(",")
        grep_patterns = []
        for tag in tag_list:
            tag = tag.strip()
            if tag == "ut":
                continue
            grep_patterns.append(tag)
        if grep_patterns:
            grep_str = "|".join(grep_patterns)
            cmd = f'npx playwright test --reporter=list --grep "{grep_str}"'
    
    if spec:
        cmd = f"npx playwright test --reporter=list {spec}"
    
    if exclude:
        exclude_list = exclude.split(",")
        exclude_str = " ".join([f"--ignore=e2e/{e}.spec.ts" for e in exclude_list])
        cmd = f"npx playwright test --reporter=list {exclude_str}"
    
    return cmd


def build_ut_command(tags=None, spec=None, exclude=None, backend_only=False, mobile_only=False):
    """构建 UT 测试命令"""
    backend_dir = get_backend_dir()
    mobile_dir = get_mobile_dir()
    commands = []
    
    if backend_only or not mobile_only:
        backend_cmd = "pytest --maxfail=5 --disable-warnings"
        if tags and "ut" in tags:
            backend_cmd = "pytest --maxfail=5 --disable-warnings -m ut"
        if spec:
            backend_cmd = f"pytest --maxfail=5 --disable-warnings -k '{spec}'"
        if exclude:
            exclude_list = exclude.split(",")
            exclude_str = " ".join([f"--ignore=tests/{e}" for e in exclude_list])
            backend_cmd = f"pytest --maxfail=5 --disable-warnings {exclude_str}"
        commands.append((backend_cmd, backend_dir))
    
    if mobile_only or not backend_only:
        mobile_cmd = "npm test"
        if tags and "ut" in tags:
            mobile_cmd = "npm test"
        if spec:
            mobile_cmd = f"npm test -- --testPathPattern='{spec}'"
        commands.append((mobile_cmd, mobile_dir))
    
    return commands


def run_ut(tags=None, spec=None, exclude=None, backend_only=False, mobile_only=False):
    """运行 UT 测试"""
    print("\n" + "="*60)
    print(">>> 运行单元测试 <<<")
    print("="*60)
    
    commands = build_ut_command(tags, spec, exclude, backend_only, mobile_only)
    all_passed = True
    
    for cmd, cwd in commands:
        if not run_command(cmd, cwd=cwd):
            all_passed = False
    
    return all_passed


def run_e2e(tags=None, spec=None, exclude=None, frontend_dir=None):
    """运行 E2E 测试"""
    print("\n" + "="*60)
    print(">>> 运行 E2E 测试 <<<")
    print("="*60)
    
    if frontend_dir is None:
        frontend_dir = get_frontend_dir()
    
    cmd = build_e2e_command(tags, spec, exclude)
    return run_command(cmd, cwd=frontend_dir)


def docker_mode(tags=None, spec=None, exclude=None, run_ut=True):
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
    
    # 6. 运行 UT（如果指定）
    if run_ut:
        print("\n[6/7] 运行单元测试...")
        run_ut(tags=tags, spec=spec, exclude=exclude)
    else:
        print("\n[6/7] 跳过单元测试 (--no-ut)")
    
    # 7. 运行 E2E 测试
    print("\n[7/7] 运行 E2E 测试...")
    os.environ["PLAYWRIGHT_BASE_URL"] = "http://localhost:3001"
    run_e2e(tags=tags, spec=spec, exclude=exclude, frontend_dir=frontend_dir)
    
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


def local_mode(tags=None, spec=None, exclude=None, run_ut=True):
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
    
    # 2. 运行 UT（如果指定）
    if run_ut:
        print("\n运行单元测试...")
        run_ut(tags=tags, spec=spec, exclude=exclude)
    else:
        print("\n跳过单元测试 (--no-ut)")
    
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
            run_e2e(tags=tags, spec=spec, exclude=exclude, frontend_dir=frontend_dir)
        
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


def e2e_mode(tags=None, spec=None, exclude=None):
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
    run_e2e(tags=tags, spec=spec, exclude=exclude, frontend_dir=frontend_dir)
    
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
  python scripts/qa_pipeline.py --mode docker                    # Docker 后端 + 本地前端 + 全量测试
  python scripts/qa_pipeline.py --mode local                     # 全本地 SQLite + 全量测试
  python scripts/qa_pipeline.py --mode e2e                       # 仅启动服务跑 E2E
  python scripts/qa_pipeline.py --mode dev                       # 仅启动开发环境
  python scripts/qa_pipeline.py --mode e2e --tags critical       # 仅跑 E2E 核心链路
  python scripts/qa_pipeline.py --mode e2e --tags smoke          # 仅跑冒烟测试
  python scripts/qa_pipeline.py --mode local --run-ut            # 仅跑 UT
  python scripts/qa_pipeline.py --mode e2e --spec "upload*"      # 仅跑上传相关
  python scripts/qa_pipeline.py --mode e2e --exclude "ux"        # 排除 UX 测试

测试分类标签:
  critical   - 核心链路（上传→OCR→审核→仪表盘）
  smoke      - 冒烟测试
  regression - 回归测试
  ut         - 单元测试（后端 + 移动端）
        """
    )
    parser.add_argument(
        "--mode",
        choices=["docker", "local", "e2e", "dev"],
        default="docker",
        help="运行模式: docker (Docker 后端 + 本地前端 + 测试), local (全本地), e2e (仅 E2E), dev (仅开发环境)"
    )
    parser.add_argument(
        "--tags",
        type=str,
        default=None,
        help="测试标签筛选，逗号分隔: critical,smoke,regression,ut"
    )
    parser.add_argument(
        "--spec",
        type=str,
        default=None,
        help="测试文件/用例名匹配，支持通配符: upload*,member*"
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default=None,
        help="排除的测试文件/用例，逗号分隔: ux,review"
    )
    parser.add_argument(
        "--run-ut",
        action="store_true",
        default=True,
        help="运行单元测试 (默认: True)"
    )
    parser.add_argument(
        "--no-ut",
        action="store_true",
        default=False,
        help="跳过单元测试"
    )
    args = parser.parse_args()
    
    run_ut_flag = args.run_ut and not args.no_ut
    
    print("\n" + "="*60)
    print(f">>> [QA Pipeline Start] 模式: {args.mode} <<<")
    if args.tags:
        print(f">>> 标签筛选: {args.tags} <<<")
    if args.spec:
        print(f">>> 用例匹配: {args.spec} <<<")
    if args.exclude:
        print(f">>> 排除测试: {args.exclude} <<<")
    print(f">>> 运行 UT: {run_ut_flag} <<<")
    print("="*60)
    
    mode_map = {
        "docker": lambda: docker_mode(args.tags, args.spec, args.exclude, run_ut_flag),
        "local": lambda: local_mode(args.tags, args.spec, args.exclude, run_ut_flag),
        "e2e": lambda: e2e_mode(args.tags, args.spec, args.exclude),
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
