import asyncio
import pytest
from pymodbus.client import AsyncModbusTcpClient
import time

pytestmark = pytest.mark.simulator_mode("NORMAL")

# 配置
DEVICE_IP = "127.0.0.1"
DEVICE_PORT = 5020
CONCURRENT_TASKS = 50  # 并发连接/请求数
ITERATIONS = 10        # 每个任务发送的请求数
BASE_TEST_ADDR = 30000  # 每个 worker 使用独立地址，避免同址请求掩盖串话
ADDR_STRIDE = 32        # 保证地址区间互不重叠


def _worker_signature(worker_id, iteration):
    """
    为每个 worker 生成稳定且可区分的写入签名。
    这样即使并发下响应被串线，也会在读回校验时暴露出来。
    """
    return ((worker_id + 1) << 8) | (iteration + 1)


async def run_single_worker(worker_id, start_event):
    """
    单个并发工作协程
    """
    test_addr = BASE_TEST_ADDR + (worker_id * ADDR_STRIDE)
    async with AsyncModbusTcpClient(DEVICE_IP, port=DEVICE_PORT) as client:
        if not client.connected:
            print(f"Worker {worker_id} failed to connect")
            return False

        await start_event.wait()

        success_count = 0
        for i in range(ITERATIONS):
            signature = _worker_signature(worker_id, i)

            try:
                write_result = await client.write_register(test_addr, signature, device_id=1)
                assert not write_result.isError(), (
                    f"Worker {worker_id} write request {i} failed: {write_result}"
                )

                read_result = await client.read_holding_registers(
                    test_addr, count=1, device_id=1
                )
                assert not read_result.isError(), (
                    f"Worker {worker_id} readback request {i} failed: {read_result}"
                )
                assert read_result.registers[0] == signature, (
                    f"Worker {worker_id} detected cross-talk on addr {test_addr}: "
                    f"expected {signature}, got {read_result.registers[0]}"
                )
                success_count += 1
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")

        return success_count == ITERATIONS


@pytest.mark.asyncio
async def test_modbus_concurrency_stress():
    """
    并发压力测试：验证 50 个并发客户端同时请求时，仿真器的响应隔离与串话防护能力
    """
    print(f"\n[Stress Test] Starting {CONCURRENT_TASKS} concurrent workers...")
    start_time = time.time()

    start_event = asyncio.Event()
    tasks = [asyncio.create_task(run_single_worker(i, start_event)) for i in range(CONCURRENT_TASKS)]

    # 让所有 worker 先完成连接准备，再同时放行，尽量把并发冲突压到同一时间窗。
    await asyncio.sleep(0.2)
    start_event.set()

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
