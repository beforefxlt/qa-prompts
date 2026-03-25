import pytest
import pytest_asyncio
import asyncio
from pymodbus.client import AsyncModbusTcpClient
import malicious_simulator

@pytest_asyncio.fixture
async def honeypot_simulator():
    sim = malicious_simulator.MaliciousSimulator(port=5020, mode="HONEYPOT", config_file="pcs_profile.json")
    task = asyncio.create_task(sim.start())
    await asyncio.sleep(0.1) # allow time to bind port
    
    yield sim
    
    await sim.stop()
    task.cancel()

@pytest.mark.asyncio
async def test_baseline_normal_operation(honeypot_simulator):
    """
    [GREEN] 基础准线（Baseline）测试。
    为了证明我们的模拟器以及测试工具本身是没有代码错误的，
    必须先验证它在正常的读取/写入行为下，能和标准的 Modbus 设备一样工作！
    """
    client = AsyncModbusTcpClient("127.0.0.1", port=5020, timeout=1, retries=0)
    await client.connect()
    
    # 【准线测试1】：正常写入合法数值
    # 写入 500 到 6006 (有功功率)，这远小于 32767，不应该触发 Honeypot。
    res_write = await client.write_register(6006, 500, device_id=1)
    assert not res_write.isError(), "正常写入请求不应被拒绝或发生底层连接错误！"
    
    # 【准线测试2】：正常读取合法数据块
    res_read = await client.read_holding_registers(6001, count=16, device_id=1)
    assert not res_read.isError(), "正常读取时模拟器应返回完整合法的数据块结构！"
    assert len(res_read.registers) == 16, "读取的寄存器数量必须相符"
    
    client.close()
    
    # 【准线测试3】：确认正常行为没有被误判触发报警
    assert len(honeypot_simulator.honeypot_alerts) == 0, "准线测试下发生了意料外的异常报错截获！"

@pytest.mark.asyncio
async def test_honeypot_negative_overflow(honeypot_simulator):
    """
    [RED] 测试负数溢出欺骗检测
    当我们写入一个大于 32767 的巨大正数（例如 65535）到控制地址（如 6006）时，
    恶性模拟器应能拦截并记录一个 honeypot报警。
    """
    client = AsyncModbusTcpClient("127.0.0.1", port=5020)
    await client.connect()
    
    # 向地址 6006 (有功功率) 写入 65535 (对应 EMS 处理负数引发的转换溢出截断)
    await client.write_register(6006, 65535, device_id=1)
    
    client.close()
    
    # 断言模拟器成功捕获此钓鱼/溢出行为
    assert len(honeypot_simulator.honeypot_alerts) == 1, "模拟器未能记录任何钓鱼/溢出报警"
    assert "6006" in honeypot_simulator.honeypot_alerts[0], "报警信息中未包含被写入的寄存器地址"

@pytest_asyncio.fixture
async def drop_simulator():
    sim = malicious_simulator.MaliciousSimulator(port=5021, mode="DROP", drop_after_n=2)
    task = asyncio.create_task(sim.start())
    await asyncio.sleep(0.1)
    
    yield sim
    
    await sim.stop()
    task.cancel()

@pytest.mark.asyncio
async def test_drop_storm_connection(drop_simulator):
    """
    [RED/GREEN] 测试在 DROP 模式下，设备是否会在正常处理前 N 个包后强制切断 Socket。
    使用真正的底层 Socket 以避免 pymodbus 客户端自动重连掩盖断线现象。
    """
    reader, writer = await asyncio.open_connection("127.0.0.1", 5021)
    
    import struct
    def build_req(trans_id, addr):
        mbap = struct.pack('>HHHB', trans_id, 0, 6, 1)
        pdu = struct.pack('>BHH', 0x06, addr, 1) # write single register
        return mbap + pdu

    # 第 1 包
    writer.write(build_req(1, 6001))
    await writer.drain()
    resp1 = await reader.read(1024)
    assert len(resp1) > 0
    
    # 第 2 包
    writer.write(build_req(2, 6002))
    await writer.drain()
    resp2 = await reader.read(1024)
    assert len(resp2) > 0
    
    # 第 3 包 (此时应触发 drop)
    writer.write(build_req(3, 6003))
    await writer.drain()
    resp3 = await reader.read(1024)
    
    # 模拟器此时强制拉闸，TCP Socket 会读到 0 字节 (EOF)
    assert len(resp3) == 0, "断言失败：预期第三个包时模拟器强制断开（返回0字节），但却收到了数据！"
    
    writer.close()
    await writer.wait_closed()

