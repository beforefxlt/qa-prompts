#!/usr/bin/env python3
import asyncio
import logging
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusDeviceContext, ModbusServerContext
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.pdu.device import ModbusDeviceIdentification

# 配置日志
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# 真实点表配置
REGISTERS = {
    # pcs100k_a
    6001: 0,    # 开机
    6003: 0,    # 无功
    6006: 0,    # 有功
    6013: 1,    # 运行模式
    6016: 0,    # 紧急功率
    
    # inpower_100k
    301: 1,     # 运行模式
    309: 0,     # A相有功
    310: 0,     # B相有功
    311: 0,     # C相有功
    312: 0,     # A相无功
}

class ValidatingDataBlock(ModbusSparseDataBlock):
    """
    带有自定义校验逻辑的数据块
    """
    def setValues(self, address, values):
        # 模拟校验逻辑：如果值超过某个范围，可以抛出异常或拒绝更新
        # 在 Modbus 中，如果想返回异常响应，我们需要在 Server 层处理
        # 这里的模拟器为了演示测试脚本，默认接受所有值，但在日志中记录警告
        for i, val in enumerate(values):
            addr = address + i
            if addr in [6006, 309, 310, 311] and val > 10000: # 假设 > 1000kW 是异常
                log.warning(f"检测到非法数据注入！地址: {addr}, 值: {val}")
        
        return super().setValues(address, values)

async def run_server():
    # 初始化数据块 (使用实际代码中的地址)
    block = ValidatingDataBlock(REGISTERS)
    store = ModbusDeviceContext(hr=block, ir=block, co=block, di=block)
    context = ModbusServerContext(devices=store, single=True)

    # 设备识别信息
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'KelinEnergy'
    identity.ProductCode = 'PCS-MVP-SIM'
    identity.ProductName = 'PCS Simulator for Anomaly Testing'
    identity.ModelName = 'PCS-100K'

    log.info("启动 PCS Modbus TCP 模拟器 (Port: 502)...")
    await StartAsyncTcpServer(context=context, identity=identity, address=("0.0.0.0", 502))

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        log.info("模拟器已停止")
