import asyncio
import time
import argparse
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

async def soak_worker(target_ip, target_port, interval, timeout, iterations):
    """
    长时稳定性测试工作协程
    模拟高频叠加请求 (Interval < Response Time)
    """
    print(f"\n[Soak Test] Target: {target_ip}:{target_port}")
    print(f"[Soak Test] Interval: {interval}s, Timeout: {timeout}s")
    print(f"[Soak Test] Starting...")

    success = 0
    fail = 0
    timeouts = 0
    pending_tasks = set()

    async def send_request(idx):
        nonlocal success, fail, timeouts
        start_t = time.time()
        client = AsyncModbusTcpClient(target_ip, port=target_port, timeout=timeout)
        try:
            await client.connect()
            if not client.connected:
                print(f"[{idx}] Connection Failed")
                fail += 1
                return

            # 读取寄存器 (模拟全量查询)
            result = await client.read_holding_registers(0, count=100, device_id=1)
            
            if result.isError():
                print(f"[{idx}] Protocol Error: {result}")
                fail += 1
            else:
                elapsed = time.time() - start_t
                # print(f"[{idx}] Success in {elapsed:.2f}s")
                success += 1
        except asyncio.TimeoutError:
            print(f"[{idx}] Request TIMEOUT (>{timeout}s)")
            timeouts += 1
        except Exception as e:
            print(f"[{idx}] Unexpected Error: {e}")
            fail += 1
        finally:
            client.close()

    for i in range(iterations):
        # 创建一个异步任务但不立刻等待它结束 (模拟重叠请求)
        task = asyncio.create_task(send_request(i))
        pending_tasks.add(task)
        task.add_done_callback(pending_tasks.discard)
        
        # 实时监控堆积情况
        if i % 5 == 0:
            print(f"Progress: {i}/{iterations} | Success: {success} | Fail: {fail} | Timeouts: {timeouts} | Pending: {len(pending_tasks)}")
        
        await asyncio.sleep(interval)

    # 等待所有任务完成
    print("\n[Soak Test] Draining remaining tasks...")
    await asyncio.gather(*pending_tasks, return_exceptions=True)
    
    print("\n[Soak Test Final Results]")
    print(f"- Total Iterations: {iterations}")
    print(f"- Success: {success}")
    print(f"- Fail: {fail}")
    print(f"- Timeouts: {timeouts}")
    print(f"- Success Rate: {(success/iterations)*100:.2f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Modbus Soak Test Tool")
    parser.add_argument("--ip", default="127.0.0.1", help="Target IP")
    parser.add_argument("--port", type=int, default=5020, help="Target Port")
    parser.add_argument("--interval", type=float, default=2.0, help="Query interval (s)")
    parser.add_argument("--timeout", type=float, default=3.0, help="Timeout (s)")
    parser.add_argument("--count", type=int, default=100, help="Total iterations")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(soak_worker(args.ip, args.port, args.interval, args.timeout, args.count))
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