@pytest_asyncio.fixture
async def truncated_simulator():
    sim = malicious_simulator.MaliciousSimulator(port=5022, mode="TRUNCATED", config_file="pcs_profile.json")
    task = asyncio.create_task(sim.start())
    await asyncio.sleep(0.1)
    
    yield sim
    
    await sim.stop()
    task.cancel()

@pytest.mark.asyncio
async def test_truncated_response(truncated_simulator):
    """
    [RED/GREEN] 测试 TRUNCATED 模式。
    客户端请求 16 个寄存器 (32字节数据)。模拟器返回的 MBAP 声称含有 35 字节，
    但载荷中途被无情切断，只发了 5 个字节。
    """
    reader, writer = await asyncio.open_connection("127.0.0.1", 5022)
    
    import struct
    # 构造标准请求: 事务 ID=1, 长度=6, 单元 ID=1, Read Holding Registers (0x03), Addr=6001, Count=16
    mbap = struct.pack('>HHHB', 1, 0, 6, 1)
    pdu = struct.pack('>BHH', 0x03, 6001, 16)
    writer.write(mbap + pdu)
    await writer.drain()
    
    # 读回 MBAP Header
    resp_mbap = await reader.readexactly(7)
    trans_id, proto_id, length, unit_id = struct.unpack('>HHHB', resp_mbap)
    
    # 在 TDD RED 阶段，标准的（或者回 0x01 的）模拟器会给出完整的长度。
    # 恶性模拟器 (TRUNCATED) 会给出巨大的 length 声明，但随后直接中断。
    try:
        # 尝试读取声明的长度 (使用 readexactly 会抛出 IncompleteReadError)
        resp_pdu = await reader.readexactly(length - 1)
        # 如果能读满，说明没有截断！
        assert False, f"缺陷：模拟器声称的长度为 {length-1}，且实际也下发了完整的数据，没有执行截断！"
    except asyncio.IncompleteReadError as e:
        # 捕获到了不完整的数据流，说明模拟器成功发送了残缺报文
        assert len(e.partial) < (length - 1), "部分数据长度应必小于声明长度"
    
    writer.close()
    await writer.wait_closed()

@pytest_asyncio.fixture
async def mismatch_simulator():
    sim = malicious_simulator.MaliciousSimulator(port=5023, mode="MISMATCH")
    task = asyncio.create_task(sim.start())
    await asyncio.sleep(0.1)
    
    yield sim
    
    await sim.stop()
    task.cancel()

@pytest.mark.asyncio
async def test_transaction_mismatch(mismatch_simulator):
    """
    [RED] 测试 MISMATCH 模式。
    验证模拟器在响应时是否抛弃了请求的事务 ID (Transaction ID)，随机/固定地使用别的 ID。
    导致严格对应的客户端状态机出现乱序或报错。
    """
    reader, writer = await asyncio.open_connection("127.0.0.1", 5023)
    
    import struct
    # 构造标准请求: 事务 ID=99, Write Single Register
    req_tid = 99
    mbap = struct.pack('>HHHB', req_tid, 0, 6, 1)
    pdu = struct.pack('>BHH', 0x06, 6001, 1)
    writer.write(mbap + pdu)
    await writer.drain()
    
    # 读回 MBAP Header
    resp_mbap = await reader.readexactly(7)
    trans_id, proto_id, length, unit_id = struct.unpack('>HHHB', resp_mbap)
    
    # 作为 TDD 的测试：我们要求恶性模拟器必须篡改了事务 ID！
    assert trans_id != req_tid, f"缺陷：恶性模拟器并未打乱事务 ID，仍然老实地回复了 {trans_id}"
    
    writer.close()
    await writer.wait_closed()

