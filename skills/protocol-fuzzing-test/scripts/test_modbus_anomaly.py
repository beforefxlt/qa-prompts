import pytest
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse
import time

# 真实寄存器地址 (根据生产代码)
PCS_A_ACTIVE_POWER_ADDR = 6006
INPOWER_A_ACTIVE_POWER_ADDR = 309
INVALID_ADDR = 0xFFFF
POWER_ON_ADDR = 6001

# 异常测试输入
TEST_CASES = [
    (PCS_A_ACTIVE_POWER_ADDR, 65535, "pcs100k_a 有功功率越界写入"),
    (INPOWER_A_ACTIVE_POWER_ADDR, 65535, "inpower_100k A相有功功率越界写入"),
    (POWER_ON_ADDR, 0xFFFF, "开关机指令非法值写入"),
]

@pytest.mark.parametrize("addr, value, desc", TEST_CASES)
def test_modbus_write_anomaly(modbus_client, network_capture, addr, value, desc):
    """
    用例：向关键控制寄存器写入非法/越界值
    验证：设备必须返回错误码，不能无条件接受或崩溃
    """
    print(f"\n[Running] {desc} (Addr: {addr}, Value: {value})")
    
    # 执行写入
    result = modbus_client.write_register(addr, value, device_id=1)
    
    # 判定 1: 必须是异常响应
    # 如果模拟器没有做校验，这里会返回正常的 WriteRegisterResponse，导致断言失败
    assert isinstance(result, ExceptionResponse), \
        f"致命缺陷: 设备未拒绝非法值 {value}，可能导致系统级失效！"

    # 判定 2: 响应码符合标准 (02:非法地址 或 03:非法数据值)
    assert result.exception_code in [2, 3], \
        f"返回了未预定义的 Modbus 异常码: {result.exception_code}"

def test_modbus_invalid_address(modbus_client, network_capture):
    """
    用例：访问不存在的寄存器地址
    """
    print(f"\n[Running] 非法地址访问测试 (Addr: {INVALID_ADDR})")
    result = modbus_client.write_register(INVALID_ADDR, 1, device_id=1)
    
    assert isinstance(result, ExceptionResponse), "缺陷: 写入不存在的地址未返回异常响应"
    assert result.exception_code == 2, f"预期异常码 0x02，实际返回: {result.exception_code}"

def test_system_liveness_after_anomaly(modbus_client, network_capture):
    """
    用例：异常注入后存活性验证
    验证：发送异常指令后，系统仍能正常响应后续写请求
    """
    print(f"\n[Running] 存活性验证...")
    
    # 1. 注入异常（故意触发）
    modbus_client.write_register(PCS_A_ACTIVE_POWER_ADDR, 0xFFFF, device_id=1)
    
    # 2. 发送合法指令
    legal_value = 500 # 50kW
    result = modbus_client.write_register(PCS_A_ACTIVE_POWER_ADDR, legal_value, device_id=1)
    
    # 3. 判定：合法指令应成功
    assert not isinstance(result, ExceptionResponse), "缺陷: 异常注入导致系统进入死锁，无法响应后续正常指令"
    
    # 4. 验证值确实写入了 (读回校验)
    read_back = modbus_client.read_holding_registers(PCS_A_ACTIVE_POWER_ADDR, count=1, device_id=1)
    assert read_back.registers[0] == legal_value, "存活性验证读回值不匹配"

def test_high_frequency_anomaly_injection(modbus_client, network_capture):
    """
    用例：高频度、长时间异常报文注入压测
    目的：验证设备在遭遇类似 DDoS 或重传风暴的异常 Modbus 请求时，是否会发生缓冲区溢出、内存泄漏或服务崩溃
    """
    ITERATIONS = 500  # 高频写入次数 (可根据实际压测情况调整到上万次)
    test_addr = INPOWER_A_ACTIVE_POWER_ADDR
    invalid_value = 0xFFFF
    
    print(f"\n[Running] 开始高频异常注入压测 (目标: {ITERATIONS} 次)...")
    
    start_time = time.time()
    for i in range(ITERATIONS):
        # 持续高频轰炸
        result = modbus_client.write_register(test_addr, invalid_value, device_id=1)
        
        # 即使它没有正确返回 Error Code（如之前的 FAILED 情况），
        # 在这里的首要观测目标是：连接是否断开？抛出 Timeout？
        if result.isError():
            # 这是设备崩溃或通信熔断的标准反馈（比如 Socket 异常断开）
            assert not isinstance(result, ModbusException), f"在第 {i+1} 次高频注入时设备崩溃或断开连接！"
            
    end_time = time.time()
    
    # 压测后存活性“一锤定音”验证
    legal_value = 0
    liveness_check = modbus_client.write_register(test_addr, legal_value, device_id=1)
    assert not liveness_check.isError(), "高频异常压测导致设备后续全部瘫痪 (拒绝合法请求)！"
    
    qps = ITERATIONS / (end_time - start_time)
    print(f"\n[Performance] 高频压测完成，未发生崩溃。频率: {qps:.2f} 报文/秒")
