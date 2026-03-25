import asyncio
import pytest
from pymodbus.client import AsyncModbusTcpClient
import time

# 配置
DEVICE_IP = "127.0.0.1"
DEVICE_PORT = 5020
CONCURRENT_TASKS = 50  # 并发连接/请求数
ITERATIONS = 10        # 每个任务发送的请求数

async def run_single_worker(worker_id):
    """
    单个并发工作协程
    """
    async with AsyncModbusTcpClient(DEVICE_IP, port=DEVICE_PORT) as client:
        if not client.connected:
            print(f"Worker {worker_id} failed to connect")
            return False
            
        success_count = 0
        for i in range(ITERATIONS):
            # 发送读请求 (6006 地址)
            # pymodbus 会自动处理 Transaction ID
            try:
                result = await client.read_holding_registers(6006, count=1, device_id=1)
                
                if result.isError():
                    print(f"Worker {worker_id} request {i} failed: {result}")
                else:
                    # 在异步模式下，pymodbus 内部会校验 Transaction ID 是否匹配
                    # 如果不匹配，在底层就会报错或返回错误对象
                    success_count += 1
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                
        return success_count == ITERATIONS

@pytest.mark.asyncio
async def test_modbus_concurrency_stress():
    """
    并发压力测试：验证 50 个并发客户端同时请求时，仿真器的稳定性和响应正确性
    """
    print(f"\n[Stress Test] Starting {CONCURRENT_TASKS} concurrent workers...")
    start_time = time.time()
    
    tasks = [run_single_worker(i) for i in range(CONCURRENT_TASKS)]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    
    total_requests = CONCURRENT_TASKS * ITERATIONS
    success_rate = sum(results) / len(results) * 100
    duration = end_time - start_time
    qps = total_requests / duration
    
    print(f"\n[Stress Test Results]")
    print(f"- Total Requests: {total_requests}")
    print(f"- Success Rate: {success_rate:.2f}%")
    print(f"- Duration: {duration:.2f}s")
    print(f"- Throughput: {qps:.2f} QPS")
    
    assert success_rate == 100, f"并发压测失败，成功率仅为 {success_rate:.2f}%"
