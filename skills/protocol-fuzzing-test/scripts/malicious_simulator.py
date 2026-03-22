import asyncio
import logging
import struct
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MaliciousSimulator")

class MaliciousSimulator:
    def __init__(self, host="127.0.0.1", port=5020, mode="HONEYPOT", drop_after_n=0, config_file=None):
        self.host = host
        self.port = port
        self.mode = mode
        self.drop_after_n = drop_after_n
        self.config = {}
        if config_file:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        self.server = None
        self.honeypot_alerts = [] # Records honeypot triggers

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        logger.info(f"Client connected: {addr}")
        req_count = 0
        try:
            while True:
                # 1. 解析 MBAP 头部 (7字节)
                mbap = await reader.readexactly(7)
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

                pdu = await reader.readexactly(length - 1)
                func_code = pdu[0]
                
                # Write Single Register (0x06)
                if func_code == 0x06:
                    reg_addr, reg_val = struct.unpack('>HH', pdu[1:5])
                    
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
                        else:
                            # 兼容无配置文件的旧版回退模式
                            if reg_addr == 6006 and reg_val > 32767:
                                alert_msg = f"HONEYPOT TRIGGERED! Address {reg_addr} got overflow value {reg_val}"
                                logger.error(alert_msg)
                                self.honeypot_alerts.append(alert_msg)
                    
                    # 伪造正常响应 (0x06 原样返回 PDU)
                    response_pdu = pdu
                    response_mbap = struct.pack('>HHHB', trans_id, proto_id, len(response_pdu) + 1, unit_id)
                    writer.write(response_mbap + response_pdu)
                    await writer.drain()
                # Read Holding Registers (0x03)
                elif func_code == 0x03:
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
                        # Baseline (正常模式): 乖乖返回合法的全零数据
                        reg_addr, reg_count = struct.unpack('>HH', pdu[1:5])
                        byte_count = reg_count * 2
                        response_pdu = struct.pack('>BB', 0x03, byte_count) + bytes(byte_count) # fill 0
                        response_mbap = struct.pack('>HHHB', trans_id, proto_id, len(response_pdu) + 1, unit_id)
                        writer.write(response_mbap + response_pdu)
                        await writer.drain()
                else:
                    # 对于非 0x06 和 0x03 的功能码，为了保持连接不被拆除，返回一个标准的 Modbus 异常码 0x01
                    response_pdu = bytes([func_code | 0x80, 0x01])
                    response_mbap = struct.pack('>HHHB', trans_id, proto_id, len(response_pdu) + 1, unit_id)
                    writer.write(response_mbap + response_pdu)
                    await writer.drain()
                    
        except asyncio.IncompleteReadError:
            logger.info(f"Client disconnected gracefully: {addr}")
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
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
    parser.add_argument("--mode", choices=["HONEYPOT", "DROP", "TRUNCATED", "MISMATCH"], default="HONEYPOT", help="恶性模式")
    parser.add_argument("--drop-after", type=int, default=2, help="针对 DROP 模式: 几包后断开")
    parser.add_argument("--config", default=None, help="配置驱动文件路径，如 pcs_profile.json")
    args = parser.parse_args()
    
    sim = MaliciousSimulator(host=args.host, port=args.port, mode=args.mode, drop_after_n=args.drop_after, config_file=args.config)
    await sim.start()
    
    logger.info("Press Ctrl+C to stop.")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Simulator stopped by user.")
