import pytest
from pymodbus.client import ModbusTcpClient

# 寄存器地址
PCS_A_ACTIVE_POWER_ADDR = 6006
INPOWER_A_ACTIVE_POWER_ADDR = 309
POWER_ON_ADDR = 6001

def test_baseline_connection(modbus_client):
    """验证客户端是否能成功连接"""
    assert modbus_client.connect(), "无法连接到 Modbus 仿真器"

def test_baseline_read_registers(modbus_client):
    """
    基线测试：验证常规寄存器的读操作
    """
    # 读取有功功率
    result = modbus_client.read_holding_registers(PCS_A_ACTIVE_POWER_ADDR, count=1, device_id=1)
    assert not result.isError(), f"读取 6006 寄存器失败: {result}"
    
    # 读取 B 相有功
    result = modbus_client.read_holding_registers(INPOWER_A_ACTIVE_POWER_ADDR, count=1, device_id=1)
    assert not result.isError(), f"读取 309 寄存器失败: {result}"

def test_baseline_write_registers(modbus_client):
    """
    基线测试：验证常规寄存器的写操作（正向路径）
    """
    # 写入一个合法值 (例如 100kW)
    test_val = 1000
    result = modbus_client.write_register(PCS_A_ACTIVE_POWER_ADDR, test_val, device_id=1)
    assert not result.isError(), f"写入 6006 寄存器失败: {result}"
    
    # 验证开关机指令 (1: 开机)
    result = modbus_client.write_register(POWER_ON_ADDR, 1, device_id=1)
    assert not result.isError(), f"写入 6001 开机指令失败: {result}"

def test_baseline_coils(modbus_client):
    """
    基线测试：验证线圈 (Coils) 的读写
    """
    COIL_ADDR = 100
    # 写入线圈
    result = modbus_client.write_coil(COIL_ADDR, True, device_id=1)
    assert not result.isError(), "写线圈失败"
    
    # 读回线圈
    result = modbus_client.read_coils(COIL_ADDR, count=1, device_id=1)
    assert not result.isError(), "读线圈失败"
    assert result.bits[0] is True, "线圈读回值不匹配"

def test_baseline_write_multiple_registers(modbus_client):
    """
    基线测试：验证多寄存器写入 (0x10)
    """
    START_ADDR = 2000
    VALUES = [10, 20, 30, 40, 50]
    
    # 批量写入
    result = modbus_client.write_registers(START_ADDR, VALUES, device_id=1)
    assert not result.isError(), "多寄存器写入失败"
    
    # 读回验证
    result = modbus_client.read_holding_registers(START_ADDR, count=len(VALUES), device_id=1)
    assert not result.isError(), "读回验证失败"
    assert result.registers == VALUES, "多寄存器读回值不匹配"
