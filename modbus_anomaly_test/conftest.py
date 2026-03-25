import pytest
import subprocess
import time
import os
import socket
import sys
from pathlib import Path
from pymodbus.client import ModbusTcpClient

# 配置
BASE_DIR = Path(__file__).resolve().parent
DEVICE_IP = os.environ.get("MODBUS_SIM_HOST", "127.0.0.1")
DEVICE_PORT = int(os.environ.get("MODBUS_SIM_PORT", "5020"))
DEFAULT_DEVICE_MODE = os.environ.get("MODBUS_SIM_MODE", "NORMAL")
DEVICE_CONFIG = os.environ.get("MODBUS_SIM_CONFIG", str(BASE_DIR / "pcs_profile.json"))
AUTOSTART = os.environ.get("MODBUS_SIM_AUTOSTART", "1") != "0"
REUSE_EXISTING = os.environ.get("MODBUS_SIM_REUSE_EXISTING", "1") != "0"
STARTUP_TIMEOUT = float(os.environ.get("MODBUS_SIM_STARTUP_TIMEOUT", "15"))
INTERFACE = "eth0" # 模拟 Linux 环境


def _simulator_log_path() -> Path:
    return Path(
        os.environ.get("MODBUS_SIM_LOG", str(Path("/tmp") / f"modbus_simulator_{DEVICE_PORT}.log"))
    )


def _is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _needs_shared_simulator(request) -> bool:
    path_name = getattr(getattr(request.node, "path", None), "name", "")
    return (
        path_name.startswith("test_modbus_")
        or "modbus_client" in request.fixturenames
        or "network_capture" in request.fixturenames
    )


def _stop_process(process: subprocess.Popen | None) -> None:
    if not process or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def _start_modbus_simulator(mode: str) -> tuple[subprocess.Popen | None, Path]:
    log_path = _simulator_log_path()
    if REUSE_EXISTING and _is_port_open(DEVICE_IP, DEVICE_PORT):
        return None, log_path

    if not AUTOSTART:
        if _is_port_open(DEVICE_IP, DEVICE_PORT):
            return None, log_path
        pytest.fail(
            f"Modbus simulator is not running on {DEVICE_IP}:{DEVICE_PORT}. "
            "Set MODBUS_SIM_AUTOSTART=1 to let pytest start it automatically."
        )

    simulator_script = BASE_DIR / "malicious_simulator.py"
    if not simulator_script.exists():
        pytest.fail(f"Simulator script not found: {simulator_script}")

    log_file = open(log_path, "w")
    cmd = [
        sys.executable,
        str(simulator_script),
        "--host",
        DEVICE_IP,
        "--port",
        str(DEVICE_PORT),
        "--mode",
        mode,
        "--config",
        DEVICE_CONFIG,
    ]
    process = subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    deadline = time.time() + STARTUP_TIMEOUT
    try:
        while time.time() < deadline:
            if process.poll() is not None:
                break
            if _is_port_open(DEVICE_IP, DEVICE_PORT):
                return process, log_path
            time.sleep(0.2)

        _stop_process(process)
        pytest.fail(
            f"Failed to start Modbus simulator on {DEVICE_IP}:{DEVICE_PORT}. "
            f"Check log: {log_path}"
        )
    finally:
        log_file.close()


@pytest.fixture(scope="function", autouse=True)
def modbus_simulator(request):
    """
    统一管理 Modbus 仿真器生命周期。

    优先复用已存在的本地服务；否则由 pytest 自动拉起并在用例结束后回收。
    仅对共享 Modbus 测试文件生效，避免干扰自带仿真器的独立测试。
    """
    if not _needs_shared_simulator(request):
        yield
        return

    marker = request.node.get_closest_marker("simulator_mode")
    mode = marker.args[0] if marker and marker.args else DEFAULT_DEVICE_MODE
    process, _ = _start_modbus_simulator(mode)
    yield
    _stop_process(process)

@pytest.fixture(scope="function")
def network_capture(request):
    """
    自动启停 tshark 抓包
    """
    # 检查是否在 Linux 环境且有 tshark
    if os.name == 'posix' and subprocess.run(["which", "tshark"], capture_output=True).returncode == 0:
        pcap_file = f"capture_{request.node.name}_{int(time.time())}.pcap"
        tshark_cmd = [
            "tshark", "-i", "any", # 使用 any 捕获所有接口（包含 lo）
            "-f", f"tcp port {DEVICE_PORT}",
            "-w", pcap_file
        ]
        # 使用 sudo 如果需要的话，或者确保当前用户有权限
        log_file = open("/tmp/tshark_log.txt", "w")
        process = subprocess.Popen(tshark_cmd, stdout=log_file, stderr=log_file)
        
        time.sleep(2) # 等待抓包启动
        
        yield pcap_file
        
        process.terminate()
        process.wait()
        log_file.close()
        
        # 结果判定：如果测试通过且没有特殊要求，可以手动决定是否保留
        # 这里默认保留，打印路径
        print(f"\n[Evidence] PCAP saved to: {os.path.abspath(pcap_file)}")
    else:
        print("\n[Warning] tshark not found or not in Linux, skipping capture.")
        yield None

@pytest.fixture(scope="function")
def modbus_client():
    """
    提供 Modbus 客户端实例
    """
    client = ModbusTcpClient(DEVICE_IP, port=DEVICE_PORT)
    if not client.connect():
        pytest.fail(f"Failed to connect to Modbus server at {DEVICE_IP}:{DEVICE_PORT}")
    
    yield client
    
    client.close()
