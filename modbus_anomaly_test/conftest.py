import pytest
import subprocess
import time
import os
from pymodbus.client import ModbusTcpClient

# 配置
DEVICE_IP = "127.0.0.1"
DEVICE_PORT = 5020
INTERFACE = "eth0" # 模拟 Linux 环境

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
