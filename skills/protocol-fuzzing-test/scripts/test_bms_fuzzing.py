import pytest
import pytest_asyncio
import asyncio
from pymodbus.client import AsyncModbusTcpClient
import malicious_simulator

@pytest_asyncio.fixture
async def bms_honeypot_sim():
    sim = malicious_simulator.MaliciousSimulator(port=5030, mode="HONEYPOT", config_file="bms_profile.json")
    task = asyncio.create_task(sim.start())
    await asyncio.sleep(0.1)
    yield sim
    await sim.stop()
    task.cancel()

@pytest_asyncio.fixture
async def bms_truncated_sim():
    sim = malicious_simulator.MaliciousSimulator(port=5031, mode="TRUNCATED", config_file="bms_profile.json")
    task = asyncio.create_task(sim.start())
    await asyncio.sleep(0.1)
    yield sim
    await sim.stop()
    task.cancel()

@pytest.mark.asyncio
async def test_bms_soc_overflow(bms_honeypot_sim):
    """
    针对 BMS 的设防测试：验证根据 bms_profile 中的规定，
    向 SOC(地址 274) 和 Temp(地址 272) 写入非法极大值是否正确被捕获。
    """
    client = AsyncModbusTcpClient("127.0.0.1", port=5030, timeout=1, retries=0)
    await client.connect()
    
    # 正常写入 SOC = 100
    await client.write_register(274, 100, device_id=1)
    assert len(bms_honeypot_sim.honeypot_alerts) == 0, "合法的 SOC 写入不应当触发报警"
    
    # 恶意写入 SOC = 65000 (极可能是上游 float 意外变负从而强转引发的无符号溢出)
    await client.write_register(274, 65000, device_id=1)
    assert len(bms_honeypot_sim.honeypot_alerts) == 1, "BMS 配置文件未能生效：漏报了 SOC 溢出"
    assert "274" in bms_honeypot_sim.honeypot_alerts[0]
    
    # 恶意写入最高单体温度 = 200 (极可能是温度断线读取不到引发的最大值)
    await client.write_register(272, 200, device_id=1)
    assert len(bms_honeypot_sim.honeypot_alerts) == 2, "BMS 配置文件未能生效：漏报了电池温度溢出"
    assert "272" in bms_honeypot_sim.honeypot_alerts[1]
    
    client.close()

@pytest.mark.asyncio
async def test_bms_telemetry_truncation(bms_truncated_sim):
    """
    针对 BMS 遥测块读取（大块内容）发生网络截断的验证测试。
    验证配置文件中的 Fake Length (55) 配置项是否已被挂载。
    """
    reader, writer = await asyncio.open_connection("127.0.0.1", 5031)
    
    import struct
    # 尝试读取 BMS 的长串遥测数据（例如 26 个寄存器，本该返回 52 字节）
    mbap = struct.pack('>HHHB', 1, 0, 6, 1)
    pdu = struct.pack('>BHH', 0x03, 100, 26) 
    writer.write(mbap + pdu)
    await writer.drain()
    
    resp_mbap = await reader.readexactly(7)
    trans_id, proto_id, length, unit_id = struct.unpack('>HHHB', resp_mbap)
    
    # 这里的截断假冒长度是从 bms_profile.json 里设定的 55 读取的
    assert length == 55, "由 BMS Profile 设定的虚假截断长度 (55) 没有生效！"
    
    try:
        resp_pdu = await reader.readexactly(length - 1)
        assert False, "截断攻击失败：TCP 连接未被强制切断"
    except asyncio.IncompleteReadError as e:
        assert len(e.partial) < (length - 1)
        
    writer.close()
    await writer.wait_closed()
