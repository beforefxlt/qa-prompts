import asyncio
import pytest
from pymodbus.client import AsyncModbusTcpClient
import subprocess
import time
import os

# 靶机配置
TARGET_PORT = 5021

async def run_target(bug_mode):
    """
    启动带特定 Bug 的靶机
    """
    cmd = ["python", "vulnerable_target.py", "--port", str(TARGET_PORT), "--bug", bug_mode]
    process = await asyncio.create_subprocess_exec(*cmd)
    await asyncio.sleep(2) # 等待启动
    return process

@pytest.mark.asyncio
async def test_detect_bug_oob():
    """
    验证：靶机的 BUG_OOB (缓冲区越界) 是否能被识别
    """
    proc = await run_target("BUG_OOB")
    try:
        client = AsyncModbusTcpClient("127.0.0.1", port=TARGET_PORT, timeout=2)
        await client.connect()
        assert client.connected
        
        # 触发漏洞：请求 15 个寄存器 (Limit 是 10)
        print("\n[Test] Triggering BUG_OOB with 15 regs read...")
        result = await client.read_holding_registers(0, count=15, device_id=1)
        
        # 靶机应对此请求返回垃圾数据或直接断开
        if result.isError():
            print(f"[Success] Bug Detected: Target returned error/garbage or disconnected.")
        else:
            # 如果成功读回正常数据，说明漏洞漏测了
            pytest.fail("Failed to detect BUG_OOB: Target responded normally to out-of-range read.")
            
    finally:
        proc.terminate()
        await proc.wait()

@pytest.mark.asyncio
async def test_detect_bug_leak():
    """
    验证：靶机的 BUG_LEAK (连接泄露堆积) 是否能被识别
    """
    proc = await run_target("BUG_LEAK")
    try:
        clients = []
        # BUG_LEAK 限制为 5 个连接。我们并发发起 8 个。
        print(f"\n[Test] Triggering BUG_LEAK with 8 concurrent connections (Limit: 5)...")
        
        for i in range(8):
            client = AsyncModbusTcpClient("127.0.0.1", port=TARGET_PORT, timeout=3)
            await client.connect()
            clients.append(client)
            
        success_count = 0
        for i, client in enumerate(clients):
            if client.connected:
                # 尝试进行一次读取操作
                res = await client.read_holding_registers(0, 1, device_id=1)
                if not res.isError():
                    success_count += 1
                else:
                    print(f"Client {i} failed to read (expected bug behavior)")
            else:
                print(f"Client {i} failed to connect (expected bug behavior)")
        
        print(f"Successfully communicated clients: {success_count}/8")
        # 预期：第 6-8 个连接应无法正常通信
        assert success_count <= 5, f"Failed to detect BUG_LEAK: {success_count} clients succeeded, but limit is 5."
        print("[Success] Bug Detected: Connection pile-up caused failure as expected.")

    finally:
        for c in clients: c.close()
        proc.terminate()
        await proc.wait()
