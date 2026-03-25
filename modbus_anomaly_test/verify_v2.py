import asyncio
import time
from pymodbus.client import AsyncModbusTcpClient

async def verify_v2():
    print("\n[V2 Verification] Starting client to test MIXED mode (Oversized + Segmentation)...")
    
    # 模拟主站
    client = AsyncModbusTcpClient("127.0.0.1", port=5020, timeout=10)
    await client.connect()
    
    if not client.connected:
        print("Failed to connect to Fuzzer V2")
        return

    start_t = time.time()
    try:
        # 发送读取请求
        print("Sending Read Request (0x03)...")
        result = await client.read_holding_registers(0, count=1, device_id=1)
        
        duration = time.time() - start_t
        print(f"Request completed in {duration:.2f}s")
        
        # 验证结果
        # 注意：由于 Oversized 插件填充了垃圾数据，pymodbus 可能会解析失败
        # 我们主要观察的是网络层的表现和 duration（分段发送应有延迟）
        if hasattr(result, 'registers'):
            print(f"Response PDU Length: {len(result.registers) * 2}")
        else:
            print(f"Response Received (Potential parsing error expected due to Oversized payload): {result}")

    except Exception as e:
        print(f"Client captured exception: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(verify_v2())
