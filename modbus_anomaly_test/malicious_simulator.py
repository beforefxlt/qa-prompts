import asyncio
import logging
import struct
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MaliciousSimulator")

class MaliciousSimulator:
    def __init__(self, host="127.0.0.1", port=5020, mode="HONEYPOT", drop_after_n=0, config_file=None, delay=0.0, max_conns=0):
        self.host = host
        self.port = port
        self.mode = mode
        self.drop_after_n = drop_after_n
        self.delay = delay
        self.max_conns = max_conns
        self.active_conns = 0
        self.config = {}
        if config_file:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        self.server = None
        self.honeypot_alerts = [] # Records honeypot triggers
        self.registers = {}       # DataStore for Holding/Input Registers (16-bit)
        self.coils = {}           # DataStore for Coils/Discrete Inputs (1-bit)
        
        # 配解化加载插件/配置
        if self.config:
            # 初始化寄存器 (JSON key 是字符串，转为 int)
            for addr, val in self.config.get("registers_init", {}).items():
                self.registers[int(addr)] = val
            # 初始化线圈
            for addr, val in self.config.get("coils_init", {}).items():
                self.coils[int(addr)] = val

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        if self.max_conns > 0 and self.active_conns >= self.max_conns:
            logger.warning(f"MAX_CONNS reached ({self.max_conns}). Refusing connection from {addr}")
            writer.close()
            return
        
        self.active_conns += 1
        logger.info(f"Client connected: {addr} (Active: {self.active_conns})")
        req_count = 0
        try:
            while True:
                # 1. 解析 MBAP 头部 (7字节)
                try:
                    mbap = await asyncio.wait_for(reader.readexactly(7), timeout=5.0)
                except (asyncio.IncompleteReadError, asyncio.TimeoutError):
                    logger.warning(f"MBAP read failed or timeout from {addr}")
                    break
                
                # 延迟注入：模拟从机响应慢导致的阻塞
                if self.delay > 0:
                    await asyncio.sleep(self.delay)
                
                trans_id, proto_id, length, unit_id = struct.unpack('>HHHB', mbap)
                
                # 乱序模式的核心机制：暴力篡改要返回的事务 ID
                if self.mode == "MISMATCH":
                    logger.warning(f"MISMATCH TRIGGERED! Changing Transaction ID from {trans_id} to {trans_id + 999}")
                    trans_id = (trans_id + 999) % 65536
                
                # Drop 模式的核心机制：达到放行包数后猛然断开 (不回应)
                if self.mode == "DROP" and self.drop_after_n >= 0:
                    if req_count >= self.drop_after_n:
                        logger.warning(f"DROP TRIGGERED! Forcibly disconnecting {addr} after {req_count} requests.")
                        break # 跳出循环，让 error/finally block 关闭连接
                
                req_count += 1

                # 2. 读取 PDU (Length - 1(Unit ID))
                try:
                    pdu = await asyncio.wait_for(reader.readexactly(length - 1), timeout=5.0)
                except (asyncio.IncompleteReadError, asyncio.TimeoutError):
                    logger.warning(f"PDU read failed or timeout from {addr} (expected {length-1} bytes)")
                    break
                func_code = pdu[0]
                
                # Write Single Register (0x06)
                if func_code == 0x06:
                    reg_addr, reg_val = struct.unpack('>HH', pdu[1:5])
                    
                    if reg_addr == 0xFFFF:
                        # 模拟器默认防御机制：非法寄存器地址，直接返回异常码 0x02 (Illegal Data Address)
                        alert_msg = f"INVALID ADDRESS TRIGGERED! Address {reg_addr} does not exist"
                        logger.error(alert_msg)
                        response_pdu = bytes([func_code | 0x80, 0x02])
                        response_mbap = struct.pack('>HHHB', trans_id, proto_id, len(response_pdu) + 1, unit_id)
                        writer.write(response_mbap + response_pdu)
                        await writer.drain()
                        continue
                    
                    is_honeypot_triggered = False
                    if self.mode == "HONEYPOT":
                        # 配置驱动的溢出检测
                        honeypots = self.config.get("honeypots", {})
                        str_reg_addr = str(reg_addr)
                        hk_profile = honeypots.get(str_reg_addr)
                        
                        if hk_profile:
                            if reg_val > hk_profile.get("threshold_max", 32767):
                                alert_msg = f"HONEYPOT TRIGGERED! Address {reg_addr} got overflow value {reg_val}"
                                logger.error(alert_msg)
                                self.honeypot_alerts.append(alert_msg)
                                is_honeypot_triggered = True
                    
                    if is_honeypot_triggered:
                        # 触发了越界保护，返回异常码 0x03 (Illegal Data Value)
                        response_pdu = bytes([func_code | 0x80, 0x03])
                    else:
                        # 正常写入：更新 DataStore 状态
                        self.registers[reg_addr] = reg_val
                        # 伪造正常响应 (0x06 原样返回 PDU)
                        response_pdu = pdu

                    response_mbap = struct.pack('>HHHB', trans_id, proto_id, len(response_pdu) + 1, unit_id)
                    writer.write(response_mbap + response_pdu)
                    await writer.drain()
                
                # Write Multiple Registers (0x10)
                elif func_code == 0x10:
                    start_addr, reg_count, byte_count = struct.unpack('>HHB', pdu[1:6])
                    values_bytes = pdu[6:]
                    
                    # 简单批量写入 DataStore
                    for i in range(reg_count):
                        val = struct.unpack('>H', values_bytes[i*2 : i*2+2])[0]
                        self.registers[start_addr + i] = val
                    
                    # 0x10 响应：FunctionCode, StartAddr, Count
                    response_pdu = pdu[0:5]
                    response_mbap = struct.pack('>HHHB', trans_id, proto_id, len(response_pdu) + 1, unit_id)
                    writer.write(response_mbap + response_pdu)
                    await writer.drain()

                # Write Single Coil (0x05)
                elif func_code == 0x05:
                    coil_addr, coil_val = struct.unpack('>HH', pdu[1:5])
                    # 0xFF00 为 ON, 0x0000 为 OFF
                    self.coils[coil_addr] = (coil_val == 0xFF00)
                    
                    response_pdu = pdu
                    response_mbap = struct.pack('>HHHB', trans_id, proto_id, len(response_pdu) + 1, unit_id)
                    writer.write(response_mbap + response_pdu)
                    await writer.drain()

                # Read Coils (0x01) / Read Discrete Inputs (0x02)
                elif func_code in (0x01, 0x02):
                    start_addr, count = struct.unpack('>HH', pdu[1:5])
                    byte_count = (count + 7) // 8
                    
                    # 位打包逻辑
                    bits = []
                    for i in range(count):
                        bits.append(self.coils.get(start_addr + i, False))
                    
                    payload = bytearray(byte_count)
                    for i, bit in enumerate(bits):
                        if bit:
                            payload[i // 8] |= (1 << (i % 8))
                    
                    response_pdu = struct.pack('>BB', func_code, byte_count) + payload
                    response_mbap = struct.pack('>HHHB', trans_id, proto_id, len(response_pdu) + 1, unit_id)
                    writer.write(response_mbap + response_pdu)
                    await writer.drain()

                # Read Holding Registers (0x03) / Read Input Registers (0x04)
                elif func_code in (0x03, 0x04):
                    if self.mode == "TRUNCATED":
                        trunc_prof = self.config.get("truncation", {})
                        fake_length = trunc_prof.get("fake_length", 35) 
                        payload_hex = trunc_prof.get("dirty_payload_hex", "0320AABBCC")
                        
                        logger.warning("TRUNCATED TRIGGERED! Emitting truncated payload.")
                        response_mbap = struct.pack('>HHHB', trans_id, proto_id, fake_length, unit_id)
                        dirty_pdu = bytes.fromhex(payload_hex)
                        writer.write(response_mbap + dirty_pdu)
                        await writer.drain()
                        
                        # 为了确保截断效果，发完脏数据立刻断开 Socket
                        break
                    else:
                        # Baseline (正常模式): 从 DataStore 中读取数据
                        reg_addr, reg_count = struct.unpack('>HH', pdu[1:5])
                        byte_count = reg_count * 2
                        
                        # 构造负载：遍历请求的地址范围
                        payload = []
                        for i in range(reg_count):
                            _addr = reg_addr + i
                            val = self.registers.get(_addr, 0) # 默认为 0
                            payload.append(struct.pack('>H', val))
                        
                        response_pdu = struct.pack('>BB', func_code, byte_count) + b''.join(payload)
                        response_mbap = struct.pack('>HHHB', trans_id, proto_id, len(response_pdu) + 1, unit_id)
                        writer.write(response_mbap + response_pdu)
                        await writer.drain()
                else:
                    # 对于非支持的功能码，返回一个标准的 Modbus 异常码 0x01
                    response_pdu = bytes([func_code | 0x80, 0x01])
                    response_mbap = struct.pack('>HHHB', trans_id, proto_id, len(response_pdu) + 1, unit_id)
                    writer.write(response_mbap + response_pdu)
                    await writer.drain()
                    
        except asyncio.IncompleteReadError:
            logger.info(f"Client disconnected gracefully: {addr}")
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            self.active_conns -= 1
            logger.info(f"Client disconnected: {addr} (Active: {self.active_conns})")
            writer.close()
            await writer.wait_closed()
    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        logger.info(f"Malicious Simulator started on {self.host}:{self.port} in {self.mode} mode")

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="EMS Fuzzer - Malicious Modbus Simulator")
    parser.add_argument("--host", default="0.0.0.0", help="监听 IP (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5020, help="监听端口 (默认: 5020)")
    parser.add_argument('--mode', default='NORMAL', 
                        choices=['NORMAL', 'HONEYPOT', 'DROP', 'TRUNCATED', 'MISMATCH'],
                        help='Malicious behavior mode')
    parser.add_argument("--drop-after", type=int, default=2, help="针对 DROP 模式: 几包后断开")
    parser.add_argument("--config", default=None, help="配置驱动文件路径，如 pcs_profile.json")
    parser.add_argument("--delay", type=float, default=0.0, help="模拟从机响应延迟 (秒)")
    parser.add_argument("--max-conns", type=int, default=0, help="限制最大并发连接数")
    args = parser.parse_args()
    
    sim = MaliciousSimulator(host=args.host, port=args.port, mode=args.mode, drop_after_n=args.drop_after, config_file=args.config, delay=args.delay, max_conns=args.max_conns)
    await sim.start()
    
    logger.info("Press Ctrl+C to stop.")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Simulator stopped by user.")
